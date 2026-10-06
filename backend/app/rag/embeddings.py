"""
Learnova Embeddings Module
Provides base embedding interfaces and implementations for Gemini and Local vectors.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
import math
import re
import hashlib
import logging

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingProvider(ABC):
    """Abstract base class for text embedding providers."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Vector dimension produced by this provider."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name or identifier of the embedding model."""
        pass

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Compute dense vector representation for a single text."""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Compute dense vector representations for multiple texts."""
        pass


class LocalEmbeddingProvider(EmbeddingProvider):
    """
    Robust local embedding provider.
    Tries sentence-transformers if cached locally; otherwise defaults to a
    deterministic normalized semantic n-gram / subword hash vectorizer.
    Guarantees zero-network execution and 100% offline availability.
    """

    def __init__(self, dimension: int = 384, model_name: str = "local-deterministic-hash-384"):
        self._dim = dimension
        self._model_name = model_name
        self._st_model = None
        self._try_init_sentence_transformer()

    def _try_init_sentence_transformer(self) -> None:
        try:
            import os
            # Only use sentence-transformers if explicitly enabled and cached locally
            if os.environ.get("USE_LOCAL_SENTENCE_TRANSFORMER", "").lower() in ("1", "true"):
                from sentence_transformers import SentenceTransformer
                model_target = settings.LOCAL_EMBEDDING_MODEL or "all-MiniLM-L6-v2"
                self._st_model = SentenceTransformer(model_target, local_files_only=True)
                self._dim = self._st_model.get_sentence_embedding_dimension()
                self._model_name = f"st-{model_target}"
                logger.info("Loaded cached SentenceTransformer: %s (dim=%d)", self._model_name, self._dim)
            else:
                self._st_model = None
        except Exception as e:
            logger.info("SentenceTransformer not cached locally (%s), using deterministic hash vectorizer", e)
            self._st_model = None

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def model_name(self) -> str:
        return self._model_name

    def _hash_vectorize(self, text: str) -> List[float]:
        """
        Deterministic normalized semantic n-gram hash vectorizer.
        Extracts words, stems, and character 3-5 grams to capture semantic affinities.
        Normalizes the output vector to unit Euclidean length (L2 norm = 1.0).
        """
        if not text or not text.strip():
            return [0.0] * self._dim

        vector = [0.0] * self._dim
        normalized = text.lower().strip()
        tokens = re.findall(r"\b\w+\b", normalized)

        # Word-level features
        for token in tokens:
            h = int(hashlib.md5(f"w:{token}".encode("utf-8")).hexdigest(), 16)
            idx = h % self._dim
            sign = 1.0 if ((h >> 8) & 1) == 0 else -1.0
            vector[idx] += sign * 1.5

            # Subword prefix/suffix features
            if len(token) > 4:
                prefix = token[:4]
                hp = int(hashlib.md5(f"sub:{prefix}".encode("utf-8")).hexdigest(), 16)
                vector[hp % self._dim] += (1.0 if ((hp >> 8) & 1) == 0 else -1.0) * 0.8

        # Character n-gram features (captures morphology and typo tolerance)
        clean_text = " " + re.sub(r"\s+", " ", normalized) + " "
        ngram_size = 3
        if len(clean_text) >= ngram_size:
            for i in range(len(clean_text) - ngram_size + 1):
                ngram = clean_text[i:i + ngram_size]
                hn = int(hashlib.sha256(f"ng:{ngram}".encode("utf-8")).hexdigest(), 16)
                idx = hn % self._dim
                sign = 1.0 if ((hn >> 4) & 1) == 0 else -1.0
                vector[idx] += sign * 0.5

        # L2 Normalization
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 1e-12:
            return [v / norm for v in vector]
        return [0.0] * self._dim

    def embed_text(self, text: str) -> List[float]:
        if self._st_model is not None:
            try:
                emb = self._st_model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
                return emb.tolist()
            except Exception as e:
                logger.warning("SentenceTransformer encode failed, using hash vectorizer: %s", e)
        return self._hash_vectorize(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if self._st_model is not None:
            try:
                embs = self._st_model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
                return embs.tolist()
            except Exception as e:
                logger.warning("SentenceTransformer batch encode failed, using hash vectorizer: %s", e)
        return [self._hash_vectorize(t) for t in texts]


class GeminiEmbeddingProvider(EmbeddingProvider):
    """
    Google Gemini Embedding Provider using google.genai SDK.
    Uses text-embedding-004 or gemini-embedding-001 with automatic dimension detection.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "text-embedding-004"):
        self._api_key = api_key or settings.GEMINI_API_KEY
        self._model = model
        self._dim = 768
        self._client = None
        self._fallback_provider = LocalEmbeddingProvider(dimension=self._dim)

        if self._api_key:
            if not self._api_key.startswith("AIza") and not self._api_key.startswith("gemini-"):
                self._client = None
            else:
                try:
                    from google import genai
                    self._client = genai.Client(api_key=self._api_key)
                except Exception as e:
                    logger.warning("Failed to initialize Gemini Client: %s", e)
                    self._client = None

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def model_name(self) -> str:
        return self._model

    def embed_text(self, text: str) -> List[float]:
        if not self._client or not text.strip():
            return self._fallback_provider.embed_text(text)

        try:
            # Try official google.genai Client models.embed_content
            res = self._client.models.embed_content(
                model=self._model,
                contents=text
            )
            if hasattr(res, "embedding") and hasattr(res.embedding, "values"):
                vec = list(res.embedding.values)
                self._dim = len(vec)
                return vec
            elif hasattr(res, "embeddings") and len(res.embeddings) > 0:
                vec = list(res.embeddings[0].values)
                self._dim = len(vec)
                return vec
        except Exception as e:
            logger.warning("Gemini embed_text call failed, falling back to local: %s", e)

        return self._fallback_provider.embed_text(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not self._client or not texts:
            return self._fallback_provider.embed_batch(texts)

        try:
            # Batch embedding
            res = self._client.models.embed_content(
                model=self._model,
                contents=texts
            )
            if hasattr(res, "embeddings") and res.embeddings:
                return [list(item.values) for item in res.embeddings]
        except Exception as e:
            logger.warning("Gemini embed_batch failed, attempting individual or fallback: %s", e)

        # Fallback to per-item or local
        results: List[List[float]] = []
        for t in texts:
            results.append(self.embed_text(t))
        return results


def get_embedding_provider(provider_type: Optional[str] = None) -> EmbeddingProvider:
    """
    Factory function returning the configured embedding provider.
    Gracefully falls back to LocalEmbeddingProvider if Gemini is unavailable or not configured.
    """
    chosen = provider_type or settings.AI_EMBEDDING_PROVIDER or "local"
    chosen = chosen.lower()

    if chosen == "gemini" and settings.GEMINI_API_KEY:
        try:
            provider = GeminiEmbeddingProvider(api_key=settings.GEMINI_API_KEY)
            if provider._client:
                return provider
        except Exception as e:
            logger.warning("Unable to initialize GeminiEmbeddingProvider: %s", e)

    # Default to LocalEmbeddingProvider for maximum resilience and speed
    return LocalEmbeddingProvider(dimension=384)
