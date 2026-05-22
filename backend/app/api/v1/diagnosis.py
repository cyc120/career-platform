from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, List, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from app.agents.llm_factory import get_llm
from app.middleware.auth import get_current_user

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
        "- 段落之间用空行分隔\n"
        "- 总字数300-400字\n"
        "\n"
        "【报告结构】\n"
        "第一段：总体画像概述（2-3句）\n"
        "- 一句话概括整体竞争力水平\n"
        "- 指出最突出的2-3个维度及其具体技能/成果\n"
        "\n"
        "第二段：优势维度分析\n"
        "- 列出分数最高的2-3个维度\n"
        "- 每个维度引用desc中的具体技能/成果关键词\n"
        "- 分析这些优势之间的关联性\n"
        "\n"
        "第三段：待提升维度分析\n"
        "- 列出分数最低或状态为待补充的维度\n"
        "- 指出具体缺失什么\n"
        "\n"
        "第四段：综合评价（2-3句）\n"
        "- 给出中肯的整体评价\n"
        "- 用积极但务实的语气"
    )

    USER_PROMPT = (
        f"以下是用户的七维能力画像数据：\n\n"
        f"{dim_text}\n\n"
        f"请基于以上数据撰写深度诊断报告。"
    )

    llm = get_llm(temperature=0.7, max_tokens=800)
    response = await llm.ainvoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=USER_PROMPT),
    ])

    # 清理可能的markdown符号残留
    report = response.content
    for char in ['#', '*', '`', '>']:
        report = report.replace(char, '')
    report = report.replace('\n\n\n', '\n\n').strip()

    return {"success": True, "report": report}
