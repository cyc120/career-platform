from typing import TypedDict


class ProfileAnalyzerState(TypedDict, total=False):
    chat_history: list[dict]
    previous_radar_data: list[int]
    previous_details: dict
    extracted_info: str
    dimension_scores: dict
    radar_data: list[int]
    dimension_details: dict
    error: str
