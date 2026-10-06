"""
Learnova Hybrid RAG Retriever
Combines Dense Vector Similarity with Sparse BM25 Keyword Search using Reciprocal Rank Fusion (RRF).
Formats strict citation envelopes and detects information absence / grounding insufficiency.
"""

from typing import List, Dict, Any, Optional, Tuple
import math
import re
import logging
from dataclasses import dataclass

from backend.app.rag.embeddings import EmbeddingProvider, get_embedding_provider
from backend.app.rag.vector_store import VectorStore, get_vector_store

logger = logging.getLogger(__name__)


@dataclass
class Citation:
    """Structured citation referencing source document excerpt."""
    document_id: str
    chunk_id: str
    page_number: Optional[int]
    slide_number: Optional[int]
    section_title: Optional[str]
    snippet: str
    document_title: Optional[str] = None

    def to_envelope(self) -> str:
        """Render strict citation token [[Doc:<id>, Page:<p>, Chunk:<k>]]."""
        p_str = str(self.page_number) if self.page_number is not None else (
            f"Slide {self.slide_number}" if self.slide_number is not None else "1"
        )
        return f"[[Doc:{self.document_id}, Page:{p_str}, Chunk:{self.chunk_id}]]"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "document_title": self.document_title,
            "chunk_id": self.chunk_id,
            "page_number": self.page_number,
            "slide_number": self.slide_number,
            "section_title": self.section_title,
            "snippet": self.snippet,
            "citation_token": self.to_envelope()
        }


@dataclass
class RetrievalResult:
    """Result of hybrid retrieval with relevance metadata and grounding check."""
    query: str
    document_id: Optional[str]
    chunks: List[Dict[str, Any]]
    citations: List[Citation]
    insufficient_context: bool
    confidence_score: float
    warning_message: Optional[str] = None

    def get_grounding_context(self, max_tokens: int = 2500) -> str:
        """Format retrieved chunks as structured context for LLM prompt injection."""
        if not self.chunks:
            return "NO SOURCE CONTEXT AVAILABLE IN DOCUMENT."

        context_blocks = []
        for i, c in enumerate(self.chunks, 1):
            chunk_id = c.get("id", f"chk_{i}")
            p_num = c.get("page_number")
            s_num = c.get("slide_number")
            loc = f"Page {p_num}" if p_num else (f"Slide {s_num}" if s_num else "General")
            sec = f" | Section: {c.get('section_title')}" if c.get('section_title') else ""
            envelope = f"[[Doc:{c.get('document_id')}, Page:{p_num or s_num or 1}, Chunk:{chunk_id}]]"
            content = c.get("content", "").strip()

            block = (
                f"--- SOURCE EXCERPT {i} [{loc}{sec}] {envelope} ---\n"
                f"{content}\n"
            )
            context_blocks.append(block)

        return "\n".join(context_blocks)


