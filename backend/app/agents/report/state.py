from typing import TypedDict


class ReportState(TypedDict, total=False):
    user_id: int
    action: str            # "generate" | "polish"
    user_profile: dict     # 画像数据 (radar_data, dimension_details, resume_text)
    selected_job: dict     # 锁定岗位 (job_title, scores, total_score, summary)
    match_results: dict    # 匹配结果 (ranked_results)
    learning_plan: dict    # 学习计划 (phases, target_job, total_duration)
    career_plan: dict      # 职业规划 (career_path, trends)
    report_text: str       # 生成的报告文本
    polish_feedback: str   # 用户润色指令
    polished_text: str     # 润色后文本
    error: str
