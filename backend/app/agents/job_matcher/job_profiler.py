"""Job Profiler — extracts structured 7-dimension requirements from job descriptions.

This is a sub-module of job_matcher, not an independent agent.
Includes in-memory cache and retry logic to replace the lost harness features.
"""

import asyncio
import hashlib
import json
from functools import lru_cache
from typing import Dict

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.llm_factory import get_llm

DIMENSIONS = ["专业技能", "证书资质", "创新能力", "学习能力", "抗压能力", "沟通能力", "实习/项目经验"]

EXTRACT_REQUIREMENTS_PROMPT = """你是一个岗位分析专家。请根据以下岗位信息，提取该岗位在7个维度上的能力要求。

岗位信息：
- 岗位名称：{job_title}
- 公司：{company}
- 岗位描述：{job_description}
- 任职要求：{requirements}

请分析岗位对以下7个维度的具体要求，给出每个维度的期望分数(0-100)和具体要求描述：

1. 专业技能 — 岗位要求的技术栈深度和广度（如：要求精通Python+Java+微服务则80+，仅要求了解基础编程则40-）
2. 证书资质 — 岗位对证书/认证的要求（无硬性要求则30分以下，明确要求则60+）
3. 创新能力 — 岗位对创新思维的要求（研发创新岗80+，执行岗40-）
4. 学习能力 — 岗位对学习新技术的要求（技术迭代快的领域70+，稳定领域50-）
5. 抗压能力 — 岗位的工作强度和压力（互联网大厂/高强度岗70+，轻松岗40-）
6. 沟通能力 — 岗位对团队协作的要求（需要跨部门/带团队80+，独立工作40-）
7. 实习/项目经验 — 岗位对实战经验的要求（要求2年以上经验70+，应届生岗40-）

输出纯JSON，格式如下：
{{
  "专业技能": {{"expected_score": 80, "requirements": "熟悉Python/Java，了解微服务架构，有分布式系统经验"}},
  "证书资质": {{"expected_score": 25, "requirements": "无硬性证书要求"}},
  "创新能力": {{"expected_score": 60, "requirements": "需要一定的技术创新能力"}},
  "学习能力": {{"expected_score": 75, "requirements": "技术栈更新快，需要持续学习"}},
  "抗压能力": {{"expected_score": 70, "requirements": "项目周期紧，需要较强的抗压能力"}},
  "沟通能力": {{"expected_score": 65, "requirements": "需要与产品、测试团队协作"}},
  "实习/项目经验": {{"expected_score": 55, "requirements": "有相关项目经验优先"}}
}}"""

# In-memory cache for job requirements (job_id -> requirements)
_requirements_cache: Dict[str, dict] = {}
MAX_CACHE_SIZE = 200


def _cache_key(job: dict) -> str:
    """Generate cache key from job info."""
    key_parts = [
        str(job.get("id", "")),
        job.get("job_title", ""),
        job.get("company", ""),
    ]
    raw = "|".join(key_parts)
    return hashlib.md5(raw.encode()).hexdigest()


def _parse_json(content: str) -> dict:
    c = content.strip()
    for marker in ("```json", "```"):
        if marker in c:
            c = c.split(marker)[1].split("```")[0]
            break
    return json.loads(c)


def _clamp(val: float, lo: int = 10, hi: int = 100) -> int:
    return max(lo, min(hi, round(val / 5) * 5))


def _normalize_result(result: dict) -> dict:
    """Ensure all 7 dimensions exist with valid scores."""
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
    return normalized


async def extract_job_requirements(job: dict, max_retries: int = 2) -> dict:
    """Extract structured 7-dimension requirements from job description.

    Features:
    - In-memory cache: same job_id won't call LLM twice
    - Retry with exponential backoff
    - Timeout protection (30s per attempt)
    """
    # Check cache first
    cache_key = _cache_key(job)
    if cache_key in _requirements_cache:
        return _requirements_cache[cache_key]

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

    # Retry logic with exponential backoff
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            response = await asyncio.wait_for(
                llm.ainvoke([
                    SystemMessage(content="输出纯JSON，不要加任何前缀说明或markdown标记。"),
                    HumanMessage(content=prompt),
                ]),
                timeout=30,
            )
            result = _parse_json(response.content)
            normalized = _normalize_result(result)

            # Cache the result
            if len(_requirements_cache) >= MAX_CACHE_SIZE:
                # Remove oldest entry (simple FIFO)
                oldest_key = next(iter(_requirements_cache))
                del _requirements_cache[oldest_key]
            _requirements_cache[cache_key] = normalized

            return normalized

        except asyncio.TimeoutError:
            last_error = "LLM timeout"
        except Exception as e:
            last_error = str(e)

        # Exponential backoff: 1s, 2s
        if attempt < max_retries:
            await asyncio.sleep(2 ** attempt)

    # All retries failed, return default
    print(f"[JobProfiler] Failed after {max_retries + 1} attempts: {last_error}")
    return _normalize_result({})
