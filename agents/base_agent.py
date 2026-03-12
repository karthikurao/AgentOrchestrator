"""Abstract base class for all specialist agents."""

from abc import ABC, abstractmethod
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from config.settings import settings


class BaseAgent(ABC):
    """Base class that all specialist agents must extend.

    Provides:
    - LLM initialization via GitHub Models API
    - Common invoke/describe/format interface
    - Structured output with task descriptions
    """

    def __init__(self, agent_id: str, name: str, tools: list | None = None) -> None:
        self.agent_id = agent_id
        self.name = name
        self.tools = tools or []
        self._llm = ChatOpenAI(**settings.get_llm_kwargs())
        if self.tools:
            self._llm_with_tools = self._llm.bind_tools(self.tools)
        else:
            self._llm_with_tools = self._llm

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt that defines this agent's persona and behavior."""

    def describe_task(self, user_request: str) -> str:
        """Generate a thorough, detailed description of what this agent will do for the given request.

        This is called by the orchestrator before execution so the user
        understands exactly what work will be performed.
        """
        description_prompt = (
            f"You are the {self.name} agent. A user has made the following request:\n\n"
            f'"{user_request}"\n\n'
            "Provide a thorough, detailed description of EXACTLY what you will do to address "
            "this request. Include:\n"
            "1. The specific steps you will take\n"
            "2. What aspects you will analyze or review\n"
            "3. What kind of output/deliverables the user can expect\n"
            "4. Any assumptions you are making\n\n"
            "Be specific and actionable — this description tells the user what work is being performed."
        )
        response = self._llm.invoke([
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=description_prompt),
        ])
        return response.content

    def invoke(self, user_request: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute this agent's task and return structured results.

        Args:
            user_request: The user's original request or the orchestrator's task assignment.
            context: Optional additional context (file contents, git diffs, etc.).

        Returns:
            Dict with keys: agent_id, agent_name, task_description, result, status
        """
        task_description = self.describe_task(user_request)

        context_block = ""
        if context:
            context_parts = []
            for key, value in context.items():
                context_parts.append(f"### {key}\n```\n{value}\n```")
            context_block = "\n\n## Provided Context\n" + "\n\n".join(context_parts)

        execution_prompt = (
            f"## Task\n{user_request}\n\n"
            f"## Your Task Description\n{task_description}"
            f"{context_block}\n\n"
            "Now execute the task thoroughly. Provide detailed, actionable output."
        )

        response = self._llm_with_tools.invoke([
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=execution_prompt),
        ])

        return self.format_output(
            task_description=task_description,
            result=response.content,
            status="success",
        )

    def format_output(self, task_description: str, result: str, status: str) -> dict[str, Any]:
        """Format the agent's output into a consistent structure."""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.name,
            "task_description": task_description,
            "result": result,
            "status": status,
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.agent_id}, name={self.name})>"
