from functools import lru_cache
from langchain_openai import ChatOpenAI
from app.config import settings


@lru_cache(maxsize=16)
def get_llm(temperature: float = 0.1, max_tokens: int = 4096) -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.OPENAI_MODEL,
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=60.0,
    )
