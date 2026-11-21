from functools import lru_cache
from app.core.config import settings


@lru_cache(maxsize=1)
def model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.embedding_model)


@lru_cache(maxsize=512)
def embed_query(text: str) -> list[float]:
    return model().encode(text, normalize_embeddings=True).tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    return model().encode(texts, batch_size=32, normalize_embeddings=True).tolist()
