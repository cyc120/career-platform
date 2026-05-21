from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from app.agents.harness import harness
from app.agents.learning_plan import tools
from app.agents.llm_factory import get_llm
from app.middleware.auth import get_current_user

router = APIRouter()


class GenerateRequest(BaseModel):
    plan_type: str = "长期"


class PolishRequest(BaseModel):
    user_feedback: str


class DailyTasksRequest(BaseModel):
    phase_index: int = 0


class AdjustRequest(BaseModel):
    completed_task_ids: List[int] = []
    remaining_tasks: List[dict] = []


class TaskUpdateRequest(BaseModel):
    status: str


class CoachRequest(BaseModel):
    message: str
    history: List[dict] = []  # [{role: "user"|"assistant", content: str}]
    previous_radar_data: List[int] = []
    previous_details: Optional[dict] = None


@router.post("/generate")
async def generate_plan(req: GenerateRequest, user: dict = Depends(get_current_user)):
    result = await harness.run(
        "learning_plan",
        {"user_id": user["user_id"], "action": "generate", "plan_type": req.plan_type},
        user_id=user["user_id"],
    )
    return result


@router.post("/polish")
async def polish_plan(req: PolishRequest, user: dict = Depends(get_current_user)):
    result = await harness.run(
        "learning_plan",
        {"user_id": user["user_id"], "action": "polish", "user_feedback": req.user_feedback},
        user_id=user["user_id"],
    )
    return result


@router.post("/daily-tasks")
async def generate_daily_tasks(req: DailyTasksRequest, user: dict = Depends(get_current_user)):
    result = await harness.run(
        "learning_plan",
        {"user_id": user["user_id"], "action": "daily_tasks", "phase_index": req.phase_index},
        user_id=user["user_id"],
    )
    return result


@router.post("/adjust")
async def adjust_tasks(req: AdjustRequest, user: dict = Depends(get_current_user)):
    result = await harness.run(
        "learning_plan",
        {
            "user_id": user["user_id"],
            "action": "adjust",
            "completed_task_ids": req.completed_task_ids,
            "remaining_tasks": req.remaining_tasks,
        },
        user_id=user["user_id"],
    )
    return result


@router.post("/export")
async def export_plan(user: dict = Depends(get_current_user)):
    result = await harness.run(
        "learning_plan",
        {"user_id": user["user_id"], "action": "export"},
        user_id=user["user_id"],
    )
    return result


@router.post("/coach")
async def career_coach(req: CoachRequest, user: dict = Depends(get_current_user)):
    """Real-time AI career coaching chat with profile analysis."""
    # Build dimension gap info from previous_details to guide the coach
    prev_details = req.previous_details or {}
    DIM_ORDER = ["专业技能", "创新能力", "学习能力", "实习能力", "抗压能力", "沟通能力", "证书"]
    filled = [d for d in DIM_ORDER if prev_details.get(d, {}).get("status") == "已分析"]
    gaps = [d for d in DIM_ORDER if d not in filled]
    gap_hint = ""
    if gaps:
        gap_hint = f"用户尚未提供：{'、'.join(gaps)}。请在回复末尾用一句话自然地引导用户补充其中一项。"
    else:
        gap_hint = "用户画像已较完善，可以给出总结性建议或深度追问。"

    COACH_SYSTEM_PROMPT = (
        "你是「职途无限」AI职业教练，专注于计算机/IT方向求职辅导。"
        "你熟悉的技术栈包括：前后端开发、算法、大数据、人工智能、网络安全、运维等方向。\n"
        "规则：\n"
        "1. 回复不超过80字，禁止markdown符号，纯文本\n"
        "2. 先回应用户内容，再自然追问，不列点\n"
        "3. 每次只追问一个方向，优先补充画像缺口\n"
        f"4. {gap_hint}\n"
        "5. 提问要具体到技术方向，比如：你用过什么框架？参加过ACM吗？有实习经历吗？\n"
        "6. 语气像学长聊天，简短直接"
    )

    llm = get_llm(temperature=0.7, max_tokens=200)

    messages = [SystemMessage(content=COACH_SYSTEM_PROMPT)]
    for h in req.history[-10:]:
        role = h.get("role", "user")
        content = h.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))

    messages.append(HumanMessage(content=req.message))

    response = await llm.ainvoke(messages)
    reply = response.content

    # Build full chat history including the new reply for profile analysis
    full_history = list(req.history) + [
        {"role": "user", "content": req.message},
        {"role": "assistant", "content": reply},
    ]

    # Run profile analyzer agent via harness
    radar_data = [0, 0, 0, 0, 0, 0, 0]
    dimension_details = {}
    try:
        result = await harness.run(
            "profile_analyzer",
            {
                "chat_history": full_history,
                "previous_radar_data": req.previous_radar_data,
                "previous_details": req.previous_details or {},
            },
            user_id=user["user_id"],
        )
        if result.get("success") and result.get("data"):
            radar_data = result["data"].get("radar_data", radar_data)
            dimension_details = result["data"].get("dimension_details", dimension_details)
    except Exception:
        pass

    return {
        "reply": reply,
        "radar_data": radar_data,
        "dimension_details": dimension_details,
    }


@router.get("/tasks")
async def get_tasks(user: dict = Depends(get_current_user)):
    tasks = await tools.get_daily_tasks(user["user_id"])
    return {"success": True, "tasks": tasks}


@router.put("/tasks/{task_id}")
async def update_task(task_id: int, req: TaskUpdateRequest, user: dict = Depends(get_current_user)):
    await tools.update_task_status(task_id, req.status)
    return {"success": True}


@router.post("/tasks/{task_id}/complete")
async def complete_task(task_id: int, user: dict = Depends(get_current_user)):
    await tools.update_task_status(task_id, "completed")
    return {"success": True}
