"""Profile Analyzer — extracts 7-dimension capability scores from chat history.

This is a sub-module used by the learning_plan API, not an independent agent.
Includes retry logic and timeout protection.
"""

import json
from typing import Dict, Any

from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.retry import llm_call_with_retry

# RadarChart维度顺序
DIMENSION_ORDER = ["专业技能", "创新能力", "学习能力", "实习能力", "抗压能力", "沟通能力", "证书"]

# EMA平滑系数 — 降低新分权重，减少波动
SMOOTH_ALPHA = 0.3
SCORE_THRESHOLD = 2

# ============================================================
# 维度关联推断 — 高分维度自动提升关联的低分维度
# ============================================================
# (来源维度, 目标维度, 提升比例, 提升上限)
CORRELATIONS = [
    # 实习能力 → 其他维度（实战经验的辐射效应）
    ("实习能力", "专业技能", 0.18, 15),  # 实习→技能：实战提升技术
    ("实习能力", "抗压能力", 0.30, 25),  # 实习→抗压：职场deadline和多任务
    ("实习能力", "沟通能力", 0.12, 10),  # 实习→沟通：职场协作
    ("实习能力", "创新能力", 0.12, 10),  # 实习→创新：项目实践中产生创新
    ("实习能力", "学习能力", 0.10, 8),   # 实习→学习：项目驱动的快速学习

    # 创新能力 → 其他维度
    ("创新能力", "专业技能", 0.12, 10),  # 创新→技能：技术突破需要扎实基础
    ("创新能力", "学习能力", 0.15, 12),  # 创新→学习：探索新领域
    ("创新能力", "抗压能力", 0.28, 22),  # 创新→抗压：竞赛/论文/项目高压
    ("创新能力", "实习能力", 0.10, 8),   # 创新→实习：竞赛/开源项目等同实战

    # 学习能力 → 其他维度
    ("学习能力", "抗压能力", 0.20, 18),  # 学习→抗压：学业压力、持续学习

    # 沟通能力 → 抗压能力
    ("沟通能力", "抗压能力", 0.18, 15),  # 沟通→抗压：团队协调有压力

    # 专业技能 → 抗压能力
    ("专业技能", "抗压能力", 0.18, 15),  # 技能→抗压：技术栈越多项目越多
]

# ============================================================
# 基准分兜底 — 根据提取信息中的关键词确保最低分数
# ============================================================
_TECH_KEYWORDS = {"python", "java", "c++", "javascript", "go", "rust", "typescript",
                  "django", "flask", "spring", "react", "vue", "angular", "node",
                  "mysql", "redis", "mongodb", "postgresql", "docker", "kubernetes",
                  "linux", "git", "html", "css", "sql", "nosql", "nginx", "aws",
                  "编程", "开发", "技术栈", "框架", "数据库", "服务器", "前端", "后端",
                  "算法", "数据结构", "操作系统", "计算机网络", "计算机"}
_SCHOOL_KEYWORDS = {"大学", "学院", "本科", "硕士", "博士", "在读", "学生", "毕业",
                    "学校", "高校", "985", "211", "双一流", "专业", "计算机系"}
_PROJECT_KEYWORDS = {"项目", "课设", "课程设计", "毕设", "毕业设计", "实习", "兼职",
                     "开发了", "做了", "实现了", "搭建了", "独立完成", "负责"}
_TEAM_KEYWORDS = {"团队", "小组", "合作", "协作", "组长", "队长", "带领", "组织",
                  "汇报", "演讲", "答辩", "助教", "社团", "学生会"}

EXTRACT_INFO_PROMPT = """你是一个简历信息提取专家。请从以下对话历史中提取与用户职业能力相关的关键信息。

对话历史：
{chat_history}

请按以下7个维度逐一提取信息，每个维度单独列出：

1. 【专业技能】编程语言、框架、工具、技术栈（如 Python、Java、Spring Boot、MySQL、Docker 等）
   注意：提到学校课程（如数据结构、操作系统、计算机网络）也属于专业技能基础
2. 【证书资质】必须仔细查找以下内容：
   - 职业资格：软件设计师、系统架构师、PMP、网络工程师、数据库工程师
   - 云计算/AI认证：AWS认证、Azure认证、Google Cloud、TensorFlow认证
   - 语言证书：CET-4、CET-6、雅思、托福、托业
   - 其他认证：计算机等级考试(NCRE)、华为认证、思科认证、红帽认证
   - 竞赛获奖证书：ACM、数学建模、蓝桥杯、Kaggle
   注意：用户提到的任何"证书"、"认证"、"资格证"、"通过了XX考试"、"拿了XX证"都算
3. 【创新经历】项目创新、技术突破、竞赛获奖、开源贡献、独立开发的项目
4. 【学习能力】自学经历、GPA、学历、新技术掌握速度、在校成绩、掌握的技术数量
5. 【抗压经历】高压环境、紧迫项目、通宵赶工、多任务并行、课程繁重、实习压力
6. 【沟通协作】团队合作、汇报演讲、带团队、当助教、组织活动、小组作业组长
7. 【实习/项目经验】实习经历、项目经验、工作内容、课程设计、毕业设计、个人项目

【重要】提取规则：
- 即使信息不完整，也要尽量从间接证据中提取。例如用户说"我是计算机专业的"，应推断出有编程基础和学业压力。
- 用户提到的任何技术、项目、经历都要记录，不要遗漏。
- 如果某个维度完全没有提及，输出"未提及"。
直接输出提取结果，每个维度用【维度名】开头。"""


