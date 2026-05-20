from typing import TypedDict, List, Dict


class ResumeAnalyzerState(TypedDict, total=False):
    # Input
    input_text: str
    file_path: str
    image_path: str

    # Extraction phase
    extracted_text: str
    file_text: str
    ocr_content: str
    merged_text: str
    user_profile: dict
    completeness_flags: dict
    missing_fields: list[str]
    next_question: str
    supplement_text: str
    supplement_count: int

    # Analysis phase
    skill_analysis: dict
    competitiveness: dict
    report: str
