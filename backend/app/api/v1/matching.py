import asyncio
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict
from sqlalchemy import text
from app.agents.harness import harness
from app.agents.job_matcher.db_utils import save_selected_job, get_selected_job
from app.db.mysql import AsyncSessionLocal
from app.middleware.auth import get_current_user

router = APIRouter()


class MatchRequest(BaseModel):
    radar_data: Optional[List[int]] = None
    dimension_details: Optional[Dict] = None


class SelectJobRequest(BaseModel):
    job_data: Dict


async def push_to_planners(user_id: int, top_job: dict):
    """异步推送匹配结果给 career_planner 和 learning_plan"""
    try:
        job_name = top_job.get("job_title", "") or top_job.get("job_name", "")
        await asyncio.gather(
            harness.run(
                "career_planner",
                {"user_id": user_id, "top_job": top_job},
                user_id=user_id,
            ),
            harness.run(
                "learning_plan",
                {"user_id": user_id, "action": "generate", "target_job": job_name},
                user_id=user_id,
            ),
            return_exceptions=True,
        )
    except Exception as e:
        print(f"[Matching] push_to_planners error: {e}")


async def push_career_planner(user_id: int, top_job: dict):
    """异步推送匹配结果给 career_planner（learning_plan 已在 select-job 中同步完成）"""
    try:
        await harness.run(
            "career_planner",
            {"user_id": user_id, "top_job": top_job},
            user_id=user_id,
        )
    except Exception as e:
        print(f"[Matching] push_career_planner error: {e}")


@router.post("/match")
async def match_jobs(req: MatchRequest = None, user: dict = Depends(get_current_user)):
    input_data = {"user_id": user["user_id"]}

    # If frontend sends profile data, use it directly
    if req and req.radar_data and any(v > 0 for v in req.radar_data):
        input_data["user_profile"] = {
            "radar_data": req.radar_data,
            "dimension_details": req.dimension_details or {},
            "source": "frontend",
        }

    result = await harness.run(
        "job_matcher",
        input_data,
        user_id=user["user_id"],
    )

    # 异步推送匹配结果给 career_planner 和 learning_plan
    if result.get("success") and result.get("data"):
        matches = result["data"].get("matches", [])
        if matches:
            top_job = matches[0]
            # 不等待完成，立即返回匹配结果给前端
            asyncio.create_task(push_to_planners(user["user_id"], top_job))

    return result


@router.post("/select-job")
async def select_job(req: SelectJobRequest, user: dict = Depends(get_current_user)):
    """Save user's selected/locked job and clear stale tasks."""
    uid = user["user_id"]
    await save_selected_job(uid, req.job_data)
    job_name = req.job_data.get("job_title", "") or req.job_data.get("job_name", "")
    print(f"[Matching] select-job: saved '{job_name}' for user {uid}, old tasks cleared")

    # career_planner 异步执行
    asyncio.create_task(push_career_planner(uid, req.job_data))

    return {"success": True, "message": "岗位已锁定"}


@router.get("/selected-job")
async def get_user_selected_job(user: dict = Depends(get_current_user)):
    """Get user's currently selected/locked job."""
    job = await get_selected_job(user["user_id"])
    return {"success": True, "data": job}


@router.get("/has-matching")
async def has_matching(user: dict = Depends(get_current_user)):
    """Check if user has any matching data (selected job or match report)."""
    uid = user["user_id"]
    # Check selected job first
    selected = await get_selected_job(uid)
    if selected:
        return {"success": True, "has_data": True}
    # Check matching_report table
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("SELECT 1 FROM matching_report WHERE user_id = :uid LIMIT 1"),
            {"uid": uid},
        )
        row = result.fetchone()
    return {"success": True, "has_data": row is not None}


import re as _re


@router.get("/capability-model")
async def get_capability_model(user: dict = Depends(get_current_user)):
    """Get capability model data for radar chart from the selected job's matching scores."""
    uid = user["user_id"]
    job = await get_selected_job(uid)
    if not job or not job.get("scores"):
        return {"success": True, "data": None}

    scores = job["scores"]
    # Map Chinese dimension names
    DIM_MAP = {
        "专业技能": "专业技能", "证书资质": "证书", "创新能力": "创新能力",
        "学习能力": "学习能力", "抗压能力": "抗压能力", "沟通能力": "沟通能力",
        "实习/项目经验": "实习能力",
    }
    # Standard order matching the frontend radar
    STD_DIMS = ["专业技能", "创新能力", "学习能力", "实习能力", "抗压能力", "沟通能力", "证书"]

    current = []
    target = []
    for dim in STD_DIMS:
        # Find matching score entry
        src_key = next((k for k, v in DIM_MAP.items() if v == dim), dim)
        entry = scores.get(src_key, {})
        cur_val = entry.get("score", 0)
        current.append(cur_val)

        # Parse target from gap text like "需提升至85+（当前55）" or "超出岗位要求（岗位期望65）"
        gap = entry.get("gap", "")
        target_val = cur_val
        if gap:
            m = _re.search(r"提升至(\d+)", gap)
            if m:
                target_val = int(m.group(1))
            else:
                # Handle "超出岗位要求（岗位期望65）" format
                m = _re.search(r"期望(\d+)", gap)
                if m:
                    target_val = int(m.group(1))
                else:
                    m = _re.search(r"要求.*?(\d+)分", gap)
                    if m:
                        target_val = int(m.group(1))
                    else:
                        m = _re.search(r"(\d+)\+", gap)
                        if m:
                            target_val = int(m.group(1))
        target.append(target_val)

    return {
        "success": True,
        "data": {
            "dimensions": STD_DIMS,
            "current_level": current,
            "target_level": target,
            "job_title": job.get("job_title", ""),
        },
    }
