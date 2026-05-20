from typing import TypedDict, List, Dict


class CareerPlannerState(TypedDict, total=False):
    user_id: int
    user_profile: dict
    top_job: dict
    trends: dict
    promotion_data: list[dict]
    career_path: dict
    chart_path: str
    plan_id: int
