"""Resume Analyzer Agent — merged resume_extractor + data_analyzer.

LangGraph flow:
Phase 1 (Extraction):
  process_text -> process_file -> process_image -> integrate_info
  -> extract_params -> check_completeness
  -> (missing?) generate_question -> END (with next_question in response)
  -> (complete) analyze_profile -> generate_report -> END
"""
from typing import Dict, Any

from langgraph.graph import StateGraph, END

from app.agents.base import AgentBase
from app.agents.resume_analyzer.state import ResumeAnalyzerState
from app.agents.resume_analyzer import nodes


class ResumeAnalyzerAgent(AgentBase):
    @property
    def agent_id(self) -> str:
        return "resume_analyzer"

    @property
    def display_name(self) -> str:
        return "简历分析与评估"

    @property
    def description(self) -> str:
        return "从文本、文档、图片中提取简历信息，进行7维能力评分和竞争力分析，生成职业发展报告"

    def build_graph(self) -> StateGraph:
        builder = StateGraph(ResumeAnalyzerState)

        builder.add_node("process_text", nodes.process_text)
        builder.add_node("process_file", nodes.process_file)
        builder.add_node("process_image", nodes.process_image)
        builder.add_node("integrate_info", nodes.integrate_info)
        builder.add_node("extract_params", nodes.extract_params)
        builder.add_node("check_completeness", nodes.check_completeness)
        builder.add_node("generate_question", nodes.generate_question)
        builder.add_node("analyze_profile", nodes.analyze_profile)
        builder.add_node("generate_report", nodes.generate_report)

        builder.set_entry_point("process_text")
        builder.add_edge("process_text", "process_file")
        builder.add_edge("process_file", "process_image")
        builder.add_edge("process_image", "integrate_info")
        builder.add_edge("integrate_info", "extract_params")
        builder.add_edge("extract_params", "check_completeness")

        builder.add_conditional_edges(
            "check_completeness",
            nodes.check_completeness,
            {
                "generate_question": "generate_question",
                "analyze": "analyze_profile",
            },
        )
        builder.add_edge("generate_question", END)
        builder.add_edge("analyze_profile", "generate_report")
        builder.add_edge("generate_report", END)

        return builder.compile()

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        graph = self.build_graph()
        result = await graph.ainvoke({
            "input_text": input_data.get("input_text", ""),
            "file_path": input_data.get("file_path", ""),
            "image_path": input_data.get("image_path", ""),
            "supplement_text": input_data.get("supplement_text", ""),
            "supplement_count": input_data.get("supplement_count", 0),
            "user_profile": input_data.get("user_profile", {}),
        })

        return {
            "step": "complete" if "report" in result else "extract",
            "user_profile": result.get("user_profile"),
            "completeness_flags": result.get("completeness_flags"),
            "missing_fields": result.get("missing_fields", []),
            "next_question": result.get("next_question"),
            "supplement_count": result.get("supplement_count", 0),
            "skill_analysis": result.get("skill_analysis"),
            "competitiveness": result.get("competitiveness"),
            "report": result.get("report"),
        }


agent = ResumeAnalyzerAgent()
