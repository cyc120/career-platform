from typing import TypedDict, List, Dict


class JobMatcherState(TypedDict, total=False):
    user_id: int
    user_profile: dict
    candidate_job_ids: list[str]
    job_details: list[dict]
    neo4j_profiles: list[dict]
    match_results: list[dict]
    ranked_results: list[dict]
    report_id: int
