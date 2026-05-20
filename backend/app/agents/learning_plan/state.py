from typing import TypedDict, List, Dict


class LearningPlanState(TypedDict, total=False):
    user_id: int
    action: str  # generate, polish, daily_tasks, adjust, export
    plan_type: str  # 长期, 短期
    target_job: str
    user_feedback: str
    phase_index: int
    completed_task_ids: list[int]
    remaining_tasks: list[dict]

    # Generated outputs
    learning_plan: dict
    daily_tasks: list[dict]
    export_text: str
    resources: list[dict]
    error: str
