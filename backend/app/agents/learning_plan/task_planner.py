"""
两步 LLM 任务规划器 — 融合用户画像，保证永远不返回空任务列表。

Step 1: 一次调用：分析用户能力 + 提取技能领域 + 生成个性化任务
Step 2: 审核去重补全（可选）

每步独立降级，最终兜底从 phase 数据直接生成任务。
"""

import asyncio
import json

from langchain_core.messages import SystemMessage, HumanMessage

from app.agents.llm_factory import get_llm

# ────────────────────── Prompts ──────────────────────

TASK_GENERATE_SYSTEM = """你是一个个性化学习任务规划师。你需要根据用户的个人能力画像和目标岗位，生成切实可行的学习任务。

输出严格的JSON格式：
{{
  "skill_areas": ["技能领域1", "技能领域2", ...],
  "tasks": [
    {{"title": "任务标题", "description": "具体步骤说明，结合用户现有能力说明如何提升", "duration": "30min", "difficulty": "简单", "area": "所属技能领域"}},
    ...
  ]
}}

规则：
1. 先分析用户的能力雷达图和各维度描述，识别强项和弱项
2. 优先针对弱项（低分维度）生成提升任务，强项维度生成进阶任务
3. 每个任务必须具体可执行，包含明确的学习动作和资源建议
4. description中说明：(1)该任务针对用户哪个弱项 (2)对目标岗位的价值
5. duration格式：数字+min（30min/45min/60min/90min），根据任务难度合理设定
6. difficulty只能是：简单、中等、困难
7. 总任务数控制在6-10个
8. 输出纯JSON，不要有任何其他文字"""

TASK_GENERATE_USER = """目标岗位：{target_job}

学习阶段：{phase_name}
阶段目标：{goals}
阶段内容：{content}

=== 用户能力画像 ===
能力雷达图（满分100）：
{radar_summary}

各维度详情：
{dimension_summary}

用户背景摘要：
{resume_summary}

请结合用户现有能力水平，生成针对该学习阶段的个性化任务。"""

TASK_REVIEW_SYSTEM = """你是一个学习任务质量审核员。请检查以下任务列表，确保质量和个性化程度。

规则：
1. 如果任务列表质量良好、无明显问题，直接原样输出
2. 如发现重复任务，合并为一个
3. 如发现某个任务与用户已有能力重叠（用户已掌握），替换为进阶任务
4. 如发现缺少对弱项维度的覆盖，补充1-2个针对性任务
5. 总任务数保持在5-10个
6. 输出格式同输入格式（JSON数组）
7. 输出纯JSON数组，不要有任何其他文字"""

TASK_REVIEW_USER = """目标岗位：{target_job}
学习阶段：{phase_name}

用户能力概况：{radar_summary}

当前任务列表：
{tasks_json}

请审核并输出最终任务列表。"""

# ────────────────────── Helpers ──────────────────────

DIM_NAMES = ["专业技能", "创新能力", "学习能力", "实习能力", "抗压能力", "沟通能力", "证书"]


def _parse_json(content: str):
    """去 markdown 围栏后解析 JSON。"""
    c = content.strip()
    for marker in ("```json", "```"):
        if marker in c:
            c = c.split(marker)[1].split("```")[0]
            break
    return json.loads(c.strip())


async def _llm_call(
    messages: list,
    temperature: float = 0.4,
    max_tokens: int = 2500,
    timeout: int = 60,
) -> str | None:
    """单次 LLM 调用，带超时保护。失败返回 None。"""
    try:
        llm = get_llm(temperature=temperature, max_tokens=max_tokens)
        resp = await asyncio.wait_for(llm.ainvoke(messages), timeout=timeout)
        return resp.content
    except Exception as e:
        print(f"[task_planner] LLM call failed: {e}")
        return None


def _build_profile_context(profile: dict | None) -> dict:
    """从用户画像中提取结构化上下文，供 prompt 使用。"""
    if not profile:
        return {
            "radar_summary": "暂无能力数据",
            "dimension_summary": "暂无维度详情",
            "resume_summary": "暂无用户背景信息",
        }

    # 雷达图摘要
    radar = profile.get("radar_data", [])
    if radar and len(radar) >= 7:
        lines = []
        for i, name in enumerate(DIM_NAMES):
            score = radar[i] if i < len(radar) else 0
            level = "强" if score >= 80 else "中等" if score >= 60 else "弱"
            lines.append(f"  - {name}: {score}分 ({level})")
        radar_summary = "\n".join(lines)
    else:
        radar_summary = "暂无能力数据"

    # 维度详情摘要
    details = profile.get("dimension_details", {})
    if details:
        lines = []
        for name, info in details.items():
            if isinstance(info, dict):
                score = info.get("score", 0)
                desc = info.get("desc", "")
                status = info.get("status", "")
                if desc:
                    lines.append(f"  - {name}({score}分, {status}): {desc}")
                else:
                    lines.append(f"  - {name}({score}分, {status})")
        dimension_summary = "\n".join(lines) if lines else "暂无维度详情"
    else:
        dimension_summary = "暂无维度详情"

    # 用户背景摘要（取前500字）
    resume = profile.get("resume_text", "")
    resume_summary = resume[:500] + "..." if len(resume) > 500 else resume
    if not resume_summary:
        resume_summary = "暂无用户背景信息"

    return {
        "radar_summary": radar_summary,
        "dimension_summary": dimension_summary,
        "resume_summary": resume_summary,
    }


