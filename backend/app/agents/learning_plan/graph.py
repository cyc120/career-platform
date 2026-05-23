"""Learning Plan Agent — RAG-enhanced learning plan generation.

LangGraph flow:
  detect_action (router) ->
    "generate":      load_profile -> retrieve_resources(RAG) -> generate_plan -> END
    "daily_tasks":   generate_daily_tasks -> END
    "polish":        polish_plan -> END
    "adjust":        adjust_tasks -> END
    "export":        export_plan -> END
"""
from typing import Dict, Any

from langgraph.graph import StateGraph, END

from app.agents.base import AgentBase
from app.agents.learning_plan.state import LearningPlanState
from app.agents.learning_plan import nodes


class LearningPlanAgent(AgentBase):
    @property
    def agent_id(self) -> str:
        return "learning_plan"

    @property
    def display_name(self) -> str:
        return "学习计划生成器"

    @property
    def description(self) -> str:
        return "基于RAG检索学习资源+LLM生成阶段性学习计划、每日任务、润色调整、导出Markdown"

    def build_graph(self) -> StateGraph:
        builder = StateGraph(LearningPlanState)

        builder.add_node("detect_action", nodes.detect_action_node)
        builder.add_node("load_profile_and_job", nodes.load_profile_and_job)
        builder.add_node("retrieve_resources", nodes.retrieve_resources)
        builder.add_node("generate_plan", nodes.generate_plan)
        builder.add_node("generate_daily_tasks", nodes.generate_daily_tasks)
        builder.add_node("polish_plan", nodes.polish_plan)
        builder.add_node("adjust_tasks", nodes.adjust_tasks)
        builder.add_node("export_plan", nodes.export_plan)

        builder.set_entry_point("detect_action")

        # Route based on action
        builder.add_conditional_edges(
            "detect_action",
            nodes.detect_action,
            {
                "generate": "load_profile_and_job",
                "daily_tasks": "generate_daily_tasks",
                "polish": "polish_plan",
                "adjust": "adjust_tasks",
                "export": "export_plan",
            },
        )

        builder.add_edge("load_profile_and_job", "retrieve_resources")
        builder.add_edge("retrieve_resources", "generate_plan")
        builder.add_edge("generate_plan", END)
        builder.add_edge("generate_daily_tasks", END)
        builder.add_edge("polish_plan", END)
        builder.add_edge("adjust_tasks", END)
        builder.add_edge("export_plan", END)

        return builder.compile()

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        graph = self.build_graph()
        result = await graph.ainvoke({
            "user_id": input_data.get("user_id", 0),
            "action": input_data.get("action", "generate"),
            "plan_type": input_data.get("plan_type", "长期"),
            "user_feedback": input_data.get("user_feedback", ""),
            "phase_index": input_data.get("phase_index", 0),
            "completed_task_ids": input_data.get("completed_task_ids", []),
            "remaining_tasks": input_data.get("remaining_tasks", []),
            "target_job": input_data.get("target_job", ""),
        })

        return {
            "action": input_data.get("action", "generate"),
            "learning_plan": result.get("learning_plan"),
            "daily_tasks": result.get("daily_tasks", []),
            "export_text": result.get("export_text"),
            "resources": result.get("resources", []),
            "error": result.get("error"),
        }


agent = LearningPlanAgent()
