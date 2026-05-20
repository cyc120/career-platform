from functools import lru_cache
from langchain_openai import OpenAIEmbeddings
from app.config import settings


@lru_cache(maxsize=1)
def get_embeddings():
    """Returns a cached embeddings instance.

    If OPENAI_EMBEDDING_MODEL looks like a HuggingFace model (contains '/'),
    uses local BGE embeddings. Otherwise uses OpenAI-compatible API.
    """
    model = settings.OPENAI_EMBEDDING_MODEL
    if "/" in model:
        from langchain_community.embeddings import HuggingFaceBgeEmbeddings
        return HuggingFaceBgeEmbeddings(
            model_name=model,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    return OpenAIEmbeddings(
        model=model,
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
    )
