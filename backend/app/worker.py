"""ARQ Worker for async Agent execution via Redis queue."""

import json
from arq.connections import RedisSettings
from app.config import settings


async def run_agent_job(ctx, job_id: str, agent_id: str, user_id: int, input_data: dict):
    """ARQ task: execute an agent job asynchronously."""
    from app.agents.harness import harness

    result = await harness.run(agent_id, input_data, user_id=user_id, force_refresh=True)

    r = ctx["redis"]
    await r.hset(
        f"job:{job_id}",
        mapping={
            "status": "success" if result["success"] else "failed",
            "output_data": json.dumps(result, ensure_ascii=False, default=str),
        },
    )


class WorkerSettings:
    functions = [run_agent_job]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    queue_name = "agent_tasks"
    max_jobs = 10
    poll_delay = 2