SCORE_DIMENSIONS_PROMPT = """你是一个职业能力评估专家。请基于用户信息对以下6个维度进行评分。
（证书维度已由系统自动评分，你不需要评分）

【核心要求】相同输入必须产生相同输出！严格按照评分标准中的固定分数档打分，不要使用中间值。

用户信息：
{extracted_info}

当前已有评分（必须参考，只做微调）：
{previous_scores}

【严格评分标准】每个维度只能从以下固定分数中选择，不要使用其他数值：

专业技能（0-100）：
- 0分：无任何技术信息
- 35分：提到1-2个基础技术（如Python、HTML）
- 50分：掌握2-3个技术栈
- 65分：掌握3-5个技术栈，有项目应用
- 75分：熟练掌握主流技术栈，有实际项目经验
- 85分：精通多种技术，有架构设计经验
- 95分+：完全匹配岗位技术栈，且有深度经验

创新能力（0-100）：
- 0分：无相关信息
- 40分：有课程项目或小创新
- 55分：有完整项目开发经历
- 65分：有竞赛参与经历或开源贡献
- 75分：有获奖经历或技术突破
- 90分+：顶级竞赛获奖或重大创新成果

学习能力（0-100）：
- 0分：无相关信息
- 40分：提到在校学习或自学某技术
- 55分：有自学经历，掌握多项技术
- 70分：GPA优秀或快速掌握新技术
- 85分：名校背景或突出学业表现
- 95分+：跨领域学习、多项技能突出

实习能力（0-100）：
- 0分：无实习/项目经验
- 40分：有课程项目或简单实践
- 55分：有完整项目经历（课设、毕设、开源项目）
- 65分：有1段实习或竞赛项目经验
- 75分：有2段实习或知名公司经验
- 85分：有多段实习或大厂经验
- 95分+：丰富大厂实习经验

抗压能力（0-100）：
- 0分：无相关信息
- 40分：有基本学业压力应对（如课程繁忙）
- 55分：有多任务或deadline经验
- 65分：有项目赶工、竞赛备赛等经历
- 75分：有高强度项目经历或实习中的压力应对
- 85分：有高压环境成功案例（如大厂实习、创业、重大竞赛）
- 95分+：极端高压环境下的卓越表现

沟通能力（0-100）：
- 0分：无相关信息
- 40分：有基本团队合作或小组作业
- 55分：有团队协作或汇报经验
- 65分：有带团队或组织活动经验
- 75分：有演讲、领导或跨部门协作经验
- 85分+：有公开演讲、大型活动组织经验

【评分规则】
1. 有直接证据：严格按上述标准评分
2. 可合理推断：在标准基础上±5分微调（宁可偏高不要偏低）
3. 完全无信息且无法推断：保持0分，status标为"待补充"
4. 已有评分且无新信息：保持当前分数不变
5. 已有评分且有新信息：调整幅度不超过±15分
6. desc字段要求：用逗号分隔列出该维度的具体关键词/成果，不要写概括性套话。
   - 专业技能：列出具体技术名（如"Python,Django,MySQL,Docker"）
   - 创新能力：列出具体成果（如"论文发表,数学建模国赛"）
   - 学习能力：列出具体依据（如"GPA3.8,自学机器学习"）
   - 实习能力：列出具体项目/实习（如"字节跳动实习,电商系统项目"）
   - 抗压能力：列出具体经历（如"3天完成毕设答辩,多门考试并行"）
   - 沟通能力：列出具体经历（如"小组组长,技术分享汇报"）

【推断指导】
- 用户是计算机相关专业 → 专业技能至少35分，学习能力至少40分
- 用户提到任何技术/编程语言 → 专业技能至少50分
- 用户提到学校/在读 → 学习能力至少40分，抗压能力至少40分
- 用户提到任何项目/课设 → 实习能力至少40分，抗压能力至少40分
- 用户提到团队/小组 → 沟通能力至少40分

输出严格的JSON格式，不要加任何前缀说明：
{{
  "专业技能": {{"score": 65, "status": "已分析", "desc": "Python,Django,MySQL,Redis"}},
  "创新能力": {{"score": 40, "status": "已分析", "desc": "课程项目开发,开源贡献"}},
  "学习能力": {{"score": 55, "status": "已分析", "desc": "自学Docker,GPA3.5"}},
  "实习能力": {{"score": 55, "status": "已分析", "desc": "电商系统课设,毕设项目"}},
  "抗压能力": {{"score": 40, "status": "已分析", "desc": "多门考试并行,项目赶工"}},
  "沟通能力": {{"score": 40, "status": "待补充", "desc": "暂无相关信息"}}
}}"""


