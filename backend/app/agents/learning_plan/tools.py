"""Database tools for learning_plan agent."""

import json
from datetime import date
from sqlalchemy import text
from app.db.mysql import AsyncSessionLocal


async def get_target_job(user_id: int) -> dict | None:
    # 优先查询用户锁定的岗位
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("SELECT job_data FROM user_selected_job WHERE user_id = :uid"),
            {"uid": user_id},
        )
        row = result.fetchone()
        if row:
            try:
                job = json.loads(row[0])
                return {"job_name": job.get("job_title", ""), "match_score": job.get("total_score", 0)}
            except Exception:
                pass

    # 回退到匹配报告中得分最高的岗位
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
    from app.config import settings
    phases_json = json.dumps(phases, ensure_ascii=False)
    async with AsyncSessionLocal() as db:
        if settings.DB_BACKEND == "sqlite":
            await db.execute(
                text(
                    "INSERT OR REPLACE INTO learning_plans "
                    "(user_id, target_job, plan_type, phases, updated_at) "
                    "VALUES (:uid, :tj, :pt, :ph, datetime('now'))"
                ),
                {"uid": user_id, "tj": target_job, "pt": plan_type, "ph": phases_json},
            )
        else:
            await db.execute(
                text(
                    "INSERT INTO learning_plans (user_id, target_job, plan_type, phases, updated_at) "
                    "VALUES (:uid, :tj, :pt, :ph, NOW()) "
                    "ON DUPLICATE KEY UPDATE target_job = :tj2, plan_type = :pt2, "
                    "phases = :ph2, updated_at = NOW()"
                ),
                {
                    "uid": user_id, "tj": target_job, "pt": plan_type,
                    "ph": phases_json, "tj2": target_job, "pt2": plan_type, "ph2": phases_json,
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


async def save_daily_tasks(user_id: int, tasks: list[dict], target_job: str = "") -> int:
    if not tasks:
        return 0

    # 先删除该用户旧的任务
    async with AsyncSessionLocal() as db:
        await db.execute(
            text("DELETE FROM daily_tasks WHERE user_id = :uid"),
            {"uid": user_id},
        )
        await db.commit()

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
                    "res": json.dumps({
                        "difficulty": task.get("difficulty", "中等"),
                        "target_job": target_job,
                        "resources": task.get("resources", []),
                    }, ensure_ascii=False),
                },
            )
            count += 1
        await db.commit()
    return count


async def get_daily_tasks(user_id: int) -> list[dict]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text(
                "SELECT id, task_date, title, description, duration, resources, status "
                "FROM daily_tasks WHERE user_id = :uid ORDER BY task_date, id"
            ),
            {"uid": user_id},
        )
        rows = [dict(r._mapping) for r in result.fetchall()]
        # 解析 resources 字段提取 difficulty 和 target_job
        for row in rows:
            try:
                res = json.loads(row.get("resources", "{}"))
                row["difficulty"] = res.get("difficulty", "中等")
                row["target_job"] = res.get("target_job", "")
            except Exception:
                row["difficulty"] = "中等"
                row["target_job"] = ""
        return rows


async def update_task_status(task_id: int, status: str) -> bool:
    async with AsyncSessionLocal() as db:
        await db.execute(
            text("UPDATE daily_tasks SET status = :s WHERE id = :tid"),
            {"s": status, "tid": task_id},
        )
        await db.commit()
    return True
