"""Unified Agent Registry — 4 independent agents registered with Harness.

Note: job_profiler and profile_analyzer are sub-modules, not independent agents.
- job_profiler is used internally by job_matcher
- profile_analyzer is used internally by the learning_plan API
"""

from app.agents.harness import harness
from app.agents.resume_analyzer.graph import agent as resume_analyzer
from app.agents.job_matcher.graph import agent as job_matcher
from app.agents.career_planner.graph import agent as career_planner
from app.agents.learning_plan.graph import agent as learning_plan

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
    _initialized = True
