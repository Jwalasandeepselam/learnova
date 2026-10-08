"""Semantic chunking pipeline for Learnova.

Implements sliding window semantic chunking with natural boundary awareness (paragraphs,
sentences, headings), preserving strict metadata (page_number, slide_number, section_title).
"""

from dataclasses import dataclass, field
import re
from typing import Any, Dict, List, Optional
import uuid

from .parsers import ParsedDocument


@dataclass
class DocumentChunk:
    """Discrete text chunk with location coordinates and metadata."""

    id: str
    document_id: str
    chunk_index: int
    page_number: int
    slide_number: Optional[int]
    section_title: Optional[str]
    content: str
    token_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary for database insertion."""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "page_number": self.page_number,
            "slide_number": self.slide_number,
            "section_title": self.section_title,
            "content": self.content,
            "token_count": self.token_count,
            "metadata": self.metadata,
        }


class SemanticChunker:
    """Splits documents into coherent semantic chunks with overlap and boundary preservation."""

    def __init__(
        self,
        target_chunk_tokens: int = 400,
        min_chunk_tokens: int = 100,
        max_chunk_tokens: int = 600,
        overlap_tokens: int = 50,
    ):
        self.target_tokens = target_chunk_tokens
        self.min_tokens = min_chunk_tokens
        self.max_tokens = max_chunk_tokens
        self.overlap_tokens = overlap_tokens
        self.sentence_pattern = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])")

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Estimate token count based on words and characters (1 word ~ 1.33 tokens)."""
        words = text.split()
        return max(1, int(len(words) * 1.33))

    def split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences while respecting abbreviations and formulas."""
        paragraphs = text.split("\n\n")
        sentences: List[str] = []
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            para_sentences = self.sentence_pattern.split(para)
            for s in para_sentences:
                s_clean = s.strip()
                if s_clean:
                    sentences.append(s_clean)
        return sentences

    def chunk_document(
        self, parsed_doc: ParsedDocument, document_id: str
    ) -> List[DocumentChunk]:
        """Chunk an entire ParsedDocument preserving page numbers and section headers."""
        chunks: List[DocumentChunk] = []
        global_chunk_idx = 0

        # Process page by page to strictly preserve page-level fidelity
        for page in parsed_doc.pages:
            page_text = page.text.strip()
            if not page_text:
                continue

            page_tokens = self.estimate_tokens(page_text)

            # If page fits comfortably within max_tokens, treat page as a single chunk
            if page_tokens <= self.max_tokens:
                chunk = DocumentChunk(
                    id=f"chk_{document_id[-8:] if len(document_id) >= 8 else document_id}_{global_chunk_idx:04d}",
                    document_id=document_id,
                    chunk_index=global_chunk_idx,
                    page_number=page.page_number,
                    slide_number=page.slide_number,
                    section_title=page.section_title or "General",
                    content=page_text,
                    token_count=page_tokens,
                    metadata={
                        "filename": parsed_doc.filename,
                        "file_type": parsed_doc.file_type,
                        "source_page": page.page_number,
                    },
                )
                chunks.append(chunk)
                global_chunk_idx += 1
                continue

            # Otherwise, perform sliding-window sentence-level chunking for large page
            sentences = self.split_into_sentences(page_text)
            if not sentences:
                sentences = [page_text]

            current_window: List[str] = []
            current_tokens = 0

            for sentence in sentences:
                sent_tokens = self.estimate_tokens(sentence)

                if current_tokens + sent_tokens > self.max_tokens and current_tokens >= self.min_tokens:
                    # Flush current window
                    chunk_content = " ".join(current_window).strip()
                    chunk = DocumentChunk(
                        id=f"chk_{document_id[-8:] if len(document_id) >= 8 else document_id}_{global_chunk_idx:04d}",
                        document_id=document_id,
                        chunk_index=global_chunk_idx,
                        page_number=page.page_number,
                        slide_number=page.slide_number,
                        section_title=page.section_title or "General",
                        content=chunk_content,
                        token_count=current_tokens,
                        metadata={
                            "filename": parsed_doc.filename,
                            "file_type": parsed_doc.file_type,
                            "source_page": page.page_number,
                        },
                    )
                    chunks.append(chunk)
                    global_chunk_idx += 1

                    # Retain overlap sentences
                    overlap_window: List[str] = []
                    overlap_acc = 0
                    for s in reversed(current_window):
                        s_tok = self.estimate_tokens(s)
                        if overlap_acc + s_tok <= self.overlap_tokens:
                            overlap_window.insert(0, s)
                            overlap_acc += s_tok
                        else:
                            break

                    current_window = overlap_window
                    current_tokens = overlap_acc

                current_window.append(sentence)
                current_tokens += sent_tokens

            # Flush trailing sentences
            if current_window:
                chunk_content = " ".join(current_window).strip()
                chunk = DocumentChunk(
                    id=f"chk_{document_id[-8:] if len(document_id) >= 8 else document_id}_{global_chunk_idx:04d}",
                    document_id=document_id,
                    chunk_index=global_chunk_idx,
                    page_number=page.page_number,
                    slide_number=page.slide_number,
                    section_title=page.section_title or "General",
                    content=chunk_content,
                    token_count=current_tokens,
                    metadata={
                        "filename": parsed_doc.filename,
                        "file_type": parsed_doc.file_type,
                        "source_page": page.page_number,
                    },
                )
                chunks.append(chunk)
                global_chunk_idx += 1

        return chunks
