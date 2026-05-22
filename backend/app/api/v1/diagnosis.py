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
        "你是一位资深的职业分析师。请根据用户的七维能力画像数据，撰写一份300-400字的深度诊断报告。\n"
        "要求：\n"
        "1. 分析用户的优势维度和待提升维度\n"
        "2. 解读各维度之间的关联性和整体特征\n"
        "3. 仅做分析，不提建议\n"
        "4. 语言专业但易懂，段落清晰\n"
        "5. 纯文本输出，不要markdown符号"
    )

    USER_PROMPT = f"""以下是用户的七维能力画像数据：

{dim_text}

请基于以上数据，撰写一份300-400字的深度诊断报告。"""

    llm = get_llm(temperature=0.7, max_tokens=800)
    response = await llm.ainvoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=USER_PROMPT),
    ])

    return {"success": True, "report": response.content}