class BM25Index:
    """Lightweight in-memory BM25 lexical index for document chunks."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_count = 0
        self.avg_dl = 0.0
        self.doc_lengths: Dict[str, int] = {}
        self.doc_term_freqs: Dict[str, Dict[str, int]] = {}
        self.idf: Dict[str, float] = {}

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"\b\w{2,}\b", text.lower())

    def index(self, chunks: List[Dict[str, Any]]) -> None:
        self.doc_count = len(chunks)
        if self.doc_count == 0:
            return

        total_length = 0
        doc_freqs: Dict[str, int] = {}
        self.doc_lengths.clear()
        self.doc_term_freqs.clear()

        for chunk in chunks:
            cid = chunk["id"]
            tokens = self._tokenize(chunk.get("content", ""))
            length = len(tokens)
            self.doc_lengths[cid] = length
            total_length += length

            tf: Dict[str, int] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            self.doc_term_freqs[cid] = tf

            for term in tf:
                doc_freqs[term] = doc_freqs.get(term, 0) + 1

        self.avg_dl = total_length / self.doc_count if self.doc_count > 0 else 0.0

        # Calculate IDF with Robertson-Spärck Jones formula
        self.idf.clear()
        for term, freq in doc_freqs.items():
            self.idf[term] = math.log(1.0 + (self.doc_count - freq + 0.5) / (freq + 0.5))

    def score(self, query: str) -> List[Tuple[str, float]]:
        query_terms = self._tokenize(query)
        if not query_terms or self.doc_count == 0:
            return []

        scores: List[Tuple[str, float]] = []
        for cid, tf in self.doc_term_freqs.items():
            dl = self.doc_lengths.get(cid, 0)
            score = 0.0
            for term in query_terms:
                if term in tf:
                    term_tf = tf[term]
                    idf = self.idf.get(term, 0.0)
                    denom = term_tf + self.k1 * (1.0 - self.b + self.b * (dl / (self.avg_dl or 1.0)))
                    score += idf * (term_tf * (self.k1 + 1.0)) / denom
            if score > 0.0:
                scores.append((cid, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores


class Retriever:
    """
    Hybrid Retriever executing dense cosine similarity and sparse BM25 retrieval,
    fused using Reciprocal Rank Fusion (RRF, k=60).
    Ensures precise page/slide citations and identifies ungrounded / out-of-scope topics.
    """

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
        rrf_k: int = 60,
        relevance_threshold: float = 0.012
    ):
        self.vector_store = vector_store or get_vector_store()
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self.rrf_k = rrf_k
        self.relevance_threshold = relevance_threshold

    def retrieve(
        self,
        query: str,
        document_id: Optional[str] = None,
        document_title: Optional[str] = None,
        top_k: int = 4
    ) -> RetrievalResult:
        """
        Hybrid retrieval combining Dense Vector Search + BM25 Lexical Ranking.
        Returns top_k chunks with citations and insufficiency flag.
        """
        if not query or not query.strip():
            return RetrievalResult(
                query=query,
                document_id=document_id,
                chunks=[],
                citations=[],
                insufficient_context=True,
                confidence_score=0.0,
                warning_message="Query is empty."
            )

        all_doc_chunks = self.vector_store.get_document_chunks(document_id) if document_id else []
        if not all_doc_chunks and document_id:
            return RetrievalResult(
                query=query,
                document_id=document_id,
                chunks=[],
                citations=[],
                insufficient_context=True,
                confidence_score=0.0,
                warning_message=f"No indexed content found for document '{document_id}'."
            )

        # 1. Dense Semantic Search
        query_vec = self.embedding_provider.embed_text(query)
        dense_results = self.vector_store.search(
            query_vector=query_vec,
            document_id=document_id,
            top_k=max(top_k * 3, 10)
        )

        # 2. Sparse BM25 Search
        target_chunks = all_doc_chunks if all_doc_chunks else list(self.vector_store._cache.values())
        bm25 = BM25Index()
        bm25.index(target_chunks)
        bm25_ranked = bm25.score(query)

        # 3. Reciprocal Rank Fusion (RRF)
        rrf_scores: Dict[str, float] = {}

        # Rank positions from dense search
        for rank, item in enumerate(dense_results, 1):
            cid = item["id"]
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (self.rrf_k + rank))

        # Rank positions from BM25 search
        for rank, (cid, _) in enumerate(bm25_ranked, 1):
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (self.rrf_k + rank))

        if not rrf_scores:
            return RetrievalResult(
                query=query,
                document_id=document_id,
                chunks=[],
                citations=[],
                insufficient_context=True,
                confidence_score=0.0,
                warning_message="Source material contains no relevant matches for this inquiry."
            )

        # Sort by combined RRF score
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
        top_ids = sorted_ids[:top_k]

        selected_chunks: List[Dict[str, Any]] = []
        citations: List[Citation] = []

        for cid in top_ids:
            chunk_data = self.vector_store.get_chunk(cid)
            if not chunk_data:
                continue
            
            chunk_data["rrf_score"] = round(rrf_scores[cid], 5)
            selected_chunks.append(chunk_data)

            # Generate concise snippet (up to 180 chars)
            content = chunk_data.get("content", "")
            snippet = content[:180].strip() + ("..." if len(content) > 180 else "")

            citations.append(Citation(
                document_id=chunk_data.get("document_id", document_id or "unknown"),
                document_title=document_title,
                chunk_id=cid,
                page_number=chunk_data.get("page_number"),
                slide_number=chunk_data.get("slide_number"),
                section_title=chunk_data.get("section_title"),
                snippet=snippet
            ))

        # 4. Grounding Check & Confidence Calculation
        max_rrf = max(rrf_scores.values()) if rrf_scores else 0.0
        # Normalize RRF to 0.0 - 1.0 confidence approximation
        confidence = min(1.0, max_rrf / (2.0 / self.rrf_k))
        insufficient = max_rrf < self.relevance_threshold or len(selected_chunks) == 0

        warning = None
        if insufficient:
            warning = (
                "The source material appears to lack direct coverage of this query. "
                "Any answer provided will rely primarily on general principles."
            )

        return RetrievalResult(
            query=query,
            document_id=document_id,
            chunks=selected_chunks,
            citations=citations,
            insufficient_context=insufficient,
            confidence_score=round(confidence, 3),
            warning_message=warning
        )

    @staticmethod
    def verify_citations(
        llm_text: str,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Verify citation tokens in generated text against retrieved candidates.
        Matches [[Doc:<doc_id>, Page:<p>, Chunk:<chunk_id>]].
        Returns (all_valid, valid_chunk_ids, hallucinated_chunk_ids).
        """
        retrieved_ids = {c["id"] for c in retrieved_chunks}
        pattern = r"\[\[Doc:(?P<doc_id>[^,]+),\s*Page:(?P<page>[^,]+),\s*Chunk:(?P<chunk>[^\]]+)\]\]"
        matches = list(re.finditer(pattern, llm_text))

        valid_ids = []
        hallucinated_ids = []

        for m in matches:
            cid = m.group("chunk").strip()
            if cid in retrieved_ids:
                valid_ids.append(cid)
            else:
                hallucinated_ids.append(cid)

        all_valid = len(hallucinated_ids) == 0
        return all_valid, valid_ids, hallucinated_ids


def get_retriever() -> Retriever:
    """Factory helper for the standard hybrid retriever."""
    return Retriever()
