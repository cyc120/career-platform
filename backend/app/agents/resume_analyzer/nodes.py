"""LangGraph nodes for the Resume Analyzer agent."""

import json
import os
from typing import Dict

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.llm_factory import get_llm
from app.agents.resume_analyzer.state import ResumeAnalyzerState
from app.agents.resume_analyzer.prompts import (
    INTEGRATE_PROMPT,
    EXTRACT_PROMPT,
    QUESTION_PROMPT,
    ANALYZE_PROMPT,
    GENERATE_REPORT_PROMPT,
    SUPPLEMENT_EXTRACT_PROMPT,
)


def process_text(state: ResumeAnalyzerState) -> Dict:
    if state.get("input_text"):
        return {"extracted_text": state["input_text"]}
    return {"extracted_text": ""}


def process_file(state: ResumeAnalyzerState) -> Dict:
    path = state.get("file_path", "")
    if not path or not os.path.exists(path):
        return {"file_text": ""}

    ext = os.path.splitext(path)[1].lower()
    text = ""
    try:
        if ext == ".pdf":
            from langchain_community.document_loaders import PyPDFLoader
            loader = PyPDFLoader(path)
            pages = loader.load()
            text = "\n".join(p.page_content for p in pages)
        elif ext == ".docx":
            from docx import Document
            doc = Document(path)
            text = "\n".join(p.text for p in doc.paragraphs)
        elif ext in (".txt", ".md"):
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
    except Exception:
        pass
    return {"file_text": text}


def process_image(state: ResumeAnalyzerState) -> Dict:
    path = state.get("image_path", "")
    if not path or not os.path.exists(path):
        return {"ocr_content": ""}
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(path)
        return {"ocr_content": pytesseract.image_to_string(img, lang="chi_sim+eng")}
    except Exception:
        return {"ocr_content": ""}


def integrate_info(state: ResumeAnalyzerState) -> Dict:
    parts = [
        state.get("extracted_text", ""),
        state.get("file_text", ""),
        state.get("ocr_content", ""),
    ]
    non_empty = [p for p in parts if p.strip()]

    if len(non_empty) == 0:
        return {"merged_text": "", "missing_fields": ["所有维度"], "completeness_flags": {}}
    if len(non_empty) == 1:
        return {"merged_text": non_empty[0]}

    llm = get_llm(temperature=0.1)
    combined = "\n\n---\n\n".join(non_empty)
    msg = llm.invoke([
        SystemMessage(content=INTEGRATE_PROMPT),
        HumanMessage(content=combined),
    ])
    return {"merged_text": msg.content}


def extract_params(state: ResumeAnalyzerState) -> Dict:
    merged = state.get("merged_text", "")
    supplement = state.get("supplement_text", "")

    llm = get_llm(temperature=0.1)

    if supplement and state.get("user_profile"):
        prompt = SUPPLEMENT_EXTRACT_PROMPT.format(
            supplement_text=supplement,
            current_profile=json.dumps(state["user_profile"], ensure_ascii=False),
        )
    else:
        prompt = EXTRACT_PROMPT

    text = merged + ("\n\n用户补充: " + supplement) if supplement else merged
    msg = llm.invoke([
        SystemMessage(content=prompt),
        HumanMessage(content=text),
    ])

    try:
        content = msg.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        result = json.loads(content)
    except json.JSONDecodeError:
        result = {
            "profile": {},
            "completeness_flags": {},
            "missing_fields": [],
            "overall_completeness": 0,
        }

    count = state.get("supplement_count", 0)
    if supplement:
        count += 1

    return {
        "user_profile": result.get("profile", {}),
        "completeness_flags": result.get("completeness_flags", {}),
        "missing_fields": result.get("missing_fields", []),
        "supplement_count": count,
        "supplement_text": "",
    }


def check_completeness(state: ResumeAnalyzerState) -> str:
    missing = state.get("missing_fields", [])
    count = state.get("supplement_count", 0)
    if missing and count < 3:
        return "generate_question"
    return "analyze"


def generate_question(state: ResumeAnalyzerState) -> Dict:
    missing = state.get("missing_fields", [])
    profile = json.dumps(state.get("user_profile", {}), ensure_ascii=False)

    llm = get_llm(temperature=0.3)
    prompt = QUESTION_PROMPT.format(missing_fields=", ".join(missing), current_profile=profile)
    msg = llm.invoke([HumanMessage(content=prompt)])
    return {"next_question": msg.content}


def analyze_profile(state: ResumeAnalyzerState) -> Dict:
    profile = json.dumps(state.get("user_profile", {}), ensure_ascii=False)

    llm = get_llm(temperature=0.1)
    prompt = ANALYZE_PROMPT.format(user_profile=profile)
    msg = llm.invoke([HumanMessage(content=prompt)])

    try:
        content = msg.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        analysis = json.loads(content)
    except json.JSONDecodeError:
        analysis = {"completeness": 0, "radar_data": [], "competitiveness": {}, "skill_keywords": []}

    return {
        "skill_analysis": analysis.get("radar_data", []),
        "competitiveness": analysis.get("competitiveness", {}),
    }


def generate_report(state: ResumeAnalyzerState) -> Dict:
    profile = json.dumps(state.get("user_profile", {}), ensure_ascii=False)
    analysis = json.dumps(state.get("competitiveness", {}), ensure_ascii=False)

    llm = get_llm(temperature=0.3)
    prompt = GENERATE_REPORT_PROMPT.format(user_profile=profile, analysis_result=analysis)
    msg = llm.invoke([HumanMessage(content=prompt)])
    return {"report": msg.content}
