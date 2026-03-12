"""Master Orchestrator Agent — routes user requests to specialist agents using LangGraph."""

import json
import logging
import re
import time
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

logger = logging.getLogger(__name__)

ROUTING_RETRY_ATTEMPTS = 2


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
    1. classify_intent → Analyzes user request, retries on parse failure, selects agent(s)
    2. execute_agents → Runs assigned agents sequentially by priority, with error isolation
    3. aggregate_results → Combines all agent outputs into a structured final response

    Features:
    - Robust JSON extraction from LLM responses (handles markdown fences, preamble text)
    - Retry on routing parse failure with a stricter follow-up prompt
    - Per-agent error isolation — one agent failure doesn't block others
    - Execution timing and metadata tracking
    - Routing validation against the agent registry
    """

    VALID_AGENT_IDS = {
        "code_reviewer", "bug_analyzer", "architecture", "testing",
        "security", "documentation", "refactoring", "devops", "performance",
    }

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

    # ------------------------------------------------------------------
    # JSON extraction helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any] | None:
        """Extract JSON from LLM text that may contain markdown fences or preamble."""
        # Try direct parse first
        stripped = text.strip()
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass

        # Strip markdown code fences
        fence_match = re.search(r"```(?:json)?\s*\n?(.*?)```", stripped, re.DOTALL)
        if fence_match:
            try:
                return json.loads(fence_match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # Try to find any JSON object in the text
        brace_match = re.search(r"\{.*\}", stripped, re.DOTALL)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                pass

        return None

    def _validate_routing(self, routing: dict[str, Any]) -> dict[str, Any]:
        """Validate and sanitize the routing decision against the registry."""
        assignments = routing.get("assignments", [])
        valid_assignments = []

        for assignment in assignments:
            agent_id = assignment.get("agent_id", "")
            if agent_id in self.VALID_AGENT_IDS:
                # Ensure required fields
                assignment.setdefault("task", "")
                assignment.setdefault("priority", 1)
                valid_assignments.append(assignment)
            else:
                logger.warning("Ignoring unknown agent_id in routing: %s", agent_id)

        if not valid_assignments:
            # Fallback to code_reviewer if all agents were invalid
            valid_assignments = [{
                "agent_id": "code_reviewer",
                "task": routing.get("analysis", "Analyze the request"),
                "priority": 1,
            }]
            routing["analysis"] = (
                routing.get("analysis", "") +
                " (Warning: Original routing had no valid agents — defaulting to code_reviewer)"
            )

        routing["assignments"] = valid_assignments
        return routing

    # ------------------------------------------------------------------
    # Pipeline nodes
    # ------------------------------------------------------------------

    def _classify_intent(self, state: OrchestratorState) -> dict[str, Any]:
        """Analyze the user's request and decide which agents to invoke.

        Includes retry logic: if the first attempt fails to produce valid JSON,
        a stricter follow-up prompt is sent.
        """
        registry_summary = self.registry.get_registry_summary()
        system_prompt = ORCHESTRATOR_SYSTEM_PROMPT.format(agent_registry=registry_summary)

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=state["user_request"]),
        ]

        for attempt in range(1, ROUTING_RETRY_ATTEMPTS + 1):
            try:
                response = self._llm.invoke(messages)
                routing = self._extract_json(response.content)

                if routing and "assignments" in routing:
                    routing = self._validate_routing(routing)
                    return {"routing_decision": routing}

                # If parsing failed, add a correction message for retry
                if attempt < ROUTING_RETRY_ATTEMPTS:
                    messages.append(response)
                    messages.append(HumanMessage(
                        content=(
                            "Your response was not valid JSON or was missing the 'assignments' key. "
                            "Please respond with ONLY a valid JSON object in this exact format:\n"
                            '{"analysis": "...", "assignments": [{"agent_id": "...", "task": "...", "priority": 1}]}'
                        )
                    ))
                    logger.warning("Routing attempt %d failed, retrying with correction prompt", attempt)
            except Exception as e:
                logger.error("Routing attempt %d raised %s: %s", attempt, type(e).__name__, e)
                if attempt >= ROUTING_RETRY_ATTEMPTS:
                    break

        # Ultimate fallback
        logger.warning("All routing attempts failed — using fallback routing to code_reviewer")
        return {
            "routing_decision": {
                "analysis": "Could not determine optimal routing — defaulting to code review.",
                "assignments": [{
                    "agent_id": "code_reviewer",
                    "task": state["user_request"],
                    "priority": 1,
                }],
            }
        }

    def _execute_agents(self, state: OrchestratorState) -> dict[str, Any]:
        """Execute the assigned agents based on the routing decision.

        Agents are executed sequentially sorted by priority. Each agent runs in
        an isolated error boundary — a failure in one agent does not prevent
        subsequent agents from running.
        """
        routing = state["routing_decision"]
        assignments = routing.get("assignments", [])

        # Sort by priority (lower = higher priority)
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
                logger.info("Executing agent: %s (task: %s)", agent.name, task[:80])
                agent_start = time.time()
                result = agent.invoke(task)
                agent_elapsed = round(time.time() - agent_start, 2)
                result.setdefault("metadata", {})["orchestrator_elapsed_seconds"] = agent_elapsed
                results.append(result)
            except Exception as e:
                logger.error("Agent %s failed: %s: %s", agent_id, type(e).__name__, e)
                results.append({
                    "agent_id": agent_id,
                    "agent_name": agent.name,
                    "task_description": task,
                    "result": f"Error during execution: {type(e).__name__}: {e}",
                    "status": "error",
                })

        return {"agent_results": results}

    def _aggregate_results(self, state: OrchestratorState) -> dict[str, Any]:
        """Combine results from all agents into a cohesive final response."""
        results = state["agent_results"]
        routing = state["routing_decision"]

        parts = []
        parts.append(f"## Orchestrator Analysis\n{routing.get('analysis', 'N/A')}\n")

        success_count = sum(1 for r in results if r.get("status") == "success")
        error_count = sum(1 for r in results if r.get("status") == "error")
        parts.append(f"**Agents executed:** {len(results)} | ✅ {success_count} succeeded | ❌ {error_count} failed\n")

        for result in results:
            status_icon = "✅" if result["status"] == "success" else "❌"
            metadata = result.get("metadata", {})
            timing = ""
            if "execution_time_seconds" in metadata:
                timing = f" ({metadata['execution_time_seconds']}s)"
            iterations = ""
            if "tool_iterations" in metadata:
                iterations = f" | Tool iterations: {metadata['tool_iterations']}"

            parts.append(
                f"---\n"
                f"## {status_icon} {result['agent_name']} Agent{timing}{iterations}\n\n"
                f"### Task Description\n{result['task_description']}\n\n"
                f"### Result\n{result['result']}\n"
            )

        return {"final_response": "\n".join(parts)}

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

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

        routing = self._extract_json(response.content)
        if routing and "assignments" in routing:
            return self._validate_routing(routing)
        return {"analysis": "Could not parse routing preview", "assignments": []}

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
