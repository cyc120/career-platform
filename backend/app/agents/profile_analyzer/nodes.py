import json
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.llm_factory import get_llm
from app.agents.profile_analyzer.state import ProfileAnalyzerState
from app.agents.profile_analyzer.prompts import EXTRACT_INFO_PROMPT, SCORE_DIMENSIONS_PROMPT

# RadarChart维度顺序
DIMENSION_ORDER = ["专业技能", "创新能力", "学习能力", "实习能力", "抗压能力", "沟通能力", "证书"]

# EMA平滑系数 — 降低新分权重，减少波动
SMOOTH_ALPHA = 0.3
SCORE_THRESHOLD = 2

# ============================================================
# 维度关联推断 — 高分维度自动提升关联的低分维度
# ============================================================
# (来源维度, 目标维度, 提升比例, 提升上限) — 降低推断幅度，减少误差放大
CORRELATIONS = [
    ("实习能力", "专业技能", 0.15, 12),  # 实习→技能：实战提升技术
    ("实习能力", "抗压能力", 0.15, 12),  # 实习→抗压：职场deadline和多任务
    ("实习能力", "沟通能力", 0.10, 8),   # 实习→沟通：职场协作
    ("创新能力", "专业技能", 0.12, 10),  # 创新→技能：技术突破需要扎实基础
    ("创新能力", "学习能力", 0.12, 10),  # 创新→学习：探索新领域
    ("创新能力", "抗压能力", 0.15, 12),  # 创新→抗压：竞赛/论文/项目高压
    ("学习能力", "抗压能力", 0.10, 8),   # 学习→抗压：学业压力、持续学习
    ("沟通能力", "抗压能力", 0.08, 6),   # 沟通→抗压：团队协调有压力
    ("专业技能", "抗压能力", 0.08, 6),   # 技能→抗压：技术栈越多项目越多
]


def _apply_correlation_boosts(scores: dict) -> dict:
    """根据维度间的逻辑关联，对低分维度做合理提升。

    多个来源维度的提升可以累加（如实习+竞赛+学习共同提升抗压能力），
    总提升上限为最高来源分数的40%。
    """
    boosts = {}  # dim -> accumulated boost

    for src_dim, tgt_dim, ratio, cap in CORRELATIONS:
        src_score = scores.get(src_dim, {}).get("score", 0)
        tgt_score = scores.get(tgt_dim, {}).get("score", 0)
        if src_score > 20 and tgt_score < src_score:
            boost = min(int(src_score * ratio), cap)
            max_allowed = src_score - tgt_score
            actual_boost = min(boost, max(max_allowed, 0))
            if actual_boost > 0:
                # 累加各来源的提升（多维度共同影响）
                boosts[tgt_dim] = boosts.get(tgt_dim, 0) + actual_boost

    # 总提升上限：不超过当前最高来源分数的25%（降低以减少误差放大）
    for dim, total_boost in boosts.items():
        if dim in scores:
            max_src = max(
                (scores.get(s, {}).get("score", 0) for s, t, _, _ in CORRELATIONS if t == dim),
                default=0,
            )
            capped_boost = min(total_boost, int(max_src * 0.25))
            old_score = scores[dim]["score"]
            new_score = min(old_score + capped_boost, 100)
            # 归一化到最近的5
            scores[dim]["score"] = round(new_score / 5) * 5
            if scores[dim]["status"] != "已分析":
                scores[dim]["status"] = "已分析"
                scores[dim]["desc"] = "根据关联维度推断"

    return scores

# ============================================================
# 证书评分体系 — 按领域分组，同领域取最高，跨领域累加
# ============================================================
# 每个关键词 → (分数, 领域)
# 同一领域出现多个证书只取最高分（如 CET-4+CET-6 只计 CET-6）
# 不同领域的分数累加，总分上限100

