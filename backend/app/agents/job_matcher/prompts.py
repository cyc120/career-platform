# ---- Weight Determination Prompt ----

WEIGHT_PROMPT = """你是一个岗位匹配专家。请根据岗位信息，确定以下7个维度在匹配中的权重：

岗位信息：{job_info}

7个维度：
1. 专业技能 — 与岗位技术栈的匹配程度
2. 证书资质 — 行业认证和资格
3. 创新能力 — 创新能力匹配
4. 学习能力 — 学习新技术栈的能力
5. 抗压能力 — 工作强度适应性
6. 沟通能力 — 团队协作匹配
7. 实习/项目经验 — 实战经验匹配

输出JSON，7个权重值（0-1之间，总和为1）：
{{"专业技能": 0.35, "证书资质": 0.05, ...}}"""

# ---- Match Scoring Prompt ----

MATCH_PROMPT = """你是一个岗位匹配评估员。请评估用户画像与岗位需求的匹配程度。

用户画像：
{user_profile}

岗位需求：
{job_requirement}

维度权重：
{weights}

对每个维度进行0-100评分，并给出匹配差距分析。
输出JSON格式：
{{
  "scores": {{
    "专业技能": {{"score": 85, "gap": "需要补充XX技术"}},
    ...
  }},
  "total_score": 加权总分(0-100),
  "summary": "一句话总结匹配度",
  "recommendations": ["改进建议1", "改进建议2"]
}}"""

# ---- Merge Prompt ----

MERGE_PROMPT = """合并两个匹配评估结果：

MySQL详情匹配：{detail_result}
Neo4j画像匹配：{profile_result}

取各维度评分的平均值，综合生成最终匹配报告。输出JSON格式。"""
