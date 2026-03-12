"""Inter-agent communication tools — LangChain tools for agent-to-agent delegation."""

from typing import Any

from langchain_core.tools import tool


def create_delegate_tool(bus: Any, calling_agent_id: str):
    """Create a delegate_to_agent tool bound to a specific agent and communication bus.

    This tool allows an agent to directly invoke another specialist agent.
    """

    @tool
    def delegate_to_agent(agent_id: str, task: str) -> str:
        """Delegate a sub-task to another specialist agent and get their result.

        Use this when your current task would benefit from another agent's expertise.
        For example, a code_reviewer might delegate security concerns to the security agent.

        Available agents: code_reviewer, bug_analyzer, architecture, testing,
        security, documentation, refactoring, devops, performance, exploit_analyzer.

        Args:
            agent_id: The ID of the agent to delegate to (e.g., 'security', 'testing').
            task: A clear, specific description of what the target agent should do.
        """
        try:
            return bus.delegate(calling_agent_id, agent_id, task)
        except Exception as e:
            return f"Delegation failed: {type(e).__name__}: {e}"

    return delegate_to_agent


def create_orchestrator_route_tool(bus: Any, calling_agent_id: str):
    """Create a request_via_orchestrator tool bound to a specific agent and bus.

    This tool allows an agent to route a task through the master orchestrator,
    which will classify the intent and dispatch to the best agent(s).
    """

    @tool
    def request_via_orchestrator(task: str) -> str:
        """Route a task through the master orchestrator for intelligent agent selection.

        Use this when you're unsure which agent should handle a sub-task — the
        orchestrator will analyze the request and dispatch it to the most
        appropriate specialist agent(s).

        Args:
            task: A clear description of the task to route through the orchestrator.
        """
        try:
            return bus.request_via_orchestrator(calling_agent_id, task)
        except Exception as e:
            return f"Orchestrator routing failed: {type(e).__name__}: {e}"

    return request_via_orchestrator


def create_agent_tools(bus: Any, calling_agent_id: str) -> list:
    """Factory: create all inter-agent communication tools for a given agent.

    Returns a list of LangChain tools that the agent can use to communicate
    with other agents during execution.
    """
    return [
        create_delegate_tool(bus, calling_agent_id),
        create_orchestrator_route_tool(bus, calling_agent_id),
    ]
