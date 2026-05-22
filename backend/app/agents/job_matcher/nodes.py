"""LangGraph nodes for the Job Matcher agent."""

import json
from typing import Dict

from app.agents.job_matcher.state import JobMatcherState
from app.agents.job_matcher import db_utils
from app.agents.job_matcher.scorer import MatchScorer
from app.agents.harness import harness
from app.rag.retrievers import resume_job_matcher
from app.db.neo4j import neo4j_manager


async def load_user_profile(state: JobMatcherState) -> Dict:
    uid = state["user_id"]

    # If frontend sent profile data (from profileState.js), use it directly
    input_profile = state.get("user_profile", {})
    if input_profile and input_profile.get("source") == "frontend":
        radar = input_profile.get("radar_data", [])
        if radar and any(v > 0 for v in radar):
            # Also save to DB for future use
            try:
                await db_utils.save_user_profile(uid, input_profile)
            except Exception:
                pass
            return {"user_profile": input_profile}

    # Otherwise read from database
    profile = await db_utils.get_user_profile(uid)
    if profile:
        pd = profile.get("profile_data", {})
        if isinstance(pd, str):
            try:
                pd = json.loads(pd)
            except Exception:
                pd = {}
        # Check if profile has meaningful data (radar_data with non-zero values)
        radar = pd.get("radar_data", [])
        if radar and any(v > 0 for v in radar):
            return {"user_profile": pd}
        # Profile exists but has no meaningful scores
        return {"user_profile": {}, "error": "用户画像数据为空，请先在「职能助手」中完成对话分析"}

    # If no user profile yet, check if there's one in the state
    if state.get("user_profile"):
        profile_data = state["user_profile"]
        await db_utils.save_user_profile(uid, profile_data)
        return {"user_profile": profile_data}

    return {"user_profile": {}, "error": "未找到用户画像，请先在「职能助手」中完成对话分析"}


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


async def algorithmic_match(state: JobMatcherState) -> Dict:
    """Match jobs using job_profiler (LLM) + algorithmic scoring."""
    import asyncio

    # Check if there's an error from load_user_profile (no valid profile)
    if state.get("error"):
        return {"match_results": []}

    profile = state.get("user_profile", {})
    jobs = state.get("job_details", [])

    if not jobs:
        return {"match_results": []}

    # Step 1: Get job requirements for each job via job_profiler agent
    async def get_job_requirements(job: dict) -> dict:
        try:
            result = await harness.run("job_profiler", {"job_info": job})
            if result.get("success") and result.get("data"):
                return result["data"].get("job_requirements", {})
        except Exception as e:
            print(f"[Match] job_profiler error: {e}")
        return {}

    # Run all job_profiler calls concurrently
    req_tasks = [get_job_requirements(job) for job in jobs]
    all_requirements = await asyncio.gather(*req_tasks)

    # Step 2: Compute match scores using the scorer
    scorer = MatchScorer()
    results = []
    for job, job_reqs in zip(jobs, all_requirements):
        try:
            score_result = scorer.compute_scores(profile, job_reqs, job_info=job)
        except Exception as e:
            print(f"[Match] scorer error: {e}")
            score_result = {
                "total_score": 0, "scores": {},
                "summary": "评分异常", "recommendations": [],
            }
        results.append({
            "job_id": job.get("id"),
            "job_title": job.get("job_title", ""),
            "company": job.get("company", ""),
            "industry": job.get("industry", ""),
            "city": job.get("city", ""),
            "salary_range": job.get("salary_range", ""),
            **score_result,
        })

    results.sort(key=lambda r: r.get("total_score", 0), reverse=True)
    return {"match_results": results}


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
