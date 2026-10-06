"""
Learnova Persistent Vector Store
Provides persistent storage, cosine similarity search, and metadata management for document chunks.
Uses SQLite for zero-dependency local persistence across server restarts.
"""

from typing import List, Dict, Any, Optional
import sqlite3
import json
import math
import uuid
from pathlib import Path
import logging

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Lightweight, persistent vector store using SQLite and in-memory vector cache.
    Stores chunk contents, embeddings, and layout metadata (page_number, slide_number, section_title).
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            Path(settings.VECTOR_STORE_DIR).mkdir(parents=True, exist_ok=True)
            self.db_path = str(Path(settings.VECTOR_STORE_DIR) / "vectors.db")
        else:
            self.db_path = db_path
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self._init_db()
        # In-memory index cache: chunk_id -> dict with embedding and metadata
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._load_cache()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initialize SQLite tables for vector and chunk persistence."""
        conn = self._get_connection()
        try:
            with conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS document_chunks (
                        id TEXT PRIMARY KEY,
                        document_id TEXT NOT NULL,
                        chunk_index INTEGER NOT NULL,
                        page_number INTEGER,
                        slide_number INTEGER,
                        section_title TEXT,
                        content TEXT NOT NULL,
                        token_count INTEGER,
                        embedding_json TEXT NOT NULL,
                        metadata_json TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_doc ON document_chunks(document_id);")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_page ON document_chunks(page_number);")
        finally:
            conn.close()

    def _load_cache(self) -> None:
        """Load all chunks into memory cache for fast vector operations."""
        self._cache.clear()
        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                SELECT id, document_id, chunk_index, page_number, slide_number, 
                       section_title, content, token_count, embedding_json, metadata_json
                FROM document_chunks
            """)
            for row in cursor.fetchall():
                chunk_id = row["id"]
                try:
                    emb = json.loads(row["embedding_json"])
                except Exception:
                    emb = []
                
                try:
                    meta = json.loads(row["metadata_json"]) if row["metadata_json"] else {}
                except Exception:
                    meta = {}

                self._cache[chunk_id] = {
                    "id": chunk_id,
                    "document_id": row["document_id"],
                    "chunk_index": row["chunk_index"],
                    "page_number": row["page_number"],
                    "slide_number": row["slide_number"],
                    "section_title": row["section_title"],
                    "content": row["content"],
                    "token_count": row["token_count"],
                    "embedding": emb,
                    "metadata": meta
                }
            logger.info("Loaded %d chunks into VectorStore cache from %s", len(self._cache), self.db_path)
        except Exception as e:
            logger.error("Error loading VectorStore cache: %s", e)
        finally:
            conn.close()

    def add_chunks(
        self,
        document_id: str,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]]
    ) -> int:
        """
        Add chunks and their embeddings for a document.
        chunks: List of dicts with keys:
            - 'content' (required)
            - 'chunk_index' (optional, auto-assigned if missing)
            - 'page_number' (optional)
            - 'slide_number' (optional)
            - 'section_title' (optional)
            - 'token_count' (optional)
            - 'metadata' (optional dict)
            - 'id' (optional, generated if missing)
        """
        if len(chunks) != len(embeddings):
            raise ValueError(f"Mismatch: {len(chunks)} chunks and {len(embeddings)} embeddings provided.")

        rows_to_insert = []
        new_cached_items = {}

        for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            chunk_id = chunk.get("id") or f"chk_{uuid.uuid4().hex[:12]}"
            chunk_index = chunk.get("chunk_index", idx)
            page_number = chunk.get("page_number")
            slide_number = chunk.get("slide_number")
            section_title = chunk.get("section_title")
            content = chunk.get("content", "")
            token_count = chunk.get("token_count", len(content.split()))
            metadata = chunk.get("metadata", {})

            rows_to_insert.append((
                chunk_id,
                document_id,
                chunk_index,
                page_number,
                slide_number,
                section_title,
                content,
                token_count,
                json.dumps(emb),
                json.dumps(metadata)
            ))

            new_cached_items[chunk_id] = {
                "id": chunk_id,
                "document_id": document_id,
                "chunk_index": chunk_index,
                "page_number": page_number,
                "slide_number": slide_number,
                "section_title": section_title,
                "content": content,
                "token_count": token_count,
                "embedding": emb,
                "metadata": metadata
            }

        conn = self._get_connection()
        try:
            with conn:
                conn.executemany("""
                    INSERT OR REPLACE INTO document_chunks (
                        id, document_id, chunk_index, page_number, slide_number,
                        section_title, content, token_count, embedding_json, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, rows_to_insert)
        finally:
            conn.close()

        self._cache.update(new_cached_items)
        return len(rows_to_insert)

    def _cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        """Compute cosine similarity between two float vectors."""
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0
        
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))

        if norm_a <= 1e-12 or norm_b <= 1e-12:
            return 0.0

        return dot / (norm_a * norm_b)

    def search(
        self,
        query_vector: List[float],
        document_id: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Perform cosine similarity search across chunks.
        Optionally filter by document_id.
        Returns top_k items with metadata and 'score'.
        """
        if not query_vector or not self._cache:
            return []

        candidates = []
        for chunk_id, item in self._cache.items():
            if document_id and item["document_id"] != document_id:
                continue

            sim = self._cosine_similarity(query_vector, item["embedding"])
            candidates.append({
                "id": item["id"],
                "document_id": item["document_id"],
                "chunk_index": item["chunk_index"],
                "page_number": item["page_number"],
                "slide_number": item["slide_number"],
                "section_title": item["section_title"],
                "content": item["content"],
                "token_count": item["token_count"],
                "metadata": item["metadata"],
                "score": round(sim, 4)
            })

        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:top_k]

    def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """Retrieve all chunks belonging to a document, ordered by chunk_index."""
        matching = [
            {
                "id": item["id"],
                "document_id": item["document_id"],
                "chunk_index": item["chunk_index"],
                "page_number": item["page_number"],
                "slide_number": item["slide_number"],
                "section_title": item["section_title"],
                "content": item["content"],
                "token_count": item["token_count"],
                "metadata": item["metadata"]
            }
            for item in self._cache.values()
            if item["document_id"] == document_id
        ]
        matching.sort(key=lambda x: x["chunk_index"])
        return matching

    def get_chunk(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """Get chunk details by its ID."""
        item = self._cache.get(chunk_id)
        if not item:
            return None
        return {
            "id": item["id"],
            "document_id": item["document_id"],
            "chunk_index": item["chunk_index"],
            "page_number": item["page_number"],
            "slide_number": item["slide_number"],
            "section_title": item["section_title"],
            "content": item["content"],
            "token_count": item["token_count"],
            "metadata": item["metadata"]
        }

    def delete_document(self, document_id: str) -> bool:
        """Remove all chunks associated with a document_id."""
        conn = self._get_connection()
        try:
            with conn:
                conn.execute("DELETE FROM document_chunks WHERE document_id = ?;", (document_id,))
        finally:
            conn.close()

        # Remove from cache
        to_del = [cid for cid, c in self._cache.items() if c["document_id"] == document_id]
        for cid in to_del:
            self._cache.pop(cid, None)

        return True

    def close(self) -> None:
        """Explicitly clear cache and release resources."""
        self._cache.clear()

    def count(self, document_id: Optional[str] = None) -> int:
        """Count indexed chunks."""
        if document_id:
            return sum(1 for c in self._cache.values() if c["document_id"] == document_id)
        return len(self._cache)


_global_vector_store: Optional[VectorStore] = None

def get_vector_store() -> VectorStore:
    """Singleton getter for the persistent vector store."""
    global _global_vector_store
    if _global_vector_store is None:
        _global_vector_store = VectorStore()
    return _global_vector_store