CERT_TIERS = {
    # ---- 英语类 ----
    "CET-4": (15, "english"), "四级": (15, "english"), "英语四": (15, "english"),
    "CET-6": (30, "english"), "六级": (30, "english"), "英语六": (30, "english"),
    "雅思": (35, "english"), "IELTS": (35, "english"),
    "托福": (35, "english"), "TOEFL": (35, "english"),
    "托业": (30, "english"), "TOEIC": (30, "english"),

    # ---- 计算机等级考试 ----
    "计算机二级": (15, "ncre"), "NCRE": (15, "ncre"), "计算机等级": (15, "ncre"),
    "计算机三级": (25, "ncre"), "计算机四级": (30, "ncre"),

    # ---- 软考 (中国软件考试) ----
    "软件设计师": (35, "ruankao"), "网络工程师": (35, "ruankao"),
    "数据库工程师": (35, "ruankao"), "系统架构师": (50, "ruankao"),

    # ---- 云计算 ----
    "AWS": (40, "cloud"), "Azure": (35, "cloud"),
    "Google Cloud": (35, "cloud"), "GCP": (35, "cloud"),

    # ---- 网络认证 ----
    "HCIA": (25, "network"), "CCNA": (25, "network"),
    "HCIP": (40, "network"), "CCNP": (40, "network"),
    "HCIE": (55, "network"), "CCIE": (55, "network"),

    # ---- 安全认证 ----
    "CISSP": (55, "security"), "CISP": (50, "security"),

    # ---- Linux/容器 ----
    "RHCE": (40, "linux"), "红帽": (35, "linux"), "RHCA": (55, "linux"),
    "CKA": (40, "devops"), "Kubernetes": (30, "devops"),

    # ---- AI/ML ----
    "TensorFlow": (35, "ml"), "PyTorch": (35, "ml"),

    # ---- 项目管理 ----
    "PMP": (40, "pm"), "ACP": (35, "pm"),

    # ---- 竞赛 ----
    "ACM": (40, "competition"), "数学建模": (35, "competition"),
    "蓝桥杯": (20, "competition"), "天池": (30, "competition"),
    "Kaggle": (45, "competition"),

    # ---- 驾照 ----
    "C1": (10, "driving"), "C2": (10, "driving"), "驾照": (10, "driving"),

    # ---- 通用触发词 (不直接加分，仅用于检测) ----
    "证书": (0, ""), "认证": (0, ""), "资格证": (0, ""),
    "资格证书": (0, ""), "执照": (0, ""), "获奖": (0, ""),
    "奖项": (0, ""), "奖金": (0, ""), "金牌": (0, ""),
    "银牌": (0, ""), "铜牌": (0, ""),
}

# 通用触发词列表（用于检测是否有证书相关对话，但不直接产生分数）
CERT_TRIGGERS = {"证书", "认证", "资格证", "资格证书", "执照", "获奖", "奖项", "奖金", "金牌", "银牌", "铜牌"}


def _score_certificates(chat_text: str) -> tuple[int, list[str]]:
    """扫描用户文本，按领域分组计算证书分数。

    逻辑：
    1. 找到所有匹配的证书关键词
    2. 按领域分组，每个领域只取最高分的一个证书
    3. 不同领域的分数累加
    4. 总分上限100

    Returns:
        (total_score, found_cert_names)
    """
    found = {}  # keyword -> (score, domain)
    for kw, (score, domain) in CERT_TIERS.items():
        if kw in chat_text and domain:  # domain为空的是触发词，跳过
            found[kw] = (score, domain)

    if not found:
        has_trigger = any(kw in chat_text for kw in CERT_TRIGGERS)
        if has_trigger:
            return 30, ["（未明确具体证书名称）"]
        return 0, []

    # 按领域分组，每组取最高分
    domain_best = {}  # domain -> (best_score, best_keyword)
    for kw, (score, domain) in found.items():
        if domain not in domain_best or score > domain_best[domain][0]:
            domain_best[domain] = (score, kw)

    total = sum(s for s, _ in domain_best.values())
    total = min(total, 100)

    cert_names = [kw for _, kw in domain_best.values()]
    return total, cert_names


def _build_cert_desc(score: int, cert_names: list[str]) -> str:
    """根据分数和证书名称生成描述。"""
    if not cert_names:
        return "暂无相关信息"
    if score >= 80:
        return "、".join(cert_names) + "，含金量高"
    if score >= 50:
        return "、".join(cert_names) + "，资质扎实"
    if score >= 25:
        return "、".join(cert_names) + "，有基础资质"
    return "、".join(cert_names)


# 证书相关的通用关键词（用于防幻觉判断）
CERT_KEYWORDS = list(CERT_TIERS.keys())


async def extract_info(state: ProfileAnalyzerState) -> dict:
    chat_history = state.get("chat_history", [])
    if not chat_history:
        return {"extracted_info": "暂无对话信息"}

    history_text = "\n".join(
        f"{'用户' if m.get('role') == 'user' else 'AI'}: {m.get('content', '')}"
        for m in chat_history
    )

    # 关键词扫描（只扫描用户消息，避免AI回复中的证书推荐被误识别）
    user_text = " ".join(m.get("content", "") for m in chat_history if m.get("role") == "user")
    found_certs = [kw for kw in CERT_KEYWORDS if kw in user_text]
    cert_hint = ""
    if found_certs:
        cert_hint = f"\n\n【关键词扫描发现】对话中出现了以下证书/资质相关关键词：{', '.join(found_certs)}"

    llm = get_llm(temperature=0.3, max_tokens=800)
    response = await llm.ainvoke([
        SystemMessage(content="你是一个信息提取助手，直接输出提取结果。"),
        HumanMessage(content=EXTRACT_INFO_PROMPT.format(chat_history=history_text) + cert_hint),
    ])

    return {"extracted_info": response.content + cert_hint}


