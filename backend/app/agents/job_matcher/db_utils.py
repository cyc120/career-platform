"""Database utilities for job_matcher agent.

Fixed from old code: corrected all column name references,
uses unified config, async SQLAlchemy session.
"""
from sqlalchemy import text
from app.db.mysql import AsyncSessionLocal


async def get_user_profile(user_id: int) -> dict | None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text(
                "SELECT up.profile_data FROM user_profiles up "
                "WHERE up.user_id = :uid AND up.status = 'active'"
            ),
            {"uid": user_id},
        )
        row = result.fetchone()
        return dict(row._mapping) if row else None


async def get_user_favorites(user_id: int) -> list[int]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("SELECT job_id FROM favorites WHERE user_id = :uid"),
            {"uid": user_id},
        )
        return [r[0] for r in result.fetchall()]


async def get_job_details(job_ids: list[int]) -> list[dict]:
    if not job_ids:
        return []
    placeholders = ", ".join(f":id{i}" for i in range(len(job_ids)))
    params = {f"id{i}": int(vid) for i, vid in enumerate(job_ids)}
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text(
                f"SELECT id, job_title, company, industry, city, salary_range, "
                f"job_description, requirements FROM jobs WHERE id IN ({placeholders})"
            ),
            params,
        )
        return [dict(r._mapping) for r in result.fetchall()]


async def save_user_profile(user_id: int, profile_data: dict) -> bool:
    import json
    from app.config import settings
    pd = json.dumps(profile_data, ensure_ascii=False)
    async with AsyncSessionLocal() as db:
        if settings.DB_BACKEND == "sqlite":
            await db.execute(
                text(
                    "INSERT OR REPLACE INTO user_profiles (user_id, profile_data, status, updated_at) "
                    "VALUES (:uid, :pd, 'active', datetime('now'))"
                ),
                {"uid": user_id, "pd": pd},
            )
        else:
            await db.execute(
                text(
                    "INSERT INTO user_profiles (user_id, profile_data, status) "
                    "VALUES (:uid, :pd, 'active') "
                    "ON DUPLICATE KEY UPDATE profile_data = :pd2, "
                    "updated_at = CURRENT_TIMESTAMP"
                ),
                {"uid": user_id, "pd": pd, "pd2": pd},
            )
        await db.commit()
    return True


async def save_match_report(user_id: int, job_name: str, match_score: float,
                            report_data: dict, industry: str = "", city: str = "") -> int:
    import json
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text(
                "INSERT INTO matching_report (user_id, job_name, industry, city, "
                "match_score, report_data, publish_date) "
                "VALUES (:uid, :jn, :ind, :ct, :ms, :rd, DATE('now'))"
            ),
            {
                "uid": user_id, "jn": job_name, "ind": industry, "ct": city,
                "ms": match_score, "rd": json.dumps(report_data, ensure_ascii=False),
            },
        )
        await db.commit()
    return result.lastrowid


async def save_analysis_result(user_id: int, analysis: dict,
                                target_position: str = "", target_company: str = "") -> bool:
    async with AsyncSessionLocal() as db:
        await db.execute(
            text(
                "INSERT INTO career_plans (user_id, target_position, target_company, "
                "plan_data, status) VALUES (:uid, :tp, :tc, :pd, 'active')"
            ),
            {
                "uid": user_id, "tp": target_position, "tc": target_company,
                "pd": str(analysis),
            },
        )
        await db.commit()
    return True


async def save_selected_job(user_id: int, job_data: dict) -> bool:
    import json
    from app.config import settings
    jd = json.dumps(job_data, ensure_ascii=False)
    job_title = job_data.get("job_title", "")
    print(f"[DB] save_selected_job: user_id={user_id}, job_title='{job_title}', json_len={len(jd)}")
    async with AsyncSessionLocal() as db:
        if settings.DB_BACKEND == "sqlite":
            await db.execute(
                text(
                    "INSERT OR REPLACE INTO user_selected_job (user_id, job_data, updated_at) "
                    "VALUES (:uid, :jd, datetime('now'))"
                ),
                {"uid": user_id, "jd": jd},
            )
        else:
            await db.execute(
                text(
                    "INSERT INTO user_selected_job (user_id, job_data) "
                    "VALUES (:uid, :jd) "
                    "ON DUPLICATE KEY UPDATE job_data = :jd2, updated_at = NOW()"
                ),
                {"uid": user_id, "jd": jd, "jd2": jd},
            )
        # 切换岗位时清除旧的每日任务，避免返回旧岗位的缓存任务
        await db.execute(
            text("DELETE FROM daily_tasks WHERE user_id = :uid"),
            {"uid": user_id},
        )
        await db.commit()
    return True


async def get_selected_job(user_id: int) -> dict | None:
    import json
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("SELECT job_data FROM user_selected_job WHERE user_id = :uid"),
            {"uid": user_id},
        )
        row = result.fetchone()
        if row:
            try:
                data = json.loads(row[0])
                print(f"[DB] get_selected_job: user_id={user_id}, job_title='{data.get('job_title', '')}'")
                return data
            except Exception:
                print(f"[DB] get_selected_job: user_id={user_id}, JSON parse error")
                return None
        print(f"[DB] get_selected_job: user_id={user_id}, no row found")
        return None