# ============================================================
# 证书评分体系 — 按领域分组，同领域取最高，跨领域累加
# ============================================================
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

CERT_TRIGGERS = {"证书", "认证", "资格证", "资格证书", "执照", "获奖", "奖项", "奖金", "金牌", "银牌", "铜牌"}
CERT_KEYWORDS = list(CERT_TIERS.keys())


def _detect_baselines(info_lower: str, info_raw: str) -> dict:
    """根据提取信息中的关键词，返回各维度的最低保障分数。"""
    baselines = {}

    tech_hits = sum(1 for kw in _TECH_KEYWORDS if kw in info_lower)
    if tech_hits >= 3:
        baselines["专业技能"] = 65
    elif tech_hits >= 1:
        baselines["专业技能"] = 50

    if any(kw in info_raw for kw in _SCHOOL_KEYWORDS):
        baselines["学习能力"] = 55

    if any(kw in info_raw for kw in _PROJECT_KEYWORDS):
        baselines["实习能力"] = 55

    if any(kw in info_raw for kw in _PROJECT_KEYWORDS):
        baselines["创新能力"] = 40

    if any(kw in info_raw for kw in _TEAM_KEYWORDS):
        baselines["沟通能力"] = 55

    if any(kw in info_raw for kw in _SCHOOL_KEYWORDS) or any(kw in info_raw for kw in _PROJECT_KEYWORDS):
        baselines["抗压能力"] = 40

    return baselines


def _apply_correlation_boosts(scores: dict) -> dict:
    """根据维度间的逻辑关联，对低分维度做合理提升。"""
    boosts = {}

    for src_dim, tgt_dim, ratio, cap in CORRELATIONS:
        src_score = scores.get(src_dim, {}).get("score", 0)
        tgt_score = scores.get(tgt_dim, {}).get("score", 0)
        if src_score > 15 and tgt_score < src_score * 1.2:
            boost = min(int(src_score * ratio), cap)
            max_allowed = int(src_score * 0.9) - tgt_score
            actual_boost = min(boost, max(max_allowed, 0))
            if actual_boost > 0:
                boosts[tgt_dim] = boosts.get(tgt_dim, 0) + actual_boost

    for dim, total_boost in boosts.items():
        if dim in scores:
            max_src = max(
                (scores.get(s, {}).get("score", 0) for s, t, _, _ in CORRELATIONS if t == dim),
                default=0,
            )
            capped_boost = min(total_boost, int(max_src * 0.40))
            old_score = scores[dim]["score"]
            new_score = min(old_score + capped_boost, 100)
            scores[dim]["score"] = round(new_score / 5) * 5
            if scores[dim]["status"] != "已分析":
                scores[dim]["status"] = "已分析"
                scores[dim]["desc"] = "根据关联维度推断"

    return scores


def _score_certificates(chat_text: str) -> tuple[int, list[str]]:
    """扫描用户文本，按领域分组计算证书分数。"""
    found = {}
    for kw, (score, domain) in CERT_TIERS.items():
        if kw in chat_text and domain:
            found[kw] = (score, domain)

    if not found:
        has_trigger = any(kw in chat_text for kw in CERT_TRIGGERS)
        if has_trigger:
            return 30, ["（未明确具体证书名称）"]
        return 0, []

    domain_best = {}
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


def _parse_json(content: str) -> dict:
    c = content.strip()
    for marker in ("```json", "```"):
        if marker in c:
            c = c.split(marker)[1].split("```")[0]
            break
    return json.loads(c)


