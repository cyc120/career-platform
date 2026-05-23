from functools import lru_cache
from langchain_openai import OpenAIEmbeddings
from app.config import settings

# Load HF_ENDPOINT from .env for HuggingFace mirror
import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

_fallback_mode = False


@lru_cache(maxsize=1)
def get_embeddings():
    """Returns a cached embeddings instance.

    If OPENAI_EMBEDDING_MODEL looks like a HuggingFace model (contains '/'),
    uses local BGE embeddings. Otherwise uses OpenAI-compatible API.
    """
    global _fallback_mode
    model = settings.OPENAI_EMBEDDING_MODEL
    if "/" in model:
        try:
            from langchain_community.embeddings import HuggingFaceBgeEmbeddings
            return HuggingFaceBgeEmbeddings(
                model_name=model,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )
        except Exception as e:
            print(f"[Embedding] Failed to load HuggingFace model: {e}")
            print("[Embedding] Falling back to simple hash-based embeddings")
            _fallback_mode = True
            return _SimpleEmbeddings()
    return OpenAIEmbeddings(
        model=model,
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
    )


class _SimpleEmbeddings:
    """Fallback embeddings using character-level hashing when model unavailable."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._hash_embed(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._hash_embed(text)

    @staticmethod
    def _hash_embed(text: str, dim: int = 384) -> list[float]:
        import hashlib
        h = hashlib.sha256(text.encode()).digest()
        vec = []
        for i in range(dim):
            byte_val = h[i % len(h)]
            vec.append((byte_val / 128.0) - 1.0)
        norm = sum(x * x for x in vec) ** 0.5
        return [x / norm for x in vec] if norm > 0 else vec
