"""Report Agent — aggregates all module data, generates and polishes career reports."""

from typing import Dict, Any

from langgraph.graph import StateGraph, END

from app.agents.base import AgentBase
from app.agents.report.state import ReportState
from app.agents.report import nodes


class ReportAgent(AgentBase):
    @property
    def agent_id(self) -> str:
        return "report"

    @property
    def display_name(self) -> str:
        return "职业分析报告"

    @property
    def description(self) -> str:
        return "聚合用户画像、岗位匹配、学习计划、职业规划等数据，生成完整职业分析报告，支持润色和多格式导出"

    @property
    def timeout_seconds(self) -> int:
        return 180

    @property
    def cacheable(self) -> bool:
        return False

    def build_graph(self) -> StateGraph:
        builder = StateGraph(ReportState)

        builder.add_node("load_all_data", nodes.load_all_data)
        builder.add_node("generate_report", nodes.generate_report)
        builder.add_node("polish_report", nodes.polish_report)
        builder.add_node("format_report", nodes.format_report)

        builder.set_entry_point("load_all_data")

        # generate path: load -> generate -> format -> END
        # polish path: load (skip) -> polish -> format -> END
        builder.add_conditional_edges(
            "load_all_data",
            lambda state: "generate_report" if state.get("action") == "generate" else "polish_report",
            {"generate_report": "generate_report", "polish_report": "polish_report"},
        )
        builder.add_edge("generate_report", "format_report")
        builder.add_edge("polish_report", "format_report")
        builder.add_edge("format_report", END)

        return builder.compile()

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        graph = self.build_graph()
        result = await graph.ainvoke({
            "user_id": input_data.get("user_id", 0),
            "action": input_data.get("action", "generate"),
            "polish_feedback": input_data.get("polish_feedback", ""),
            "report_text": input_data.get("report_text", ""),
        })
        return {
            "report_text": result.get("report_text", ""),
            "error": result.get("error", ""),
        }


agent = ReportAgent()
