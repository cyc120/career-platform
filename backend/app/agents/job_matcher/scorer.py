"""Profile-vs-Profile matching scorer.

Compares user radar_data against LLM-extracted job requirements
to compute 7-dimension match scores.
"""
from typing import Dict, List


# 7 dimensions aligned with frontend DIM_NAMES
DIMENSIONS = ["专业技能", "证书资质", "创新能力", "学习能力", "抗压能力", "沟通能力", "实习/项目经验"]

# Map frontend dimension names to user_profile dimension_details keys
PROFILE_DIM_MAP = {
    "专业技能": "专业技能",
    "证书资质": "证书",
    "创新能力": "创新能力",
    "学习能力": "学习能力",
    "抗压能力": "抗压能力",
    "沟通能力": "沟通能力",
    "实习/项目经验": "实习能力",
}

# Radar data index order (matches profile_analyzer output)
RADAR_INDEX = {
    "专业技能": 0,
    "创新能力": 1,
    "学习能力": 2,
    "实习/项目经验": 3,
    "抗压能力": 4,
    "沟通能力": 5,
    "证书资质": 6,
}

# Dimension weights for total score
DIM_WEIGHTS = {
    "专业技能": 0.30,
    "实习/项目经验": 0.20,
    "学习能力": 0.12,
    "创新能力": 0.10,
    "沟通能力": 0.10,
    "证书资质": 0.10,
    "抗压能力": 0.08,
}


