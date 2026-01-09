"""Shared embedding model instance to avoid duplicate loading."""
import logging
from sentence_transformers import SentenceTransformer
import config

logger = logging.getLogger(__name__)

# Global instance - will be loaded on first access
_embedding_model = None


def get_embedding_model():
    """Get or create the shared embedding model instance (lazy loading)."""
    global _embedding_model
    if _embedding_model is None:
        logger.info("Loading shared embedding model...")
        _embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
        logger.info("Shared embedding model loaded")
    return _embedding_model

