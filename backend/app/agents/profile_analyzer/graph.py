from typing import Dict, Any
from langgraph.graph import StateGraph, END
from app.agents.base import AgentBase
from app.agents.profile_analyzer.state import ProfileAnalyzerState
from app.agents.profile_analyzer.nodes import extract_info, score_dimensions, format_output


class ProfileAnalyzerAgent(AgentBase):

    @property
    def agent_id(self) -> str:
        return "profile_analyzer"

    @property
    def display_name(self) -> str:
        return "画像分析引擎"

    @property
    def description(self) -> str:
        return "实时分析对话内容，提取7维度能力评分，驱动雷达图动态更新"

    @property
    def cacheable(self) -> bool:
        return False

    def build_graph(self) -> StateGraph:
        graph = StateGraph(ProfileAnalyzerState)
        graph.add_node("extract_info", extract_info)
        graph.add_node("score_dimensions", score_dimensions)
        graph.add_node("format_output", format_output)
        graph.set_entry_point("extract_info")
        graph.add_edge("extract_info", "score_dimensions")
        graph.add_edge("score_dimensions", "format_output")
        graph.add_edge("format_output", END)
        return graph.compile()

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        graph = self.build_graph()
        state = {
            "chat_history": input_data.get("chat_history", []),
            "previous_radar_data": input_data.get("previous_radar_data", []),
            "previous_details": input_data.get("previous_details", {}),
        }
        result = await graph.ainvoke(state)
        return {
            "radar_data": result.get("radar_data", [0, 0, 0, 0, 0, 0, 0]),
            "dimension_details": result.get("dimension_details", {}),
        }


agent = ProfileAnalyzerAgent()
