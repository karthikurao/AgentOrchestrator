"""Master Orchestrator Agent — routes user requests to specialist agents using LangGraph."""

import json
from typing import Any, TypedDict

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

from config.settings import settings
from config.agent_registry import AgentRegistry
from prompts.orchestrator_prompt import ORCHESTRATOR_SYSTEM_PROMPT

from agents.code_reviewer import CodeReviewerAgent
from agents.bug_analyzer import BugAnalyzerAgent
from agents.architecture import ArchitectureAgent
from agents.testing import TestingAgent
from agents.security import SecurityAgent
from agents.documentation import DocumentationAgent
from agents.refactoring import RefactoringAgent
from agents.devops import DevOpsAgent
from agents.performance import PerformanceAgent


class OrchestratorState(TypedDict):
    """State that flows through the LangGraph orchestration pipeline."""
    user_request: str
    routing_decision: dict[str, Any]
    agent_results: list[dict[str, Any]]
    final_response: str
    error: str | None


class OrchestratorAgent:
    """Master orchestrator that routes requests to specialist agents.

    Uses LangGraph to build a state machine:
    1. classify_intent → Analyzes user request and selects agent(s)
    2. execute_agents → Runs the selected agent(s) with task descriptions
    3. aggregate_results → Combines all agent outputs into a final response
    """

    def __init__(self) -> None:
        self.registry = AgentRegistry()
        self._llm = ChatOpenAI(**settings.get_llm_kwargs())
        self._agents = self._initialize_agents()
        self._graph = self._build_graph()

    def _initialize_agents(self) -> dict[str, Any]:
        """Create instances of all specialist agents."""
        return {
            "code_reviewer": CodeReviewerAgent(),
            "bug_analyzer": BugAnalyzerAgent(),
            "architecture": ArchitectureAgent(),
            "testing": TestingAgent(),
            "security": SecurityAgent(),
            "documentation": DocumentationAgent(),
            "refactoring": RefactoringAgent(),
            "devops": DevOpsAgent(),
            "performance": PerformanceAgent(),
        }

    def _build_graph(self) -> Any:
        """Build the LangGraph state machine for orchestration."""
        graph = StateGraph(OrchestratorState)

        graph.add_node("classify_intent", self._classify_intent)
        graph.add_node("execute_agents", self._execute_agents)
        graph.add_node("aggregate_results", self._aggregate_results)

        graph.set_entry_point("classify_intent")
        graph.add_edge("classify_intent", "execute_agents")
        graph.add_edge("execute_agents", "aggregate_results")
        graph.add_edge("aggregate_results", END)

        return graph.compile()

    def _classify_intent(self, state: OrchestratorState) -> dict[str, Any]:
        """Analyze the user's request and decide which agents to invoke."""
        registry_summary = self.registry.get_registry_summary()
        system_prompt = ORCHESTRATOR_SYSTEM_PROMPT.format(agent_registry=registry_summary)

        response = self._llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=state["user_request"]),
        ])

        try:
            # Parse the JSON routing decision
            content = response.content.strip()
            # Handle markdown code blocks
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
            routing = json.loads(content)
        except (json.JSONDecodeError, IndexError):
            # Fallback: if parsing fails, try to extract JSON from the response
            routing = {
                "analysis": "Failed to parse routing decision, using fallback.",
                "assignments": [{
                    "agent_id": "code_reviewer",
                    "task": state["user_request"],
                    "priority": 1,
                }],
            }

        return {"routing_decision": routing}

    def _execute_agents(self, state: OrchestratorState) -> dict[str, Any]:
        """Execute the assigned agents based on the routing decision."""
        routing = state["routing_decision"]
        assignments = routing.get("assignments", [])

        # Sort by priority
        assignments.sort(key=lambda a: a.get("priority", 1))

        results = []
        for assignment in assignments:
            agent_id = assignment.get("agent_id", "")
            task = assignment.get("task", state["user_request"])

            agent = self._agents.get(agent_id)
            if not agent:
                results.append({
                    "agent_id": agent_id,
                    "agent_name": "Unknown",
                    "task_description": f"Agent '{agent_id}' not found in registry.",
                    "result": f"Error: No agent registered with ID '{agent_id}'.",
                    "status": "error",
                })
                continue

            try:
                result = agent.invoke(task)
                results.append(result)
            except Exception as e:
                results.append({
                    "agent_id": agent_id,
                    "agent_name": agent.name,
                    "task_description": task,
                    "result": f"Error during execution: {str(e)}",
                    "status": "error",
                })

        return {"agent_results": results}

    def _aggregate_results(self, state: OrchestratorState) -> dict[str, Any]:
        """Combine results from all agents into a cohesive final response."""
        results = state["agent_results"]
        routing = state["routing_decision"]

        parts = []
        parts.append(f"## Orchestrator Analysis\n{routing.get('analysis', 'N/A')}\n")

        for result in results:
            status_icon = "✅" if result["status"] == "success" else "❌"
            parts.append(
                f"---\n"
                f"## {status_icon} {result['agent_name']} Agent\n\n"
                f"### Task Description\n{result['task_description']}\n\n"
                f"### Result\n{result['result']}\n"
            )

        return {"final_response": "\n".join(parts)}

    def invoke(self, user_request: str) -> dict[str, Any]:
        """Process a user request through the orchestration pipeline.

        Args:
            user_request: The user's natural language request.

        Returns:
            The full orchestration state including routing decisions and agent results.
        """
        initial_state: OrchestratorState = {
            "user_request": user_request,
            "routing_decision": {},
            "agent_results": [],
            "final_response": "",
            "error": None,
        }
        return self._graph.invoke(initial_state)

    def get_routing_preview(self, user_request: str) -> dict[str, Any]:
        """Preview which agents would be selected without executing them.

        Useful for showing the user the plan before committing to execution.
        """
        registry_summary = self.registry.get_registry_summary()
        system_prompt = ORCHESTRATOR_SYSTEM_PROMPT.format(agent_registry=registry_summary)

        response = self._llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_request),
        ])

        try:
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
            return json.loads(content)
        except (json.JSONDecodeError, IndexError):
            return {"analysis": "Could not parse routing", "assignments": []}

    def list_agents(self) -> list[dict[str, str]]:
        """List all available agents with their descriptions."""
        return [
            {
                "id": info.agent_id,
                "name": info.name,
                "description": info.description,
            }
            for info in self.registry.list_all()
        ]
