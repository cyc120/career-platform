import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from app.agents.llm_factory import get_llm
from app.middleware.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

DIM_NAMES = ["专业技能", "创新能力", "学习能力", "实习能力", "抗压能力", "沟通能力", "证书"]


class DiagnosisRequest(BaseModel):
    radar_data: List[int] = [0, 0, 0, 0, 0, 0, 0]
    dimension_details: Optional[Dict] = None


@router.post("/generate")
async def generate_diagnosis(req: DiagnosisRequest, user: dict = Depends(get_current_user)):
    """Generate a 300-400 word AI diagnosis report based on profile analysis."""
    details = req.dimension_details or {}
    radar = req.radar_data

    # Build dimension summary for the prompt
    dim_summary = []
    for i, name in enumerate(DIM_NAMES):
        score = details.get(name, {}).get("score", radar[i] if i < len(radar) else 0)
        status = details.get(name, {}).get("status", "待采集")
        desc = details.get(name, {}).get("desc", "")
        dim_summary.append(f"- {name}: 评分{score}/100, 状态={status}, 描述={desc}")

    dim_text = "\n".join(dim_summary)

    SYSTEM_PROMPT = (
        "你是一位资深的职业分析师。请根据用户的七维能力画像数据，撰写一份深度诊断报告。\n"
        "\n"
        "【输出格式要求】\n"
        "- 纯文本，不要任何markdown符号（不要#、*、-、>等）\n"
        "- 不要编号，不要项目符号\n"
        "- 段落之间用两个换行符分隔（即空一行）\n"
        "- 每段至少3-4句话，内容饱满连贯，不要拆成短句\n"
        "- 总字数300-400字\n"
        "\n"
        "【报告结构 — 严格分为3段】\n"
        "第一段：画像总览与优势分析\n"
        "- 一句话概括整体竞争力水平\n"
        "- 重点分析分数最高的2-3个维度，引用具体技能和成果\n"
        "- 分析这些优势之间的关联性\n"
        "\n"
        "第二段：待提升维度与成长建议\n"
        "- 指出分数最低或待补充的维度，说明具体缺失什么\n"
        "- 结合目标岗位需求，给出2-3条可操作的提升建议\n"
        "\n"
        "第三段：综合评价与展望\n"
        "- 给出中肯的整体评价\n"
        "- 用积极但务实的语气总结发展前景"
    )

    USER_PROMPT = (
        f"以下是用户的七维能力画像数据：\n\n"
        f"{dim_text}\n\n"
        f"请基于以上数据撰写深度诊断报告。"
    )

    llm = get_llm(temperature=0.7, max_tokens=800)
    try:
        response = await asyncio.wait_for(
            llm.ainvoke([
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=USER_PROMPT),
            ]),
            timeout=60,
        )
    except asyncio.TimeoutError:
        logger.warning("[Diagnosis] LLM call timed out (60s)")
        raise HTTPException(504, "AI诊断生成超时，请稍后重试")
    except Exception as e:
        logger.warning(f"[Diagnosis] LLM call failed: {e}")
        raise HTTPException(502, "AI诊断服务暂时不可用")

    # 清理可能的markdown符号残留
    report = response.content
    for char in ['#', '*', '`', '>']:
        report = report.replace(char, '')
    report = report.replace('\n\n\n', '\n\n').strip()

    return {"success": True, "report": report}
