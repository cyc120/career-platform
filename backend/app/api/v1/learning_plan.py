import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from app.agents.harness import harness
from app.agents.learning_plan import tools
from app.agents.learning_plan.profile_analyzer import analyze_profile
from app.agents.learning_plan.task_planner import generate_daily_tasks as planner_generate
from app.agents.llm_factory import get_llm
from app.agents.job_matcher.db_utils import save_user_profile
from app.middleware.auth import get_current_user


DIM_ORDER = ["专业技能", "创新能力", "学习能力", "实习能力", "抗压能力", "沟通能力", "证书"]


def _build_save_profile(radar_data: list, dimension_details: dict, chat_history: list) -> dict:
    """将画像分析结果构建为 job_matcher 可用的 user_profile 格式。"""
    # 提取用户对话文本作为简历摘要
    resume_text = "\n".join(
        m.get("content", "") for m in chat_history if m.get("role") == "user"
    )
    # 从 dimension_details 提取各维度描述
    dim_desc = {}
    for i, dim in enumerate(DIM_ORDER):
        detail = dimension_details.get(dim, {})
        dim_desc[dim] = {
            "score": radar_data[i] if i < len(radar_data) else 0,
            "status": detail.get("status", "待补充"),
            "desc": detail.get("desc", ""),
        }
    return {
        "resume_text": resume_text,
        "radar_data": radar_data,
        "dimension_details": dim_desc,
        "source": "chat_coach",
    }

router = APIRouter()


class GenerateRequest(BaseModel):
    plan_type: str = "长期"


class PolishRequest(BaseModel):
    user_feedback: str


class DailyTasksRequest(BaseModel):
    phase_index: int = 0
    force_refresh: bool = False


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


class ParseFileRequest(BaseModel):
    filename: str
    base64: str


@router.post("/parse-file")
async def parse_file(req: ParseFileRequest, user: dict = Depends(get_current_user)):
    """Parse uploaded file (PDF/DOC) and extract text content."""
    import base64
    import io
    ext = req.filename.rsplit('.', 1)[-1].lower() if '.' in req.filename else ''

    try:
        file_bytes = base64.b64decode(req.base64)
    except Exception:
        raise HTTPException(400, "Invalid base64 data")

    if ext == 'pdf':
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                # 简历通常只需前5页，跳过后续页面加快解析
                pages = []
                for i, page in enumerate(pdf.pages[:5]):
                    pages.append(page.extract_text() or '')
            return {"success": True, "text": "\n".join(pages)}
        except ImportError:
            raise HTTPException(500, "pdfplumber not installed")
        except Exception as e:
            raise HTTPException(400, f"PDF 解析失败: {str(e)}")

    if ext == 'doc':
        return {"success": False, "error": "暂不支持 .doc 格式，请转换为 .docx 后重新上传"}

    return {"success": False, "error": f"不支持的格式: .{ext}"}


