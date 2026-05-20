from abc import ABC, abstractmethod
from typing import Any, Dict
from langgraph.graph import StateGraph


class AgentBase(ABC):
    @abstractmethod
    def build_graph(self) -> StateGraph:
        """Build and return a compiled LangGraph StateGraph."""
        ...

    @abstractmethod
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the graph with input data, return structured result."""
        ...

    @property
    @abstractmethod
    def agent_id(self) -> str:
        ...

    @property
    @abstractmethod
    def display_name(self) -> str:
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        ...

    @property
    def max_retries(self) -> int:
        return 3

    @property
    def timeout_seconds(self) -> int:
        return 300

    @property
    def cacheable(self) -> bool:
        return True
