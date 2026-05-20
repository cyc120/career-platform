"""LangGraph nodes for Career Planner agent."""

import json
import os
from typing import Dict

from langchain_core.messages import HumanMessage, SystemMessage
from app.config import settings

from app.agents.llm_factory import get_llm
from app.agents.career_planner.state import CareerPlannerState
from app.agents.career_planner.prompts import (
    TREND_SYSTEM_PROMPT, TREND_USER_PROMPT,
    PATH_SYSTEM_PROMPT, PATH_USER_PROMPT,
)
from app.agents.career_planner import tools


async def get_top_job(state: CareerPlannerState) -> Dict:
    uid = state["user_id"]
    top = await tools.get_top_matched_job(uid)
    return {"top_job": top or {}}


async def predict_trends(state: CareerPlannerState) -> Dict:
    top = state.get("top_job", {})
    profile = state.get("user_profile", {})
    job_name = top.get("job_name", "")

    if not job_name:
        return {"trends": {}}

    # Extract skills from profile
    skills = ", ".join(profile.get("技能清单", {}).get("content", "").split("\n")[:5]) if profile else ""

    llm = get_llm(temperature=0.7)
    msg = llm.invoke([
        SystemMessage(content=TREND_SYSTEM_PROMPT + "\n输出纯JSON。"),
        HumanMessage(content=TREND_USER_PROMPT.format(job_name=job_name, skills=skills or "未提供")),
    ])
    try:
        return {"trends": _parse_json(msg.content)}
    except Exception:
        return {"trends": {"job_name": job_name, "error": "预测生成失败"}}


async def get_promotion_data(state: CareerPlannerState) -> Dict:
    top = state.get("top_job", {})
    job_name = top.get("job_name", "")
    if not job_name:
        return {"promotion_data": []}
    data = await tools.get_promotion_transitions(job_name)
    return {"promotion_data": data}


async def generate_career_path(state: CareerPlannerState) -> Dict:
    top = state.get("top_job", {})
    profile = state.get("user_profile", {})
    promo = state.get("promotion_data", [])

    llm = get_llm(temperature=0.7)
    msg = llm.invoke([
        SystemMessage(content=PATH_SYSTEM_PROMPT + "\n输出纯JSON。"),
        HumanMessage(content=PATH_USER_PROMPT.format(
            user_profile=json.dumps(profile, ensure_ascii=False),
            job_name=top.get("job_name", ""),
            promotion_data=json.dumps(promo, ensure_ascii=False),
        )),
    ])
    try:
        return {"career_path": _parse_json(msg.content)}
    except Exception:
        return {"career_path": {}}


async def plot_chart(state: CareerPlannerState) -> Dict:
    """Generate a dual-axis trend chart and save to static."""
    trends = state.get("trends", {})
    if not trends:
        return {"chart_path": ""}

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        years = ["2026", "2027", "2028"]
        salary = trends.get("salary_trend", [20, 25, 30])
        demand = trends.get("demand_trend", [70, 80, 90])

        fig, ax1 = plt.subplots(figsize=(8, 4))
        ax1.bar(years, salary, color="steelblue", alpha=0.7)
        ax1.set_ylabel("年薪(万)", color="steelblue")
        ax2 = ax1.twinx()
        ax2.plot(years, demand, "ro-", linewidth=2)
        ax2.set_ylabel("需求量指数", color="red")
        plt.title(f'{trends.get("job_name", "")} 发展趋势')
        plt.tight_layout()

        os.makedirs(os.path.join(settings.UPLOAD_DIR, "charts"), exist_ok=True)
        path = os.path.join(settings.UPLOAD_DIR, "charts", "career_trends.png")
        plt.savefig(path, dpi=100)
        plt.close()
        return {"chart_path": path}
    except Exception:
        return {"chart_path": ""}


async def save_plan(state: CareerPlannerState) -> Dict:
    uid = state["user_id"]
    top = state.get("top_job", {})
    trends = state.get("trends", {})
    career_path = state.get("career_path", {})

    try:
        pid = await tools.save_career_plan(
            uid, top, float(top.get("match_score", 0)), trends, career_path
        )
        return {"plan_id": pid}
    except Exception:
        return {"plan_id": 0}


def _parse_json(content: str) -> dict:
    c = content.strip()
    for marker in ("```json", "```"):
        if marker in c:
            c = c.split(marker)[1].split("```")[0]
            break
    return json.loads(c)
