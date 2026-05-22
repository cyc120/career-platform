"""Unified Agent Registry — all 6 agents registered with Harness."""

from app.agents.harness import harness
from app.agents.resume_analyzer.graph import agent as resume_analyzer
from app.agents.job_matcher.graph import agent as job_matcher
from app.agents.career_planner.graph import agent as career_planner
from app.agents.learning_plan.graph import agent as learning_plan
from app.agents.profile_analyzer.graph import agent as profile_analyzer
from app.agents.job_profiler.graph import agent as job_profiler

_initialized = False


def init_agents():
    """Register all agents with the Harness. Call once at startup."""
    global _initialized
    if _initialized:
        return
    harness.register(resume_analyzer)
    harness.register(job_matcher)
    harness.register(career_planner)
    harness.register(learning_plan)
    harness.register(profile_analyzer)
    harness.register(job_profiler)
    _initialized = True
