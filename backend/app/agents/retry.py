"""Common retry utility for LLM calls with exponential backoff."""

import asyncio
from typing import Any

from langchain_core.messages import BaseMessage

from app.agents.llm_factory import get_llm


async def llm_call_with_retry(
    messages: list[BaseMessage],
    temperature: float = 0.1,
    max_tokens: int = 1000,
    max_retries: int = 2,
    timeout: int = 30,
) -> str:
    """Call LLM with retry, exponential backoff, and timeout protection.

    Args:
        messages: List of LangChain message objects.
        temperature: LLM temperature.
        max_tokens: Max output tokens.
        max_retries: Number of retries (total attempts = max_retries + 1).
        timeout: Per-attempt timeout in seconds.

    Returns:
        LLM response content string.

    Raises:
        Exception: After all retries exhausted.
    """
    llm = get_llm(temperature=temperature, max_tokens=max_tokens)
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            response = await asyncio.wait_for(
                llm.ainvoke(messages),
                timeout=timeout,
            )
            return response.content
        except asyncio.TimeoutError:
            last_error = f"LLM timeout ({timeout}s)"
        except Exception as e:
            last_error = str(e)

        if attempt < max_retries:
            await asyncio.sleep(min(2 ** attempt, 8))

    raise Exception(f"LLM call failed after {max_retries + 1} attempts: {last_error}")


def parse_json_response(content: str) -> dict:
    """Strip markdown fences and parse JSON from LLM response."""
    import json
    c = content.strip()
    for marker in ("```json", "```"):
        if marker in c:
            c = c.split(marker)[1].split("```")[0]
            break
    return json.loads(c)