@router.post("/generate")
async def generate_plan(req: GenerateRequest, user: dict = Depends(get_current_user)):
    from app.agents.job_matcher.db_utils import get_selected_job
    from app.agents.learning_plan import prompts as lp_prompts

    uid = user["user_id"]
    selected = await get_selected_job(uid)
    target_job = selected.get("job_title", "") if selected else ""

    # 优先从数据库读取已保存的计划
    existing = await tools.get_learning_plan(uid)
    existing_job = existing.get("target_job", "") if existing else ""

    if existing and existing.get("phases") and (not target_job or existing_job == target_job):
        phases = existing["phases"]
        if isinstance(phases, str):
            try:
                phases = json.loads(phases)
            except Exception:
                phases = []
        return {
            "success": True,
            "learning_plan": {
                "target_job": existing.get("target_job", ""),
                "plan_type": existing.get("plan_type", "长期"),
                "phases": phases,
            },
        }

    # 直接调 LLM 生成
    llm = get_llm(temperature=0.7)
    msg = await llm.ainvoke([
        SystemMessage(content=lp_prompts.PLAN_GENERATION_SYSTEM + "\n输出纯JSON。"),
        HumanMessage(content=lp_prompts.PLAN_GENERATION_USER.format(
            current_skills="", target_job=target_job,
            resources="[]", plan_type=req.plan_type,
        )),
    ])
    try:
        raw = msg.content.strip()
        for marker in ("```json", "```"):
            if marker in raw:
                raw = raw.split(marker)[1].split("```")[0]
                break
        plan = json.loads(raw.strip())
    except Exception:
        plan = {"phases": []}

    if plan.get("phases"):
        await tools.save_learning_plan(uid, target_job, req.plan_type, plan["phases"])

    if not plan or not plan.get("phases"):
        if existing and existing.get("phases"):
            phases = existing["phases"]
            if isinstance(phases, str):
                try:
                    phases = json.loads(phases)
                except Exception:
                    phases = []
            plan = {"target_job": existing_job, "plan_type": "长期", "phases": phases}

    return {"success": True, "learning_plan": plan}


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
    from app.agents.job_matcher.db_utils import get_selected_job, get_user_profile
    from app.agents.learning_plan import prompts as lp_prompts
    import json as _json

    uid = user["user_id"]
    selected = await get_selected_job(uid)
    target_job = selected.get("job_title", "") if selected else ""
    print(f"[API] daily-tasks user_id={uid}, target_job='{target_job}', selected={selected is not None}")

    # 没有锁定岗位时直接返回空，避免用空 target_job 生成无效任务
    if not target_job:
        return {"success": False, "daily_tasks": [], "target_job": "", "error": "请先在人岗匹配中锁定一个岗位"}

    # 1. 检查已有任务是否匹配当前锁定岗位
    existing_tasks = await tools.get_daily_tasks(uid)
    if existing_tasks and not req.force_refresh:
        task_target = existing_tasks[0].get("target_job", "") if existing_tasks else ""
        print(f"[API] daily-tasks: existing tasks target='{task_target}', count={len(existing_tasks)}")
        if target_job and task_target == target_job:
            print(f"[API] daily-tasks returning cached tasks for '{target_job}'")
            return {"success": True, "daily_tasks": existing_tasks, "target_job": target_job, "cached": True}
        print(f"[API] daily-tasks: target mismatch (task='{task_target}' vs job='{target_job}'), regenerating")

    # 2. 从 DB 读取学习计划
    plan = await tools.get_learning_plan(uid)
    plan_job = plan.get("target_job", "") if plan else ""
    print(f"[API] daily-tasks: plan from DB target_job='{plan_job}', has_phases={bool(plan and plan.get('phases'))}")

    # 3. 计划不存在或目标岗位不匹配 → 直接调 LLM 生成计划
    if not plan or not plan.get("phases") or (target_job and plan_job != target_job):
        print(f"[API] daily-tasks: generating plan for '{target_job}' via LLM...")
        llm = get_llm(temperature=0.7)
        msg = await llm.ainvoke([
            SystemMessage(content=lp_prompts.PLAN_GENERATION_SYSTEM + "\n输出纯JSON。"),
            HumanMessage(content=lp_prompts.PLAN_GENERATION_USER.format(
                current_skills="", target_job=target_job,
                resources="[]", plan_type="长期",
            )),
        ])
        try:
            raw = msg.content.strip()
            for marker in ("```json", "```"):
                if marker in raw:
                    raw = raw.split(marker)[1].split("```")[0]
                    break
            plan_data = _json.loads(raw.strip())
        except Exception as e:
            print(f"[API] daily-tasks: plan LLM parse error: {e}")
            plan_data = {"phases": []}

        phases_list = plan_data.get("phases", [])
        if phases_list:
            await tools.save_learning_plan(uid, target_job, "长期", phases_list)
            plan = {"target_job": target_job, "phases": phases_list}
            print(f"[API] daily-tasks: plan saved with {len(phases_list)} phases for '{target_job}'")
        else:
            return {"success": False, "daily_tasks": [], "target_job": target_job, "error": "学习计划生成失败"}

    # 4. 提取 phases
    phases = plan.get("phases", [])
    if isinstance(phases, str):
        try:
            phases = _json.loads(phases)
        except Exception:
            pass

    if not phases:
        return {"success": False, "daily_tasks": [], "target_job": target_job, "error": "学习计划阶段为空"}

    # 5. 加载用户画像，融合到任务生成
    profile_record = await get_user_profile(uid)
    user_profile = profile_record.get("profile_data") if profile_record else None
    if isinstance(user_profile, str):
        try:
            user_profile = _json.loads(user_profile)
        except Exception:
            user_profile = None

    # 6. 多步流水线生成任务
    phase = phases[req.phase_index] if req.phase_index < len(phases) else phases[0]
    tasks = await planner_generate(phase, target_job, user_profile=user_profile)

    if tasks:
        await tools.save_daily_tasks(uid, tasks, target_job)
        print(f"[API] daily-tasks saved {len(tasks)} tasks for '{target_job}'")

    return {"success": True, "daily_tasks": tasks, "target_job": target_job}


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

    # Run profile analyzer (sub-module)
    radar_data = [0, 0, 0, 0, 0, 0, 0]
    dimension_details = {}
    try:
        result = await analyze_profile(
            chat_history=full_history,
            previous_radar_data=req.previous_radar_data,
            previous_details=req.previous_details or {},
        )
        radar_data = result.get("radar_data", radar_data)
        dimension_details = result.get("dimension_details", dimension_details)
    except Exception:
        pass

    # 持久化画像到 user_profiles 表，供 job_matcher 等智能体使用
    if any(v > 0 for v in radar_data):
        try:
            profile_for_save = _build_save_profile(radar_data, dimension_details, full_history)
            await save_user_profile(user["user_id"], profile_for_save)
        except Exception:
            pass

    return {
        "reply": reply,
        "radar_data": radar_data,
        "dimension_details": dimension_details,
    }


