"""Database tools for career_planner agent."""

import json
from sqlalchemy import text
from app.db.mysql import AsyncSessionLocal


async def get_top_matched_job(user_id: int) -> dict | None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text(
                "SELECT job_name, industry, city, match_score, report_data "
                "FROM matching_report WHERE user_id = :uid "
                "ORDER BY match_score DESC LIMIT 1"
            ),
            {"uid": user_id},
        )
        row = result.fetchone()
        return dict(row._mapping) if row else None


async def get_promotion_transitions(job_name: str) -> list[dict]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text(
                "SELECT current_role, next_role, required_skills, years_exp, "
                "transition_type FROM promotion_transition "
                "WHERE current_role LIKE :name OR next_role LIKE :name2"
            ),
            {"name": f"%{job_name}%", "name2": f"%{job_name}%"},
        )
        return [dict(r._mapping) for r in result.fetchall()]


async def save_career_plan(user_id: int, top_job: dict, match_score: float,
                            trends: dict, career_path: dict) -> int:
    plan_data = json.dumps({
        "top_job": top_job,
        "match_score": match_score,
        "trends": trends,
        "career_path": career_path,
    }, ensure_ascii=False, default=str)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text(
                "INSERT INTO career_plans (user_id, target_position, target_company, "
                "plan_data, status) VALUES (:uid, :tp, :tc, :pd, 'active')"
            ),
            {
                "uid": user_id,
                "tp": top_job.get("job_name", ""),
                "tc": "",
                "pd": plan_data,
            },
        )
        await db.commit()
    return result.lastrowid
