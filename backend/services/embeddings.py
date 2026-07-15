"""Lazy embedding model loading."""

from functools import lru_cache

from sentence_transformers import SentenceTransformer


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """Return the shared local model used for code-search embeddings."""
    return SentenceTransformer("all-MiniLM-L6-v2")


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    vectors = get_embedding_model().encode(texts, normalize_embeddings=True)
    return vectors.tolist()
