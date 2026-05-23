"""LangGraph nodes for Learning Plan agent."""

import json
from typing import Dict
from datetime import date

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.llm_factory import get_llm
from app.agents.learning_plan.state import LearningPlanState
from app.agents.learning_plan import prompts, tools
from app.rag.retrievers import learning_retriever


async def detect_action_node(state: LearningPlanState) -> Dict:
    """Node: pass through state, routing is handled by detect_action."""
    return {}


async def detect_action(state: LearningPlanState) -> str:
    """Routing function: determine which branch to take."""
    action = state.get("action", "generate")
    valid = {"generate", "polish", "daily_tasks", "adjust", "export"}
    return action if action in valid else "generate"


async def load_profile_and_job(state: LearningPlanState) -> Dict:
    # 优先使用传入的 target_job（来自 job_matcher 推送）
    if state.get("target_job"):
        return {"target_job": state["target_job"]}
    uid = state["user_id"]
    # 从 matching_report 查询
    top = await tools.get_target_job(uid)
    if top and top.get("job_name"):
        return {"target_job": top["job_name"]}
    # 兜底：从已保存的学习计划中读取 target_job
    existing = await tools.get_learning_plan(uid)
    if existing and existing.get("target_job"):
        return {"target_job": existing["target_job"]}
    return {"target_job": ""}


async def retrieve_resources(state: LearningPlanState) -> Dict:
    """RAG: retrieve learning resources based on target job and skill gaps."""
    target_job = state.get("target_job", "")

    resources = learning_retriever.search(target_job, [], top_k=5)
    return {"resources": [
        {"title": r.title, "category": r.category, "level": r.level,
         "duration": r.duration, "source": r.source}
        for r in resources
    ]}


async def generate_plan(state: LearningPlanState) -> Dict:
    target = state.get("target_job", "")
    plan_type = state.get("plan_type", "长期")
    resources = state.get("resources", [])
    uid = state["user_id"]

    # 如果没有 target_job，直接返回已保存的计划，不要用空目标生成并覆盖
    if not target:
        existing = await tools.get_learning_plan(uid)
        if existing and existing.get("phases"):
            phases = existing["phases"]
            if isinstance(phases, str):
                try:
                    phases = json.loads(phases)
                except Exception:
                    phases = []
            return {"learning_plan": {
                "target_job": existing.get("target_job", ""),
                "plan_type": existing.get("plan_type", plan_type),
                "phases": phases,
            }}
        return {"learning_plan": {"phases": [], "total_duration": "", "error": "未找到目标岗位，请先完成人岗匹配"}}

    llm = get_llm(temperature=0.7)
    msg = llm.invoke([
        SystemMessage(content=prompts.PLAN_GENERATION_SYSTEM + "\n输出纯JSON。"),
        HumanMessage(content=prompts.PLAN_GENERATION_USER.format(
            current_skills="", target_job=target,
            resources=json.dumps(resources, ensure_ascii=False),
            plan_type=plan_type,
        )),
    ])
    try:
        plan = _parse_json(msg.content)
    except Exception:
        plan = {"phases": [], "total_duration": "", "error": "生成失败"}

    await tools.save_learning_plan(uid, target, plan_type, plan.get("phases", []))
    return {"learning_plan": plan}


async def generate_daily_tasks(state: LearningPlanState) -> Dict:
    uid = state["user_id"]
    target_job = state.get("target_job", "")

    # 优先使用 API 传入的计划（由 /daily-task 端点已确认正确性）
    existing = state.get("learning_plan")
    if not existing or not existing.get("phases"):
        existing = await tools.get_learning_plan(uid)

    if not existing or not existing.get("phases"):
        return {"daily_tasks": [], "error": "未找到学习计划"}

    # 确保 target_job 有值
    target_job = target_job or existing.get("target_job", "")
    print(f"[LearningPlan] generate_daily_tasks target_job: {target_job}")

    phases = existing["phases"]
    try:
        phases_data = json.loads(phases) if isinstance(phases, str) else phases
    except Exception:
        phases_data = phases

    if not isinstance(phases_data, list) or len(phases_data) == 0:
        return {"daily_tasks": [], "error": "学习计划阶段数据为空"}

    phase_index = state.get("phase_index", 0)
    if phase_index >= len(phases_data):
        phase_index = 0
    phase = phases_data[phase_index]

    llm = get_llm(temperature=0.4)
    phase_str = json.dumps(phase, ensure_ascii=False)

    # 最多重试2次
    tasks = []
    for attempt in range(2):
        try:
            msg = llm.invoke([
                SystemMessage(content=prompts.DAILY_TASK_SYSTEM),
                HumanMessage(content=prompts.DAILY_TASK_USER.format(
                    target_job=target_job,
                    phase=phase_str,
                )),
            ])
            raw = msg.content.strip()
            print(f"[LearningPlan] daily_tasks attempt {attempt+1}, raw: {raw[:300]}")

            # 提取JSON数组
            parsed = _parse_json(raw)
            if isinstance(parsed, dict):
                parsed = parsed.get("tasks", parsed.get("daily_tasks", []))
            if isinstance(parsed, list) and len(parsed) > 0:
                tasks = parsed
                break
        except Exception as e:
            print(f"[LearningPlan] daily_tasks attempt {attempt+1} error: {e}")

    if tasks:
        # 标准化任务格式
        normalized = []
        for i, t in enumerate(tasks):
            if isinstance(t, str):
                normalized.append({"title": t, "description": t, "duration": "30min", "difficulty": "中等"})
            elif isinstance(t, dict):
                normalized.append({
                    "title": t.get("title", t.get("content", f"任务{i+1}")),
                    "description": t.get("description", t.get("desc", "")),
                    "duration": t.get("duration", t.get("time", "30min")),
                    "difficulty": t.get("difficulty", "中等"),
                })
        tasks = normalized
        try:
            await tools.save_daily_tasks(uid, tasks, target_job)
        except Exception as e:
            print(f"[LearningPlan] save_daily_tasks error: {e}")

    return {"daily_tasks": tasks}