async def _llm_with_retry(messages: list, temperature: float = 0, max_tokens: int = 1000, max_retries: int = 2, timeout: int = 30) -> str:
    """Call LLM with retry and timeout protection (delegates to common utility)."""
    return await llm_call_with_retry(
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        max_retries=max_retries,
        timeout=timeout,
    )


async def analyze_profile(
    chat_history: list[dict],
    previous_radar_data: list[int] = None,
    previous_details: dict = None,
) -> Dict[str, Any]:
    """Analyze chat history and extract 7-dimension capability scores.

    This is the core logic extracted from the former profile_analyzer agent.
    Includes retry logic and timeout protection.
    """
    if previous_radar_data is None:
        previous_radar_data = []
    if previous_details is None:
        previous_details = {}

    # Step 1: Extract info from chat history
    if not chat_history:
        extracted_info = "暂无对话信息"
    else:
        history_text = "\n".join(
            f"{'用户' if m.get('role') == 'user' else 'AI'}: {m.get('content', '')}"
            for m in chat_history
        )

        user_text = " ".join(m.get("content", "") for m in chat_history if m.get("role") == "user")
        found_certs = [kw for kw in CERT_KEYWORDS if kw in user_text]
        cert_hint = ""
        if found_certs:
            cert_hint = f"\n\n【关键词扫描发现】对话中出现了以下证书/资质相关关键词：{', '.join(found_certs)}"

        response_content = await _llm_with_retry(
            messages=[
                SystemMessage(content="你是一个信息提取助手，直接输出提取结果。"),
                HumanMessage(content=EXTRACT_INFO_PROMPT.format(chat_history=history_text) + cert_hint),
            ],
            temperature=0.3,
            max_tokens=800,
        )
        extracted_info = response_content + cert_hint

    # Step 2: Score dimensions
    if previous_details:
        prev_lines = []
        for dim in DIMENSION_ORDER:
            d = previous_details.get(dim, {})
            prev_lines.append(f"  {dim}: {d.get('score', 0)}分 ({d.get('status', '待补充')}) — {d.get('desc', '暂无')}")
        previous_scores = "\n".join(prev_lines)
    else:
        previous_scores = "（首次评估，无历史分数）"

    response_content = await _llm_with_retry(
        messages=[
            SystemMessage(content="输出纯JSON，不要加任何前缀说明。"),
            HumanMessage(content=SCORE_DIMENSIONS_PROMPT.format(
                extracted_info=extracted_info,
                previous_scores=previous_scores,
            )),
        ],
        temperature=0,
        max_tokens=1000,
    )

    try:
        scores = _parse_json(response_content)
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

    # 基准分兜底
    info_lower = extracted_info.lower() if extracted_info else ""
    baselines = _detect_baselines(info_lower, extracted_info or "")
    for dim, min_score in baselines.items():
        cur = scores.get(dim, {}).get("score", 0)
        if 0 < cur < min_score:
            scores[dim]["score"] = min_score

    # Step 3: Format output
    user_text = " ".join(m.get("content", "") for m in chat_history if m.get("role") == "user")
    cert_score, cert_names = _score_certificates(user_text)

    # 维度关联推断
    scores = _apply_correlation_boosts(dict(scores))

    radar_data = []
    dimension_details = {}

    for i, dim in enumerate(DIMENSION_ORDER):
        if dim == "证书":
            old_cert = previous_details.get("证书", {})
            if cert_names:
                old_score = old_cert.get("score", 0)
                final_score = max(cert_score, old_score)
                final_desc = _build_cert_desc(final_score, cert_names) if cert_score >= old_score else old_cert.get("desc", "")
                final_status = "已分析"
            elif old_cert.get("score", 0) > 0:
                final_score = old_cert["score"]
                final_status = old_cert.get("status", "已分析")
                final_desc = old_cert.get("desc", "")
            else:
                final_score = 0
                final_status = "待补充"
                final_desc = "暂无相关信息"
        else:
            info = scores.get(dim, {"score": 0, "status": "待补充", "desc": "暂无信息"})
            new_score = info.get("score", 0)
            new_status = info.get("status", "待补充")
            new_desc = info.get("desc", "暂无信息")

            old_score = previous_radar_data[i] if i < len(previous_radar_data) else 0
            old_detail = previous_details.get(dim, {})
            old_desc = old_detail.get("desc", "")

            if old_score > 0:
                blended = int(new_score * SMOOTH_ALPHA + old_score * (1 - SMOOTH_ALPHA))
                blended = round(blended / 5) * 5
                if abs(blended - old_score) < SCORE_THRESHOLD:
                    final_score = old_score
                else:
                    final_score = blended
            else:
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

    return {
        "radar_data": radar_data,
        "dimension_details": dimension_details,
    }
