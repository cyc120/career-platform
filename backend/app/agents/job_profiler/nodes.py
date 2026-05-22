"""LangGraph nodes for the Job Profiler agent."""

import json
from typing import Dict

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.llm_factory import get_llm
from app.agents.job_profiler.state import JobProfilerState
from app.agents.job_profiler.prompts import EXTRACT_REQUIREMENTS_PROMPT


DIMENSIONS = ["专业技能", "证书资质", "创新能力", "学习能力", "抗压能力", "沟通能力", "实习/项目经验"]


def _parse_json(content: str) -> dict:
    c = content.strip()
    for marker in ("```json", "```"):
        if marker in c:
            c = c.split(marker)[1].split("```")[0]
            break
    return json.loads(c)


def _clamp(val: float, lo: int = 10, hi: int = 100) -> int:
    return max(lo, min(hi, round(val / 5) * 5))


async def extract_requirements(state: JobProfilerState) -> Dict:
    """Extract structured 7-dimension requirements from job description."""
    job = state.get("job_info", {})
    job_title = job.get("job_title", "")
    company = job.get("company", "")
    job_desc = job.get("job_description", "")
    requirements = job.get("requirements", "")

    llm = get_llm(temperature=0.2, max_tokens=800)

    prompt = EXTRACT_REQUIREMENTS_PROMPT.format(
        job_title=job_title,
        company=company,
        job_description=job_desc or "暂无",
        requirements=requirements or "暂无",
    )

    try:
        response = await llm.ainvoke([
            SystemMessage(content="输出纯JSON，不要加任何前缀说明或markdown标记。"),
            HumanMessage(content=prompt),
        ])
        result = _parse_json(response.content)
    except Exception:
        result = {}

    # Normalize: ensure all 7 dimensions exist with valid scores
    normalized = {}
    for dim in DIMENSIONS:
        val = result.get(dim, {})
        if isinstance(val, dict):
            normalized[dim] = {
                "expected_score": _clamp(val.get("expected_score", 50)),
                "requirements": val.get("requirements", ""),
            }
        elif isinstance(val, (int, float)):
            normalized[dim] = {
                "expected_score": _clamp(val),
                "requirements": "",
            }
        else:
            normalized[dim] = {"expected_score": 50, "requirements": ""}

    return {"job_requirements": normalized}
