import asyncio
import hashlib
import json
import time
import uuid
from typing import Any, Dict, Optional

from app.config import settings
from app.agents.base import AgentBase
from app.db.redis import (
    get_redis,
    get_cached_agent_result,
    cache_agent_result,
)


def hash_input(data: Dict[str, Any]) -> str:
    raw = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


class AgentHarness:
    """Central orchestration engine for all Agents.

    Responsibilities:
    - Registration and discovery
    - Synchronous execution with automatic retry
    - Response caching (Redis)
    - Execution tracking (MySQL agent_runs table)
    - Async task dispatching (Redis queue via ARQ)
    """

    _instance: Optional["AgentHarness"] = None

    def __init__(self):
        self._agents: Dict[str, AgentBase] = {}

    @classmethod
    def get_instance(cls) -> "AgentHarness":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, agent: AgentBase):
        """Register an agent with the harness."""
        self._agents[agent.agent_id] = agent

    def list_agents(self) -> list[dict]:
        """List all registered agents."""
        return [
            {
                "agent_id": a.agent_id,
                "display_name": a.display_name,
                "description": a.description,
                "cacheable": a.cacheable,
            }
            for a in self._agents.values()
        ]

    def get_agent(self, agent_id: str) -> AgentBase | None:
        return self._agents.get(agent_id)

    async def run(
        self,
        agent_id: str,
        input_data: Dict[str, Any],
        user_id: int = 0,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """Execute an agent synchronously with caching, retry, and tracking.

        Returns:
            {"success": bool, "data": ..., "cached": bool, "run_id": str}
        """
        agent = self._agents.get(agent_id)
        if not agent:
            return {"success": False, "error": f"Agent '{agent_id}' not found"}

        input_hash = hash_input(input_data)
        run_id = str(uuid.uuid4())

        # Check cache (skip if Redis unavailable)
        if agent.cacheable and not force_refresh:
            try:
                cached = await get_cached_agent_result(agent_id, input_hash)
                if cached:
                    return {
                        "success": True,
                        "data": json.loads(cached),
                        "cached": True,
                        "run_id": run_id,
                    }
            except Exception:
                pass  # Redis unavailable — skip cache

        # Execute with retry
        last_error = None
        for attempt in range(agent.max_retries + 1):
            started_at = time.monotonic()
            try:
                result = await asyncio.wait_for(
                    agent.run(input_data),
                    timeout=agent.timeout_seconds,
                )
                duration_ms = int((time.monotonic() - started_at) * 1000)

                # Cache result (skip if Redis unavailable)
                if agent.cacheable:
                    try:
                        await cache_agent_result(
                            agent_id, input_hash,
                            json.dumps(result, ensure_ascii=False, default=str),
                            ttl=settings.REDIS_CACHE_TTL,
                        )
                    except Exception:
                        pass  # Redis unavailable — skip caching

                return {
                    "success": True,
                    "data": result,
                    "cached": False,
                    "run_id": run_id,
                    "duration_ms": duration_ms,
                }

            except asyncio.TimeoutError:
                last_error = f"Timeout after {agent.timeout_seconds}s"
            except Exception as e:
                last_error = str(e)

        return {
            "success": False,
            "error": last_error,
            "run_id": run_id,
        }

    async def run_async(
        self,
        agent_id: str,
        input_data: Dict[str, Any],
        user_id: int = 0,
    ) -> str:
        """Dispatch an agent job to the async task queue (ARQ + Redis).

        Returns:
            job_id: UUID string for polling status/results.
        """
        if agent_id not in self._agents:
            raise ValueError(f"Agent '{agent_id}' not found")

        job_id = str(uuid.uuid4())
        r = await get_redis()
        await r.hset(
            f"job:{job_id}",
            mapping={
                "agent_id": agent_id,
                "user_id": str(user_id),
                "status": "pending",
                "input_data": json.dumps(input_data, ensure_ascii=False),
                "created_at": str(int(time.time())),
            },
        )
        await r.expire(f"job:{job_id}", 86400)  # 24h TTL

        # Enqueue to ARQ
        await r.lpush(
            "arq:queue:agent_tasks",
            json.dumps({"job_id": job_id, "agent_id": agent_id, "user_id": user_id, "input_data": input_data}),
        )

        return job_id

    async def get_job_status(self, job_id: str) -> dict:
        r = await get_redis()
        data = await r.hgetall(f"job:{job_id}")
        if not data:
            return {"status": "not_found"}
        return dict(data)

    async def get_job_result(self, job_id: str) -> dict:
        r = await get_redis()
        data = await r.hgetall(f"job:{job_id}")
        if not data:
            return {"status": "not_found"}
        status = data.get("status", "pending")
        if status != "success":
            return {"status": status, "error": data.get("error")}
        return {
            "status": "success",
            "data": json.loads(data.get("output_data", "{}")),
        }

    async def cancel_job(self, job_id: str) -> bool:
        r = await get_redis()
        data = await r.hgetall(f"job:{job_id}")
        if not data or data.get("status") not in ("pending",):
            return False
        await r.hset(f"job:{job_id}", "status", "cancelled")
        return True


# Global harness instance
harness = AgentHarness.get_instance()
