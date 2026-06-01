from __future__ import annotations

from functools import lru_cache

from sentence_transformers import SentenceTransformer

MODEL_DIMENSIONS = {
    "all-mpnet-base-v2": 768,
    "all-MiniLM-L6-v2": 384,
}

DEFAULT_MODEL = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embedding_model(model_name: str = DEFAULT_MODEL) -> SentenceTransformer:
    return SentenceTransformer(model_name)


def embedding_dimension(model_name: str = DEFAULT_MODEL) -> int:
    model = get_embedding_model(model_name)
    return MODEL_DIMENSIONS.get(
        model_name,
        model.get_embedding_dimension() if hasattr(model, "get_embedding_dimension") else model.get_sentence_embedding_dimension(),
    )


def embed_texts(
    texts: list[str],
    *,
    model_name: str = DEFAULT_MODEL,
    batch_size: int = 16,
) -> list[list[float]]:
    if not texts:
        return []
    model = get_embedding_model(model_name)
    vectors = model.encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=len(texts) > 20,
    )
    return [vector.tolist() for vector in vectors]
