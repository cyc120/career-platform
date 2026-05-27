import asyncio
import re as _re
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict
from sqlalchemy import text
from app.agents.harness import harness
from app.agents.job_matcher.db_utils import save_selected_job, get_selected_job
from app.db.mysql import AsyncSessionLocal
from app.db.neo4j import neo4j_manager
from app.middleware.auth import get_current_user

router = APIRouter()


class MatchRequest(BaseModel):
    radar_data: Optional[List[int]] = None
    dimension_details: Optional[Dict] = None


class SelectJobRequest(BaseModel):
    job_data: Dict


def _task_done_callback(task: asyncio.Task, label: str):
    """Log errors from fire-and-forget background tasks."""
    if task.cancelled():
        return
    exc = task.exception()
    if exc:
        print(f"[Matching] background task '{label}' failed: {exc}")


async def push_to_planners(user_id: int, top_job: dict):
    """异步推送匹配结果给 career_planner 和 learning_plan"""
    try:
        job_name = top_job.get("job_title", "") or top_job.get("job_name", "")
        results = await asyncio.gather(
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
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                print(f"[Matching] push_to_planners subtask {i} error: {r}")
            elif isinstance(r, dict) and not r.get("success"):
                print(f"[Matching] push_to_planners subtask {i} failed: {r.get('error')}")
    except Exception as e:
        print(f"[Matching] push_to_planners error: {e}")


async def push_career_planner(user_id: int, top_job: dict):
    """异步推送匹配结果给 career_planner（learning_plan 已在 select-job 中同步完成）"""
    try:
        result = await harness.run(
            "career_planner",
            {"user_id": user_id, "top_job": top_job},
            user_id=user_id,
        )
        if isinstance(result, dict) and not result.get("success"):
            print(f"[Matching] push_career_planner failed: {result.get('error')}")
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
            task = asyncio.create_task(push_to_planners(user["user_id"], top_job))
            task.add_done_callback(lambda t: _task_done_callback(t, "push_to_planners"))

    return result


@router.post("/select-job")
async def select_job(req: SelectJobRequest, user: dict = Depends(get_current_user)):
    """Save user's selected/locked job and clear stale tasks."""
    uid = user["user_id"]
    await save_selected_job(uid, req.job_data)
    job_name = req.job_data.get("job_title", "") or req.job_data.get("job_name", "")
    print(f"[Matching] select-job: saved '{job_name}' for user {uid}, old tasks cleared")

    # career_planner 异步执行
    task = asyncio.create_task(push_career_planner(uid, req.job_data))
    task.add_done_callback(lambda t: _task_done_callback(t, "push_career_planner"))

    return {"success": True, "message": "岗位已锁定"}


@router.get("/selected-job")
async def get_user_selected_job(user: dict = Depends(get_current_user)):
    """Get user's currently selected/locked job."""
    job = await get_selected_job(user["user_id"])
    return {"success": True, "data": job}


@router.delete("/selected-job")
async def clear_selected_job(user: dict = Depends(get_current_user)):
    """Clear user's locked job (unlock)."""
    uid = user["user_id"]
    async with AsyncSessionLocal() as db:
        await db.execute(
            text("DELETE FROM user_selected_job WHERE user_id = :uid"),
            {"uid": uid},
        )
        await db.execute(
            text("DELETE FROM daily_tasks WHERE user_id = :uid"),
            {"uid": uid},
        )
        await db.commit()
    print(f"[Matching] cleared selected job for user {uid}")
    return {"success": True, "message": "已取消锁定"}


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


# ==================== 岗位知识图谱 ====================

# 前端岗位名称 → Neo4j 中心节点名称映射
JOB_NAME_MAP = {
    "软件测试": "软件测试工程师（专项方向）",
    "C/C++": "C/C++开发工程师",
    "前端开发": "前端开发工程师",
    "Java": "Java开发工程师",
    "Java后端开发": "Java开发工程师",
    "Java资深工程师": "Java开发工程师",
    "硬件测试": "硬件测试工程师",
    "测试工程师": "软件测试工程师（专项方向）",
    "Python后端开发": "Python后端开发工程师",
    "数据分析": "数据分析师",
    "产品": "产品经理",
}


def _match_neo4j_position(job_title: str) -> str:
    """将前端岗位名称映射到 Neo4j 中的标准名称。"""
    if not job_title:
        return ""
    # 精确匹配
    if job_title in JOB_NAME_MAP:
        return JOB_NAME_MAP[job_title]
    # 模糊匹配：检查映射表的 key 是否被包含
    for key, value in JOB_NAME_MAP.items():
        if key in job_title or job_title in key:
            return value
    # 无映射，直接使用原标题
    return job_title


@router.get("/job-graph")
async def get_job_graph(job_title: str, user: dict = Depends(get_current_user)):
    """获取指定岗位在 Neo4j 中的知识图谱数据"""
    position = _match_neo4j_position(job_title)
    if not position:
        return {"success": False, "error": f"未找到岗位「{job_title}」对应的图谱"}

    try:
        session = await neo4j_manager.get_session()
        if session is None:
            return {"success": False, "error": "Neo4j 连接不可用"}

        # Neo4j 标签为中文：岗位、能力维度、核心要求
        # 关系类型：包含维度、核心要求
        cypher = """
            MATCH (j:`岗位`)-[r*1..2]-(m)
            WHERE j.name = $jobTitle
            RETURN j, r, m LIMIT 300
        """
        result = await session.run(cypher, jobTitle=position)
        records = [record async for record in result]
        await session.close()

        # 构建节点和连线
        nodes = {}
        links = []

        def _node_id(node):
            return str(node.element_id) if hasattr(node, "element_id") else str(node.identity)

        for record in records:
            for key in ("j", "m"):
                node = record.get(key)
                if not node:
                    continue
                nid = _node_id(node)
                if nid in nodes:
                    continue
                label = next(iter(node.labels)) if node.labels else "Default"
                # 岗位和能力维度用 name，核心要求用 content
                props = dict(node)
                name = props.get("name") or props.get("content") or label
                nodes[nid] = {"id": nid, "name": name, "label": label}

            rel = record.get("r")
            if rel:
                rels = rel if isinstance(rel, list) else [rel]
                for r in rels:
                    src = _node_id(r.start_node)
                    tgt = _node_id(r.end_node)
                    links.append({"source": src, "target": tgt})

        if not nodes:
            return {"success": False, "error": f"Neo4j 中未找到岗位「{position}」的数据"}

        return {
            "success": True,
            "data": {
                "nodes": list(nodes.values()),
                "links": links,
                "center": position,
            },
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
