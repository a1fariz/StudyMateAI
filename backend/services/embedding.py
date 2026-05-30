"""
Embedding service: generate vector embeddings using sentence-transformers.

Uses a singleton pattern so the model is loaded once and reused.
Model: all-MiniLM-L6-v2 (~80MB, 384-dimensional embeddings).
"""

import logging
from sentence_transformers import SentenceTransformer

from backend.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class EmbeddingService:
    """Singleton wrapper around the sentence-transformers model."""

    _model: SentenceTransformer | None = None

    @classmethod
    def get_model(cls) -> SentenceTransformer:
        """
        Lazy-load the embedding model.
        First call downloads the model (~80MB) if not cached.
        """
        if cls._model is None:
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
            cls._model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info(
                f"✅ Embedding model loaded — "
                f"dimension: {cls._model.get_sentence_embedding_dimension()}"
            )
        return cls._model

    @classmethod
    def embed_texts(cls, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for a batch of texts.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors (each is a list of floats).
        """
        model = cls.get_model()
        embeddings = model.encode(
            texts,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        logger.info(f"Generated {len(texts)} embeddings")
        return embeddings.tolist()

    @classmethod
    def embed_query(cls, query: str) -> list[float]:
        """
        Generate a single embedding for a search query.

        Args:
            query: The search query string.

        Returns:
            Embedding vector as a list of floats.
        """
        model = cls.get_model()
        embedding = model.encode(query, convert_to_numpy=True)
        return embedding.tolist()
