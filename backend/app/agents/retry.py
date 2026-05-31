"""Common retry utility for LLM calls with exponential backoff.

Also provides SubModuleTracer for wrapping sub-module calls with
timeout protection, structured logging, and error context.
"""

import asyncio
import logging
import time
from typing import Any, Callable, Optional

from langchain_core.messages import BaseMessage

from app.agents.llm_factory import get_llm

logger = logging.getLogger(__name__)


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


class SubModuleTracer:
    """Wraps sub-module calls with timeout, tracing, and error context.

    Usage:
        tracer = SubModuleTracer("job_matcher", "job_profiler")
        result = await tracer.run(extract_job_requirements, job, timeout=60)
    """

    def __init__(self, parent_agent: str, module_name: str):
        self.parent_agent = parent_agent
        self.module_name = module_name

    async def run(
        self,
        func: Callable,
        *args,
        timeout: int = 60,
        default: Any = None,
        **kwargs,
    ) -> Any:
        """Execute a sub-module function with timeout and tracing.

        Args:
            func: Async function to call.
            *args, **kwargs: Forwarded to func.
            timeout: Overall timeout in seconds for this call.
            default: Value to return on failure (None = raise).

        Returns:
            Function result, or default on failure.
        """
        started = time.monotonic()
        try:
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=timeout,
            )
            elapsed = int((time.monotonic() - started) * 1000)
            logger.info(
                f"[{self.parent_agent}:{self.module_name}] "
                f"completed in {elapsed}ms"
            )
            return result
        except asyncio.TimeoutError:
            elapsed = int((time.monotonic() - started) * 1000)
            logger.warning(
                f"[{self.parent_agent}:{self.module_name}] "
                f"TIMEOUT after {elapsed}ms (limit={timeout}s)"
            )
            if default is not None:
                return default
            raise
        except Exception as e:
            elapsed = int((time.monotonic() - started) * 1000)
            logger.warning(
                f"[{self.parent_agent}:{self.module_name}] "
                f"FAILED after {elapsed}ms: {e}"
            )
            if default is not None:
                return default
            raise
