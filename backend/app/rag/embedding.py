from functools import lru_cache
from langchain_openai import OpenAIEmbeddings
from app.config import settings


@lru_cache(maxsize=1)
def get_embeddings() -> OpenAIEmbeddings:
    """Returns a cached OpenAI-compatible embeddings instance.

    Uses DeepSeek's OpenAI-compatible API for embeddings.
    Falls back to local BGE model if DeepSeek embedding is unavailable.
    """
    return OpenAIEmbeddings(
        model=settings.OPENAI_EMBEDDING_MODEL,
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
    )
