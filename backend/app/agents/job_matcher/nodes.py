"""LangGraph nodes for the Job Matcher agent."""

import asyncio
import json
from typing import Dict

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.llm_factory import get_llm
from app.agents.job_matcher.state import JobMatcherState
from app.agents.job_matcher.prompts import WEIGHT_PROMPT, MATCH_PROMPT, MERGE_PROMPT
from app.agents.job_matcher import db_utils
from app.rag.retrievers import resume_job_matcher
from app.db.neo4j import neo4j_manager


async def load_user_profile(state: JobMatcherState) -> Dict:
    uid = state["user_id"]
    profile = await db_utils.get_user_profile(uid)
    if profile:
        return {"user_profile": profile.get("profile_data", {})}

    # If no user profile yet, check if there's one in the state
    if state.get("user_profile"):
        profile_data = state["user_profile"]
        await db_utils.save_user_profile(uid, profile_data)
        return {"user_profile": profile_data}

    return {"user_profile": {"error": "No user profile found. Please complete resume extraction first."}}


async def retrieve_candidates(state: JobMatcherState) -> Dict:
    """RAG: use resume text to find top candidate jobs via vector search."""
    profile = state.get("user_profile", {})
    # Build a search query from user profile
    profile_text = json.dumps(profile, ensure_ascii=False)
    candidate_ids = resume_job_matcher.retrieve_candidates(profile_text, top_k=10)
    return {"candidate_job_ids": candidate_ids}


async def load_job_details(state: JobMatcherState) -> Dict:
    ids = state.get("candidate_job_ids", [])
    if not ids:
        # Fallback: user favorites
        uid = state["user_id"]
        fav_ids = await db_utils.get_user_favorites(uid)
        if fav_ids:
            ids = [str(i) for i in fav_ids]

    if not ids:
        return {"job_details": [], "match_results": []}

    details = await db_utils.get_job_details([int(i) for i in ids])
    return {"job_details": details}


async def neo4j_enrich(state: JobMatcherState) -> Dict:
    """Enrich job matching with Neo4j graph profiles."""
    jobs = state.get("job_details", [])
    profiles = []

    try:
        session = await neo4j_manager.get_session()
        if session is None:
            return {"neo4j_profiles": []}
        for job in jobs:
            result = await session.run(
                "MATCH (jp:JobProfile {title: $title}) RETURN jp",
                title=job.get("job_title", ""),
            )
            record = await result.single()
            if record:
                profiles.append(dict(record["jp"]))
        await session.close()
    except Exception:
        pass

    return {"neo4j_profiles": profiles}


async def llm_match(state: JobMatcherState) -> Dict:
    """LLM-based dimension matching for each job."""
    profile = state.get("user_profile", {})
    jobs = state.get("job_details", [])
    neo4j = state.get("neo4j_profiles", [])

    if not jobs:
        return {"match_results": []}

    llm = get_llm(temperature=0.3)

    async def match_one(job: dict, n4j: dict | None) -> dict:
        profile_text = json.dumps(profile, ensure_ascii=False)
        job_text = json.dumps(job, ensure_ascii=False)

        # Determine weights
        weight_msg = llm.invoke([
            SystemMessage(content="输出纯JSON，不要加任何前缀说明。"),
            HumanMessage(content=WEIGHT_PROMPT.format(job_info=job_text)),
        ])
        try:
            weights = _parse_json(weight_msg.content)
        except Exception:
            weights = {}

        # Match
        match_msg = llm.invoke([
            SystemMessage(content="输出纯JSON，不要加任何前缀说明。"),
            HumanMessage(content=MATCH_PROMPT.format(
                user_profile=profile_text,
                job_requirement=job_text,
                weights=json.dumps(weights, ensure_ascii=False),
            )),
        ])
        try:
            match_result = _parse_json(match_msg.content)
        except Exception:
            match_result = {"total_score": 0, "scores": {}, "summary": "匹配失败"}

        return {
            "job_id": job.get("id"),
            "job_title": job.get("job_title", ""),
            "company": job.get("company", ""),
            "industry": job.get("industry", ""),
            "city": job.get("city", ""),
            "salary_range": job.get("salary_range", ""),
            **match_result,
        }

    tasks = []
    for job in jobs:
        n4j_match = next((n for n in neo4j if n.get("title") == job.get("job_title")), None)
        tasks.append(match_one(job, n4j_match))

    results = await asyncio.gather(*tasks)
    return {"match_results": list(results)}


async def rank_results(state: JobMatcherState) -> Dict:
    results = state.get("match_results", [])
    ranked = sorted(results, key=lambda r: r.get("total_score", 0), reverse=True)
    return {"ranked_results": ranked}


async def save_report(state: JobMatcherState) -> Dict:
    uid = state["user_id"]
    ranked = state.get("ranked_results", [])

    for r in ranked[:5]:  # Top 5
        await db_utils.save_match_report(
            user_id=uid,
            job_name=r.get("job_title", ""),
            match_score=float(r.get("total_score", 0)),
            report_data=r,
            industry=r.get("industry", ""),
            city=r.get("city", ""),
        )

    return {"report_id": 0}


def _parse_json(content: str) -> dict:
    c = content.strip()
    for marker in ("```json", "```"):
        if marker in c:
            c = c.split(marker)[1].split("```")[0]
            break
    return json.loads(c)
