"""InLegal-SBERT embedding generation.

The model is loaded once per process and reused - loading takes several
seconds, so per-call loading would dominate runtime.
"""

from functools import lru_cache

from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"
DIMENSIONS = 768
BATCH_SIZE = 32


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


def embed_one(text: str) -> list[float]:
    return get_model().encode(text, normalize_embeddings=True).tolist()


def embed_many(texts: list[str], batch_size: int = BATCH_SIZE) -> list[list[float]]:
    vectors = get_model().encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return [v.tolist() for v in vectors]
