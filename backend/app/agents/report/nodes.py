"""报告智能体图节点。"""

import re
import json
import asyncio

from langchain_core.messages import SystemMessage, HumanMessage

from app.agents.llm_factory import get_llm
from app.agents.report import tools
from app.agents.report import prompts

DIM_NAMES = ["专业技能", "创新能力", "学习能力", "实习能力", "抗压能力", "沟通能力", "证书"]


def _format_profile(profile: dict | None) -> dict:
    """格式化用户画像为可读文本。"""
    if not profile:
        return {"radar_summary": "暂无数据", "dimension_summary": "暂无数据", "resume_summary": "暂无数据"}

    radar = profile.get("radar_data", [])
    if radar and len(radar) >= 7:
        lines = []
        for i, name in enumerate(DIM_NAMES):
            score = radar[i] if i < len(radar) else 0
            level = "优秀" if score >= 85 else "良好" if score >= 70 else "中等" if score >= 60 else "待提升"
            lines.append(f"{name}：{score}分（{level}）")
        radar_summary = "、".join(lines)
    else:
        radar_summary = "暂无数据"

    details = profile.get("dimension_details", {})
    dim_lines = []
    if details:
        for name, info in details.items():
            if isinstance(info, dict):
                score = info.get("score", 0)
                desc = info.get("desc", "")
                status = info.get("status", "")
                if desc:
                    dim_lines.append(f"{name}（{score}分，{status}）：{desc}")
    dimension_summary = "\n".join(dim_lines) if dim_lines else "暂无数据"

    resume = profile.get("resume_text", "")
    resume_summary = resume[:600] if resume else "暂无数据"

    return {"radar_summary": radar_summary, "dimension_summary": dimension_summary, "resume_summary": resume_summary}


def _format_job(job: dict | None) -> str:
    """格式化岗位信息。"""
    if not job:
        return "暂无锁定岗位"
    parts = []
    if job.get("job_title"):
        parts.append(f"岗位名称：{job['job_title']}")
    if job.get("company"):
        parts.append(f"公司：{job['company']}")
    if job.get("city"):
        parts.append(f"城市：{job['city']}")
    if job.get("salary_range"):
        parts.append(f"薪资：{job['salary_range']}")
    if job.get("total_score"):
        parts.append(f"综合匹配分：{job['total_score']}")
    scores = job.get("scores", {})
    if scores:
        score_parts = []
        for name, val in scores.items():
            s = val if isinstance(val, int) else val.get("score", 0) if isinstance(val, dict) else 0
            score_parts.append(f"{name}：{s}分")
        parts.append("各维度分数：" + "、".join(score_parts))
    if job.get("summary"):
        parts.append(f"AI简评：{job['summary']}")
    return "\n".join(parts) if parts else "暂无岗位信息"


def _format_match(match: dict | None) -> str:
    """格式化匹配结果。"""
    if not match:
        return "暂无匹配结果"
    results = match.get("ranked_results", [])
    if not results:
        return "暂无匹配结果"
    lines = []
    for i, r in enumerate(results[:5]):
        title = r.get("job_title", f"岗位{i+1}")
        company = r.get("company", "")
        score = r.get("total_score", 0)
        lines.append(f"{i+1}. {title}（{company}）匹配分：{score}")
    return "\n".join(lines)


def _format_plan(plan: dict | None) -> str:
    """格式化学习计划。"""
    if not plan:
        return "暂无学习计划"
    parts = []
    if plan.get("target_job"):
        parts.append(f"目标岗位：{plan['target_job']}")
    if plan.get("total_duration"):
        parts.append(f"预计时长：{plan['total_duration']}")
    phases = plan.get("phases", [])
    if isinstance(phases, str):
        try:
            phases = json.loads(phases)
        except Exception:
            phases = []
    for i, phase in enumerate(phases):
        name = phase.get("phase_name", phase.get("title", f"阶段{i+1}"))
        goals = phase.get("goals", [])
        content = phase.get("content", [])
        duration = phase.get("duration", "")
        parts.append(f"第{i+1}阶段：{name}")
        if duration:
            parts.append(f"  时长：{duration}")
        if goals:
            parts.append(f"  目标：{'、'.join(goals[:3])}")
        if content:
            parts.append(f"  内容：{'、'.join(content[:3])}")
    return "\n".join(parts) if parts else "暂无学习计划"


def _format_career(career: dict | None) -> str:
    """格式化职业规划。"""
    if not career:
        return "暂无职业规划"
    parts = []
    path = career.get("career_path", career)
    if path.get("phases"):
        for i, phase in enumerate(path["phases"]):
            name = phase.get("phase_name", phase.get("title", f"阶段{i+1}"))
            parts.append(f"第{i+1}阶段：{name}")
            if phase.get("goals"):
                parts.append(f"  目标：{'、'.join(phase['goals'][:3])}")
    trends = career.get("trends", {})
    if trends.get("salary_forecast"):
        salary_parts = [f"{s['year']}年：{s['value']}元" for s in trends["salary_forecast"][:3]]
        parts.append("薪资趋势：" + "、".join(salary_parts))
    if trends.get("demand_trend"):
        demand_parts = [f"{d['year']}年：指数{d['value']}" for d in trends["demand_trend"][:3]]
        parts.append("需求趋势：" + "、".join(demand_parts))
    return "\n".join(parts) if parts else "暂无职业规划"


