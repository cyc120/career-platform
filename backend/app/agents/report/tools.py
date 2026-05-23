"""报告智能体数据访问层。"""

import json
from sqlalchemy import text
from app.db.mysql import AsyncSessionLocal


async def load_user_profile(user_id: int) -> dict | None:
    """加载用户画像。"""
    from app.agents.job_matcher.db_utils import get_user_profile
    record = await get_user_profile(user_id)
    if not record:
        return None
    profile = record.get("profile_data")
    if isinstance(profile, str):
        try:
            profile = json.loads(profile)
        except Exception:
            return None
    return profile


async def load_selected_job(user_id: int) -> dict | None:
    """加载锁定岗位。"""
    from app.agents.job_matcher.db_utils import get_selected_job
    return await get_selected_job(user_id)


async def load_match_report(user_id: int) -> dict | None:
    """加载匹配报告。"""
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                text("SELECT report_data FROM matching_report WHERE user_id = :uid ORDER BY id DESC LIMIT 1"),
                {"uid": user_id},
            )
            row = result.first()
            if not row:
                return None
            data = row[0]
            if isinstance(data, str):
                data = json.loads(data)
            return data
    except Exception as e:
        print(f"[report/tools] load_match_report error: {e}")
        return None


async def load_learning_plan(user_id: int) -> dict | None:
    """加载学习计划。"""
    from app.agents.learning_plan.tools import get_learning_plan
    return await get_learning_plan(user_id)


async def load_career_plan(user_id: int) -> dict | None:
    """加载职业规划。"""
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                text("SELECT plan_data FROM career_plans WHERE user_id = :uid ORDER BY id DESC LIMIT 1"),
                {"uid": user_id},
            )
            row = result.first()
            if not row:
                return None
            data = row[0]
            if isinstance(data, str):
                data = json.loads(data)
            return data
    except Exception as e:
        print(f"[report/tools] load_career_plan error: {e}")
        return None


async def load_daily_tasks(user_id: int) -> list:
    """加载每日任务。"""
    from app.agents.learning_plan.tools import get_daily_tasks
    return await get_daily_tasks(user_id)


async def save_report(user_id: int, report_text: str) -> bool:
    """保存报告到数据库。"""
    try:
        async with AsyncSessionLocal() as db:
            if hasattr(db, 'execute'):
                from app.config import settings
                if settings.DB_BACKEND == "sqlite":
                    await db.execute(text(
                        "INSERT INTO user_reports (user_id, report_text, created_at) "
                        "VALUES (:uid, :text, datetime('now')) "
                        "ON CONFLICT(user_id) DO UPDATE SET report_text = :text, created_at = datetime('now')"
                    ), {"uid": user_id, "text": report_text})
                else:
                    await db.execute(text(
                        "INSERT INTO user_reports (user_id, report_text, created_at) "
                        "VALUES (:uid, :text, NOW()) "
                        "ON DUPLICATE KEY UPDATE report_text = :text, created_at = NOW()"
                    ), {"uid": user_id, "text": report_text})
                await db.commit()
                return True
    except Exception as e:
        print(f"[report/tools] save_report error: {e}")
    return False


async def load_report(user_id: int) -> str | None:
    """加载已保存的报告。"""
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                text("SELECT report_text FROM user_reports WHERE user_id = :uid ORDER BY id DESC LIMIT 1"),
                {"uid": user_id},
            )
            row = result.first()
            return row[0] if row else None
    except Exception as e:
        print(f"[report/tools] load_report error: {e}")
        return None