async def score_dimensions(state: ProfileAnalyzerState) -> dict:
    extracted_info = state.get("extracted_info", "暂无信息")
    previous_details = state.get("previous_details", {})

    if previous_details:
        prev_lines = []
        for dim in DIMENSION_ORDER:
            d = previous_details.get(dim, {})
            prev_lines.append(f"  {dim}: {d.get('score', 0)}分 ({d.get('status', '待补充')}) — {d.get('desc', '暂无')}")
        previous_scores = "\n".join(prev_lines)
    else:
        previous_scores = "（首次评估，无历史分数）"

    llm = get_llm(temperature=0, max_tokens=1000)
    response = await llm.ainvoke([
        SystemMessage(content="输出纯JSON，不要加任何前缀说明。"),
        HumanMessage(content=SCORE_DIMENSIONS_PROMPT.format(
            extracted_info=extracted_info,
            previous_scores=previous_scores,
        )),
    ])

    try:
        scores = _parse_json(response.content)
    except Exception:
        scores = {}

    # 证书维度由算法评分，丢弃LLM可能臆造的证书分数
    scores.pop("证书", None)

    # 分数归一化：四舍五入到最近的5，确保一致性
    for dim in scores:
        if isinstance(scores[dim], dict) and "score" in scores[dim]:
            raw_score = scores[dim]["score"]
            if isinstance(raw_score, (int, float)) and raw_score > 0:
                scores[dim]["score"] = round(raw_score / 5) * 5

    return {"dimension_scores": scores}


async def format_output(state: ProfileAnalyzerState) -> dict:
    scores = state.get("dimension_scores", {})
    previous_radar = state.get("previous_radar_data", [])
    previous_details = state.get("previous_details", {})
    chat_history = state.get("chat_history", [])

    # 证书维度：完全由关键词+等级评分决定，不依赖LLM
    # 只扫描用户消息，避免AI回复中提到的证书被误算
    user_text = " ".join(m.get("content", "") for m in chat_history if m.get("role") == "user")
    cert_score, cert_names = _score_certificates(user_text)

    # 维度关联推断：高分维度自动提升关联的低分维度
    scores = _apply_correlation_boosts(dict(scores))

    radar_data = []
    dimension_details = {}

    for i, dim in enumerate(DIMENSION_ORDER):
        if dim == "证书":
            # 证书维度：用算法评分替代LLM评分
            old_cert = previous_details.get("证书", {})
            if cert_names:
                # 有新证书证据 → 与旧分取较高者（新发现证书不应降低分数）
                old_score = old_cert.get("score", 0)
                final_score = max(cert_score, old_score)
                final_desc = _build_cert_desc(final_score, cert_names) if cert_score >= old_score else old_cert.get("desc", "")
                final_status = "已分析"
            elif old_cert.get("score", 0) > 0:
                # 无新证据但之前有 → 保持
                final_score = old_cert["score"]
                final_status = old_cert.get("status", "已分析")
                final_desc = old_cert.get("desc", "")
            else:
                # 从未提过 → 归零
                final_score = 0
                final_status = "待补充"
                final_desc = "暂无相关信息"
        else:
            # 其他6个维度：原有LLM评分 + EMA平滑逻辑
            info = scores.get(dim, {"score": 0, "status": "待补充", "desc": "暂无信息"})
            new_score = info.get("score", 0)
            new_status = info.get("status", "待补充")
            new_desc = info.get("desc", "暂无信息")

            old_score = previous_radar[i] if i < len(previous_radar) else 0
            old_detail = previous_details.get(dim, {})
            old_desc = old_detail.get("desc", "")

            if old_score > 0:
                blended = int(new_score * SMOOTH_ALPHA + old_score * (1 - SMOOTH_ALPHA))
                # 归一化到最近的5
                blended = round(blended / 5) * 5
                if abs(blended - old_score) < SCORE_THRESHOLD:
                    final_score = old_score
                else:
                    final_score = blended
            else:
                # 归一化到最近的5
                final_score = round(new_score / 5) * 5

            if new_status == "已分析" or old_detail.get("status") == "已分析":
                final_status = "已分析"
            else:
                final_status = "待补充"

            final_desc = new_desc if (new_desc and new_desc != "暂无相关信息" and new_desc != "解析失败") else (old_desc or "暂无信息")

        radar_data.append(final_score)
        dimension_details[dim] = {
            "score": final_score,
            "status": final_status,
            "desc": final_desc,
            "type": "success" if final_status == "已分析" else "info",
        }

    return {"radar_data": radar_data, "dimension_details": dimension_details}


def _parse_json(content: str) -> dict:
    c = content.strip()
    for marker in ("```json", "```"):
        if marker in c:
            c = c.split(marker)[1].split("```")[0]
            break
    return json.loads(c)
