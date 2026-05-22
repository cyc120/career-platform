"""Job Matcher Agent — RAG + LLM job profiling + algorithmic matching.

LangGraph flow:
  load_user_profile -> retrieve_candidates (RAG) -> load_job_details
  -> neo4j_enrich -> algorithmic_match (job_profiler + scorer) -> rank_results -> save_report -> END
"""
from typing import Dict, Any

from langgraph.graph import StateGraph, END

from app.agents.base import AgentBase
from app.agents.job_matcher.state import JobMatcherState
from app.agents.job_matcher import nodes


class JobMatcherAgent(AgentBase):
    @property
    def agent_id(self) -> str:
        return "job_matcher"

    @property
    def display_name(self) -> str:
        return "人岗智能匹配"

    @property
    def description(self) -> str:
        return "基于RAG检索+LLM岗位画像+7维算法匹配，从向量库和Neo4j知识图谱中匹配最适合的岗位"

    @property
    def cacheable(self) -> bool:
        return False

    def build_graph(self) -> StateGraph:
        builder = StateGraph(JobMatcherState)

        builder.add_node("load_user_profile", nodes.load_user_profile)
        builder.add_node("retrieve_candidates", nodes.retrieve_candidates)
        builder.add_node("load_job_details", nodes.load_job_details)
        builder.add_node("neo4j_enrich", nodes.neo4j_enrich)
        builder.add_node("algorithmic_match", nodes.algorithmic_match)
        builder.add_node("rank_results", nodes.rank_results)
        builder.add_node("save_report", nodes.save_report)

        builder.set_entry_point("load_user_profile")
        builder.add_edge("load_user_profile", "retrieve_candidates")
        builder.add_edge("retrieve_candidates", "load_job_details")
        builder.add_edge("load_job_details", "neo4j_enrich")
        builder.add_edge("neo4j_enrich", "algorithmic_match")
        builder.add_edge("algorithmic_match", "rank_results")
        builder.add_edge("rank_results", "save_report")
        builder.add_edge("save_report", END)

        return builder.compile()

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        graph = self.build_graph()
        result = await graph.ainvoke({
            "user_id": input_data.get("user_id", 0),
            "user_profile": input_data.get("user_profile", {}),
        })

        # If there's an error (no profile), return error message
        if result.get("error"):
            return {
                "error": result["error"],
                "matches": [],
                "total_matches": 0,
            }

        return {
            "matches": result.get("ranked_results", []),
            "total_matches": len(result.get("ranked_results", [])),
        }


agent = JobMatcherAgent()