class MatchScorer:
    """Profile-vs-Profile matching scorer.

    Compares user profile (radar_data + dimension_details) against
    job requirements (from job_profiler agent) to compute match scores.
    """

    def compute_scores(
        self, user_profile: dict, job_requirements: dict, job_info: dict = None
    ) -> dict:
        """Compute 7-dimension match scores.

        Args:
            user_profile: User profile with radar_data and dimension_details
            job_requirements: 7-dimension job requirements from job_profiler
                {"专业技能": {"expected_score": 80, "requirements": "..."}, ...}
            job_info: Optional job metadata (job_title, company, etc.)

        Returns:
            dict with total_score, scores (per-dimension), summary, recommendations
        """
        radar_data = user_profile.get("radar_data", [0] * 7)
        dim_details = user_profile.get("dimension_details", {})
        job_info = job_info or {}

        dim_scores = {}
        for dim in DIMENSIONS:
            # Get user score
            profile_key = PROFILE_DIM_MAP.get(dim, dim)
            radar_idx = RADAR_INDEX.get(dim, 0)
            user_score = 0
            if radar_idx < len(radar_data):
                user_score = radar_data[radar_idx] or 0
            detail = dim_details.get(profile_key, {})
            if detail.get("score"):
                user_score = max(user_score, detail["score"])

            # Get job expected score
            job_req = job_requirements.get(dim, {})
            if isinstance(job_req, dict):
                job_expected = job_req.get("expected_score", 50)
                job_desc = job_req.get("requirements", "")
            elif isinstance(job_req, (int, float)):
                job_expected = int(job_req)
                job_desc = ""
            else:
                job_expected = 50
                job_desc = ""

            # Compute match score
            score, gap = self._compute_dim_match(dim, user_score, job_expected, job_desc)
            dim_scores[dim] = {"score": round(score), "gap": gap}

        total = self._compute_weighted_total(dim_scores)
        summary = self._generate_summary(total, dim_scores, job_info, user_profile)
        recommendations = self._generate_recommendations(dim_scores)

        return {
            "total_score": round(total, 1),
            "scores": dim_scores,
            "summary": summary,
            "recommendations": recommendations,
        }

    def _compute_dim_match(
        self, dim: str, user_score: int, job_expected: int, job_desc: str
    ) -> tuple:
        """Compute match score for a single dimension.

        Logic:
        - user >= job_expected: score = 100 - diff * 0.3 (exceeds requirement, small penalty)
        - user < job_expected:  score = 100 - diff * 1.0 (below requirement, full penalty)
        - Floor at 20 (even poor matches get some score)
        """
        diff = abs(user_score - job_expected)

        if user_score >= job_expected:
            score = 100 - diff * 0.3
        else:
            score = 100 - diff * 1.0

        score = max(20, min(100, score))

        # Generate gap text
        gap = ""
        if user_score < job_expected:
            gap = f"需提升至{job_expected}+（当前{user_score}）"
            if job_desc:
                gap += f"：{job_desc}"
        elif diff > 20:
            gap = f"超出岗位要求（岗位期望{job_expected}）"

        return score, gap

    def _compute_weighted_total(self, dim_scores: Dict[str, dict]) -> float:
        """Compute weighted total score across all dimensions."""
        total = 0.0
        for dim, weight in DIM_WEIGHTS.items():
            score_data = dim_scores.get(dim, {})
            score = score_data.get("score", 0) if isinstance(score_data, dict) else 0
            total += score * weight
        return total

    def _generate_summary(self, total: float, dim_scores: dict, job_info: dict, user_profile: dict) -> str:
        """Generate a specific ~80 char match summary referencing actual strengths/weaknesses."""
        job_title = job_info.get("job_title", "目标岗位")
        dim_details = user_profile.get("dimension_details", {})

        # Sort dims by score
        sorted_dims = sorted(
            dim_scores.items(),
            key=lambda x: x[1].get("score", 0) if isinstance(x[1], dict) else 0,
            reverse=True,
        )
        strong1 = sorted_dims[0][0] if sorted_dims else ""
        strong2 = sorted_dims[1][0] if len(sorted_dims) > 1 else ""
        weak_dim = sorted_dims[-1][0] if sorted_dims else ""
        weak_score = sorted_dims[-1][1].get("score", 0) if sorted_dims else 0

        # Get user's actual skill keywords
        skill_desc = dim_details.get("专业技能", {}).get("desc", "")
        skills = [s.strip() for s in skill_desc.split(",") if s.strip()] if skill_desc else []
        skill_text = "、".join(skills[:3]) if skills else ""

        # Get project/internship keywords
        exp_desc = dim_details.get("实习能力", {}).get("desc", "")
        exps = [s.strip() for s in exp_desc.split(",") if s.strip()] if exp_desc else []

        if total >= 85:
            base = f"综合{round(total)}分，与{job_title}高度契合"
            if skill_text:
                base += f"。{skill_text}等技术栈匹配度高"
            if exps:
                base += f"，{exps[0]}等经历加分"
            base += f"，{strong1}和{strong2}是核心优势"
        elif total >= 70:
            base = f"综合{round(total)}分，与{job_title}较为匹配"
            if skill_text:
                base += f"。具备{skill_text}基础"
            base += f"，{strong1}表现好，但{weak_dim}({weak_score})需提升"
        else:
            base = f"综合{round(total)}分，与{job_title}存在一定差距"
            if skill_text:
                base += f"。虽有{skill_text}基础"
            base += f"，{weak_dim}仅{weak_score}分，需重点补强"

        return base

    def _generate_recommendations(self, dim_scores: dict) -> List[str]:
        """Generate improvement recommendations based on lowest scores and gaps."""
        recs = []
        sorted_dims = sorted(
            dim_scores.items(),
            key=lambda x: x[1].get("score", 0) if isinstance(x[1], dict) else 0,
        )
        for dim, data in sorted_dims[:3]:
            score = data.get("score", 0) if isinstance(data, dict) else 0
            gap = data.get("gap", "") if isinstance(data, dict) else ""
            if score < 70 and gap:
                recs.append(gap)
            elif score < 60:
                recs.append(f"{dim}方面需要重点提升")

        if not recs:
            recs.append("整体匹配度不错，可以继续保持当前的学习节奏")

        return recs[:4]