def _format_tasks(tasks: list) -> str:
    """格式化每日任务。"""
    if not tasks:
        return "暂无每日任务"
    lines = []
    for i, t in enumerate(tasks):
        title = t.get("title", t.get("text", f"任务{i+1}"))
        desc = t.get("description", t.get("desc", ""))
        diff = t.get("difficulty", "中等")
        lines.append(f"{i+1}. {title}（难度：{diff}）")
        if desc:
            lines.append(f"   {desc}")
    return "\n".join(lines)


# ────────────────────── Nodes ──────────────────────


async def load_all_data(state: dict) -> dict:
    """从数据库加载所有模块数据。"""
    uid = state["user_id"]
    profile, job, match, plan, career, tasks = await asyncio.gather(
        tools.load_user_profile(uid),
        tools.load_selected_job(uid),
        tools.load_match_report(uid),
        tools.load_learning_plan(uid),
        tools.load_career_plan(uid),
        tools.load_daily_tasks(uid),
    )

    return {
        "user_profile": profile,
        "selected_job": job,
        "match_results": match,
        "learning_plan": plan,
        "career_plan": {**career, "daily_tasks": tasks} if career else {"daily_tasks": tasks},
    }


async def generate_report(state: dict) -> dict:
    """聚合数据，LLM 生成完整报告。"""
    profile_ctx = _format_profile(state.get("user_profile"))
    job_text = _format_job(state.get("selected_job"))
    match_text = _format_match(state.get("match_results"))
    plan_text = _format_plan(state.get("learning_plan"))
    career_text = _format_career(state.get("career_plan"))
    tasks_text = _format_tasks(state.get("career_plan", {}).get("daily_tasks", []))

    user_msg = prompts.REPORT_USER.format(
        radar_summary=profile_ctx["radar_summary"],
        dimension_summary=profile_ctx["dimension_summary"],
        resume_summary=profile_ctx["resume_summary"],
        job_summary=job_text,
        match_summary=match_text,
        plan_summary=plan_text,
        career_summary=career_text + "\n\n每日任务：\n" + tasks_text,
    )

    try:
        llm = get_llm(temperature=0.6)
        resp = await asyncio.wait_for(
            llm.ainvoke([
                SystemMessage(content=prompts.REPORT_SYSTEM),
                HumanMessage(content=user_msg),
            ]),
            timeout=90,
        )
        report_text = resp.content.strip()
    except Exception as e:
        print(f"[report] generate_report LLM error: {e}")
        report_text = _fallback_report(profile_ctx, job_text, match_text, plan_text, career_text, tasks_text)

    return {"report_text": report_text}


async def polish_report(state: dict) -> dict:
    """根据用户指令润色报告。"""
    feedback = state.get("polish_feedback", "")
    report_text = state.get("report_text", "")

    if not report_text:
        return {"error": "没有可润色的报告内容"}

    try:
        llm = get_llm(temperature=0.5)
        resp = await asyncio.wait_for(
            llm.ainvoke([
                SystemMessage(content=prompts.POLISH_SYSTEM),
                HumanMessage(content=prompts.POLISH_USER.format(
                    feedback=feedback, report_text=report_text,
                )),
            ]),
            timeout=90,
        )
        polished = resp.content.strip()
    except Exception as e:
        print(f"[report] polish_report LLM error: {e}")
        polished = report_text

    return {"polished_text": polished}


async def format_report(state: dict) -> dict:
    """清理格式，去除残留特殊符号。"""
    text = state.get("polished_text") or state.get("report_text", "")

    # 去除 markdown 标记
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'^\s*[-*]\s+', '  ', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # 保存报告
    uid = state.get("user_id")
    if uid and text:
        await tools.save_report(uid, text)

    return {"report_text": text}


def _fallback_report(profile_ctx, job_text, match_text, plan_text, career_text, tasks_text) -> str:
    """LLM 失败时的兜底报告。"""
    sections = [
        ("一、个人能力概况", profile_ctx["radar_summary"]),
        ("二、目标岗位分析", job_text),
        ("三、岗位匹配评估", match_text),
        ("四、学习计划", plan_text),
        ("五、职业发展路径", career_text),
        ("六、每日任务清单", tasks_text),
    ]
    lines = ["职业分析报告", ""]
    for title, content in sections:
        lines.append(f"【{title}】")
        lines.append(content)
        lines.append("")
    lines.append("【七、综合建议】")
    lines.append("请根据以上分析，制定针对性的学习计划，持续提升弱项能力。")
    return "\n".join(lines)
