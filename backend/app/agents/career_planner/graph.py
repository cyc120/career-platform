"""Career Planner Agent.

LangGraph flow:
  get_top_job -> predict_trends -> get_promotion_data
  -> generate_career_path -> plot_chart -> save_plan -> END
"""
from typing import Dict, Any

from langgraph.graph import StateGraph, END

from app.agents.base import AgentBase
from app.agents.career_planner.state import CareerPlannerState
from app.agents.career_planner import nodes


class CareerPlannerAgent(AgentBase):
    @property
    def agent_id(self) -> str:
        return "career_planner"

    @property
    def display_name(self) -> str:
        return "职业规划师"

    @property
    def description(self) -> str:
        return "基于岗位匹配结果，预测岗位发展趋势，规划分阶段职业晋升路径，生成趋势图表"

    def build_graph(self) -> StateGraph:
        builder = StateGraph(CareerPlannerState)

        builder.add_node("get_top_job", nodes.get_top_job)
        builder.add_node("predict_trends", nodes.predict_trends)
        builder.add_node("get_promotion_data", nodes.get_promotion_data)
        builder.add_node("generate_career_path", nodes.generate_career_path)
        builder.add_node("plot_chart", nodes.plot_chart)
        builder.add_node("save_plan", nodes.save_plan)

        builder.set_entry_point("get_top_job")
        builder.add_edge("get_top_job", "predict_trends")
        builder.add_edge("predict_trends", "get_promotion_data")
        builder.add_edge("get_promotion_data", "generate_career_path")
        builder.add_edge("generate_career_path", "plot_chart")
        builder.add_edge("plot_chart", "save_plan")
        builder.add_edge("save_plan", END)

        return builder.compile()

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        graph = self.build_graph()
        result = await graph.ainvoke({
            "user_id": input_data.get("user_id", 0),
            "user_profile": input_data.get("user_profile", {}),
        })

        return {
            "top_job": result.get("top_job"),
            "trends": result.get("trends"),
            "promotion_data": result.get("promotion_data", []),
            "career_path": result.get("career_path"),
            "chart_path": result.get("chart_path", ""),
        }


agent = CareerPlannerAgent()