def _normalize_tasks(tasks: list) -> list[dict]:
    """统一任务格式。"""
    normalized = []
    for i, t in enumerate(tasks):
        if isinstance(t, str):
            normalized.append({
                "title": t,
                "description": t,
                "duration": "30min",
                "difficulty": "中等",
            })
        elif isinstance(t, dict):
            normalized.append({
                "title": t.get("title", f"任务{i + 1}"),
                "description": t.get("description", t.get("desc", "")),
                "duration": t.get("duration", t.get("time", "30min")),
                "difficulty": t.get("difficulty", "中等"),
            })
    return normalized


def _fallback_from_phase(phase: dict, target_job: str) -> list[dict]:
    """无 LLM 兜底：从阶段 goals/content 直接生成任务。"""
    tasks = []
    items = phase.get("goals", []) + phase.get("content", [])
    for i, item in enumerate(items[:8]):
        title = item if len(item) < 30 else item[:28] + "..."
        tasks.append({
            "title": title,
            "description": f"针对{target_job}岗位需求，{item}",
            "duration": "45min",
            "difficulty": "中等",
        })
    if not tasks:
        tasks.append({
            "title": f"学习{phase.get('phase_name', '相关知识')}",
            "description": f"系统学习{target_job}岗位所需的核心知识",
            "duration": "60min",
            "difficulty": "中等",
        })
    return tasks


# ────────────────────── Pipeline Steps ──────────────────────


async def _generate_tasks(
    phase: dict, target_job: str, profile_ctx: dict,
) -> list[dict] | None:
    """Step 1：融合用户画像，一次调用生成个性化任务。"""
    phase_name = phase.get("phase_name", "")
    goals = "；".join(phase.get("goals", []))
    content = "；".join(phase.get("content", []))

    raw = await _llm_call(
        [
            SystemMessage(content=TASK_GENERATE_SYSTEM),
            HumanMessage(content=TASK_GENERATE_USER.format(
                target_job=target_job,
                phase_name=phase_name,
                goals=goals or "无",
                content=content or "无",
                radar_summary=profile_ctx["radar_summary"],
                dimension_summary=profile_ctx["dimension_summary"],
                resume_summary=profile_ctx["resume_summary"],
            )),
        ],
        temperature=0.5,
        max_tokens=3000,
    )
    if not raw:
        return None

    try:
        data = _parse_json(raw)
        if isinstance(data, dict):
            tasks = data.get("tasks", [])
        elif isinstance(data, list):
            tasks = data
        else:
            return None
        return tasks if tasks else None
    except Exception as e:
        print(f"[task_planner] Step 1 parse error: {e}")
        return None


async def _review_and_refine(
    tasks: list[dict], phase: dict, target_job: str, profile_ctx: dict,
) -> list[dict] | None:
    """Step 2：审核去重补全。失败返回 None（跳过）。"""
    phase_name = phase.get("phase_name", "")
    tasks_json = json.dumps(tasks, ensure_ascii=False)

    raw = await _llm_call(
        [
            SystemMessage(content=TASK_REVIEW_SYSTEM),
            HumanMessage(content=TASK_REVIEW_USER.format(
                target_job=target_job,
                phase_name=phase_name,
                radar_summary=profile_ctx["radar_summary"],
                tasks_json=tasks_json,
            )),
        ],
        temperature=0.3,
    )
    if raw:
        try:
            parsed = _parse_json(raw)
            if isinstance(parsed, dict):
                parsed = parsed.get("tasks", [])
            if isinstance(parsed, list) and parsed:
                return parsed
        except Exception as e:
            print(f"[task_planner] Step 2 parse error: {e}")

    return None


# ────────────────────── Entry Point ──────────────────────


async def generate_daily_tasks(
    phase: dict,
    target_job: str,
    user_profile: dict | None = None,
) -> list[dict]:
    """两步流水线生成每日任务，融合用户画像，保证永远不返回空列表。"""
    # 构建用户画像上下文
    profile_ctx = _build_profile_context(user_profile)
    print(f"[task_planner] profile loaded: radar={bool(user_profile and user_profile.get('radar_data'))}, "
          f"details={bool(user_profile and user_profile.get('dimension_details'))}")

    # Step 1：融合画像生成任务
    raw_tasks = await _generate_tasks(phase, target_job, profile_ctx)
    if not raw_tasks:
        print("[task_planner] Step 1 fallback: using phase data directly")
        return _normalize_tasks(_fallback_from_phase(phase, target_job))

    # Step 2：审核（best-effort，失败跳过）
    refined = await _review_and_refine(raw_tasks, phase, target_job, profile_ctx)
    final = refined if refined else raw_tasks
    print(f"[task_planner] generated {len(final)} tasks with profile context")
    return _normalize_tasks(final)
