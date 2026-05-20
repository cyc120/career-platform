"""Database tools for learning_plan agent."""

import json
from datetime import date
from sqlalchemy import text
from app.db.mysql import AsyncSessionLocal


async def get_target_job(user_id: int) -> dict | None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text(
                "SELECT job_name, match_score FROM matching_report "
                "WHERE user_id = :uid ORDER BY match_score DESC LIMIT 1"
            ),
            {"uid": user_id},
        )
        row = result.fetchone()
        return dict(row._mapping) if row else None


async def save_learning_plan(user_id: int, target_job: str,
                               plan_type: str, phases: list) -> bool:
    async with AsyncSessionLocal() as db:
        await db.execute(
            text(
                "INSERT INTO learning_plans (user_id, target_job, plan_type, phases, updated_at) "
                "VALUES (:uid, :tj, :pt, :ph, NOW()) "
                "ON DUPLICATE KEY UPDATE target_job = :tj2, plan_type = :pt2, "
                "phases = :ph2, updated_at = NOW()"
            ),
            {
                "uid": user_id, "tj": target_job, "pt": plan_type,
                "ph": json.dumps(phases, ensure_ascii=False),
                "tj2": target_job, "pt2": plan_type,
                "ph2": json.dumps(phases, ensure_ascii=False),
            },
        )
        await db.commit()
    return True


async def get_learning_plan(user_id: int) -> dict | None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("SELECT * FROM learning_plans WHERE user_id = :uid"),
            {"uid": user_id},
        )
        row = result.fetchone()
        return dict(row._mapping) if row else None


async def save_daily_tasks(user_id: int, tasks: list[dict]) -> int:
    count = 0
    async with AsyncSessionLocal() as db:
        for task in tasks:
            await db.execute(
                text(
                    "INSERT INTO daily_tasks (user_id, task_date, title, description, "
                    "duration, resources, status) VALUES (:uid, :td, :t, :d, :dur, :res, 'pending')"
                ),
                {
                    "uid": user_id,
                    "td": date.today(),
                    "t": task.get("title", ""),
                    "d": task.get("description", ""),
                    "dur": task.get("duration", ""),
                    "res": json.dumps(task.get("resources", []), ensure_ascii=False),
                },
            )
            count += 1
        await db.commit()
    return count


async def get_daily_tasks(user_id: int) -> list[dict]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text(
                "SELECT id, task_date, title, description, duration, status "
                "FROM daily_tasks WHERE user_id = :uid ORDER BY task_date, id"
            ),
            {"uid": user_id},
        )
        return [dict(r._mapping) for r in result.fetchall()]


async def update_task_status(task_id: int, status: str) -> bool:
    async with AsyncSessionLocal() as db:
        await db.execute(
            text("UPDATE daily_tasks SET status = :s WHERE id = :tid"),
            {"s": status, "tid": task_id},
        )
        await db.commit()
    return True
