from functools import lru_cache
from pathlib import Path
from app.core.config import settings


@lru_cache(maxsize=1)
def model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.embedding_model)


@lru_cache(maxsize=1)
def compact_model():
    from app.services.onnx_embeddings import MiniLM

    assert settings.mini_lm_assets
    return MiniLM(Path(settings.mini_lm_assets))


@lru_cache(maxsize=512)
def embed_query(text: str) -> list[float]:
    if settings.mini_lm_assets:
        return compact_model().encode([text])[0]
    return model().encode(text, normalize_embeddings=True).tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    if settings.mini_lm_assets:
        return [
            vector for i in range(0, len(texts), 4) for vector in compact_model().encode(texts[i : i + 4])
        ]
    return model().encode(texts, batch_size=32, normalize_embeddings=True).tolist()