async def polish_plan(state: LearningPlanState) -> Dict:
    uid = state["user_id"]
    existing = await tools.get_learning_plan(uid)
    if not existing:
        return {"error": "未找到学习计划"}

    feedback = state.get("user_feedback", "")

    llm = get_llm(temperature=0.5)
    msg = llm.invoke([
        SystemMessage(content=prompts.PLAN_POLISH_SYSTEM + "\n输出纯JSON。"),
        HumanMessage(content=prompts.PLAN_POLISH_USER.format(
            plan=json.dumps(existing, ensure_ascii=False, default=str),
            feedback=feedback,
        )),
    ])
    try:
        new_plan = _parse_json(msg.content)
    except Exception:
        return {"error": "润色失败"}

    await tools.save_learning_plan(
        uid, existing.get("target_job", ""),
        existing.get("plan_type", "长期"),
        new_plan.get("phases", []),
    )
    return {"learning_plan": new_plan}


async def adjust_tasks(state: LearningPlanState) -> Dict:
    completed = state.get("completed_task_ids", [])
    remaining = state.get("remaining_tasks", [])

    llm = get_llm(temperature=0.3)
    msg = llm.invoke([
        SystemMessage(content=prompts.TASK_ADJUST_SYSTEM + "\n输出纯JSON数组。"),
        HumanMessage(content=prompts.TASK_ADJUST_USER.format(
            completed=json.dumps(completed, ensure_ascii=False),
            remaining=json.dumps(remaining, ensure_ascii=False),
        )),
    ])
    try:
        new_tasks = _parse_json(msg.content)
    except Exception:
        new_tasks = remaining

    uid = state["user_id"]
    await tools.save_daily_tasks(uid, new_tasks)
    return {"daily_tasks": new_tasks, "remaining_tasks": new_tasks}


async def export_plan(state: LearningPlanState) -> Dict:
    uid = state["user_id"]
    plan = await tools.get_learning_plan(uid)
    tasks = await tools.get_daily_tasks(uid)

    text = f"""# 学习计划

## 目标岗位
{plan.get('target_job', '未设定')}

## 计划类型
{plan.get('plan_type', '长期')}

## 学习阶段

"""
    phases = plan.get("phases", [])
    if isinstance(phases, str):
        try:
            phases = json.loads(phases)
        except Exception:
            phases = []

    for i, p in enumerate(phases, 1):
        if isinstance(p, dict):
            text += f"""### 阶段{i}: {p.get('phase_name', '')}
- **时长**: {p.get('duration', '')}
- **目标**: {', '.join(p.get('goals', []))}
- **内容**: {', '.join(p.get('content', []))}
"""

    if tasks:
        text += "\n## 每日任务\n"
        for t in tasks:
            text += f"- [{t.get('status', 'pending')}] {t.get('title', '')} ({t.get('duration', '')})\n"

    return {"export_text": text}


def _parse_json(content: str) -> dict | list:
    c = content.strip()
    # 移除markdown代码块标记
    for marker in ("```json", "```"):
        if marker in c:
            c = c.split(marker)[1].split("```")[0]
            break
    c = c.strip()
    # 尝试直接解析
    try:
        return json.loads(c)
    except json.JSONDecodeError:
        pass
    # 尝试提取JSON数组或对象
    for start_char, end_char in [('[', ']'), ('{', '}')]:
        start = c.find(start_char)
        end = c.rfind(end_char)
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(c[start:end+1])
            except json.JSONDecodeError:
                continue
    raise ValueError(f"无法解析JSON: {c[:200]}")
