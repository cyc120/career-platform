"""Job Profiler Agent — extracts structured 7-dimension requirements from job descriptions."""

from typing import Dict, Any

from langgraph.graph import StateGraph, END

from app.agents.base import AgentBase
from app.agents.job_profiler.state import JobProfilerState
from app.agents.job_profiler import nodes


class JobProfilerAgent(AgentBase):
    @property
    def agent_id(self) -> str:
        return "job_profiler"

    @property
    def display_name(self) -> str:
        return "岗位画像分析"

    @property
    def description(self) -> str:
        return "用LLM分析岗位描述，提取7维度能力要求画像"

    @property
    def cacheable(self) -> bool:
        return True

    def build_graph(self) -> StateGraph:
        builder = StateGraph(JobProfilerState)
        builder.add_node("extract_requirements", nodes.extract_requirements)
        builder.set_entry_point("extract_requirements")
        builder.add_edge("extract_requirements", END)
        return builder.compile()

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        graph = self.build_graph()
        result = await graph.ainvoke({
            "job_info": input_data.get("job_info", {}),
        })
        return {
            "job_requirements": result.get("job_requirements", {}),
        }


agent = JobProfilerAgent()