@router.post("/coach/stream")
async def coach_stream(req: CoachRequest, user: dict = Depends(get_current_user)):
    """Streaming SSE endpoint for career coaching chat."""
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

    async def event_stream():
        full_reply = ""

        # Stream LLM tokens
        async for chunk in llm.astream(messages):
            token = chunk.content
            if token:
                full_reply += token
                yield f"data: {json.dumps({'type': 'token', 'content': token}, ensure_ascii=False)}\n\n"

        # Run profile analyzer (sub-module) after stream completes
        full_history = list(req.history) + [
            {"role": "user", "content": req.message},
            {"role": "assistant", "content": full_reply},
        ]
        radar_data = [0, 0, 0, 0, 0, 0, 0]
        dimension_details = {}
        try:
            result = await analyze_profile(
                chat_history=full_history,
                previous_radar_data=req.previous_radar_data,
                previous_details=req.previous_details or {},
            )
            radar_data = result.get("radar_data", radar_data)
            dimension_details = result.get("dimension_details", dimension_details)
        except Exception as e:
            import traceback
            print(f"[Coach] Profile analyzer error: {e}")
            traceback.print_exc()

        # 持久化画像到 user_profiles 表，供 job_matcher 等智能体使用
        if any(v > 0 for v in radar_data):
            try:
                profile_for_save = _build_save_profile(radar_data, dimension_details, full_history)
                await save_user_profile(user["user_id"], profile_for_save)
            except Exception as e:
                print(f"[Coach] Save profile failed: {e}")

        radar_payload = json.dumps({'type': 'radar', 'radar_data': radar_data, 'dimension_details': dimension_details}, ensure_ascii=False)
        print(f"[Coach] Sending radar event: {radar_payload[:200]}")
        yield f"data: {radar_payload}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


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
