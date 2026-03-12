"""Agent Communication Bus — thread-safe message broker for inter-agent communication."""

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any

from config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class AgentMessage:
    """A single message exchanged between agents."""
    from_agent: str
    to_agent: str
    message_type: str  # "delegation", "response", "broadcast"
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


class DelegationDepthExceeded(Exception):
    """Raised when inter-agent delegation exceeds the configured maximum depth."""


class AgentCommunicationBus:
    """Thread-safe communication bus enabling inter-agent delegation and messaging.

    Supports two communication modes:
    1. Direct delegation — Agent A invokes Agent B directly via the bus
    2. Master-mediated — Agent A requests routing through the orchestrator

    Features:
    - Thread-safe message log with Lock protection
    - Per-thread delegation depth tracking via threading.local()
    - Configurable max delegation depth to prevent infinite recursion
    - Full message history for debugging and display
    """

    def __init__(self, max_delegation_depth: int | None = None) -> None:
        self._agents: dict[str, Any] = {}
        self._orchestrator_route_fn = None
        self._message_log: list[AgentMessage] = []
        self._lock = threading.Lock()
        self._thread_local = threading.local()
        self.max_delegation_depth = max_delegation_depth or settings.max_delegation_depth

    # ------------------------------------------------------------------
    # Agent registration
    # ------------------------------------------------------------------

    def register_agent(self, agent_id: str, agent: Any) -> None:
        """Register an agent instance with the bus."""
        self._agents[agent_id] = agent

    def register_all_agents(self, agents: dict[str, Any]) -> None:
        """Register multiple agent instances at once."""
        self._agents.update(agents)

    def set_orchestrator_route_fn(self, route_fn) -> None:
        """Set the orchestrator's routing function for master-mediated communication."""
        self._orchestrator_route_fn = route_fn

    def get_available_agents(self) -> list[str]:
        """Return list of registered agent IDs."""
        return list(self._agents.keys())

    # ------------------------------------------------------------------
    # Delegation depth tracking (per-thread)
    # ------------------------------------------------------------------

    def _get_depth(self) -> int:
        """Get the current delegation depth for the calling thread."""
        return getattr(self._thread_local, "depth", 0)

    def _set_depth(self, depth: int) -> None:
        """Set the delegation depth for the calling thread."""
        self._thread_local.depth = depth

    # ------------------------------------------------------------------
    # Message logging
    # ------------------------------------------------------------------

    def _log_message(self, msg: AgentMessage) -> None:
        """Thread-safe append to the message log."""
        with self._lock:
            self._message_log.append(msg)
        logger.info(
            "AgentBus [%s] %s → %s: %s",
            msg.message_type, msg.from_agent, msg.to_agent,
            msg.content[:100],
        )

    def get_message_log(self) -> list[AgentMessage]:
        """Return a copy of the full message log."""
        with self._lock:
            return list(self._message_log)

    def get_message_log_summary(self) -> list[dict[str, Any]]:
        """Return a serializable summary of all inter-agent messages."""
        with self._lock:
            return [
                {
                    "from": m.from_agent,
                    "to": m.to_agent,
                    "type": m.message_type,
                    "content_preview": m.content[:200],
                    "timestamp": m.timestamp,
                }
                for m in self._message_log
            ]

    def clear_log(self) -> None:
        """Clear the message log."""
        with self._lock:
            self._message_log.clear()

    # ------------------------------------------------------------------
    # Core communication methods
    # ------------------------------------------------------------------

    def delegate(
        self,
        from_agent_id: str,
        to_agent_id: str,
        task: str,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Direct delegation — one agent invokes another agent by ID.

        Args:
            from_agent_id: The ID of the agent making the request.
            to_agent_id: The ID of the agent to delegate to.
            task: The task description for the target agent.
            context: Optional context dict to pass along.

        Returns:
            The target agent's result as a string.

        Raises:
            DelegationDepthExceeded: If recursion depth exceeds the configured max.
            ValueError: If the target agent is not registered.
        """
        current_depth = self._get_depth()

        if current_depth >= self.max_delegation_depth:
            error_msg = (
                f"Delegation depth limit reached ({self.max_delegation_depth}). "
                f"Cannot delegate from '{from_agent_id}' to '{to_agent_id}'. "
                "This prevents infinite agent-to-agent recursion."
            )
            self._log_message(AgentMessage(
                from_agent=from_agent_id,
                to_agent=to_agent_id,
                message_type="delegation_blocked",
                content=error_msg,
            ))
            raise DelegationDepthExceeded(error_msg)

        target_agent = self._agents.get(to_agent_id)
        if not target_agent:
            available = ", ".join(self._agents.keys())
            raise ValueError(
                f"Agent '{to_agent_id}' not found. Available agents: {available}"
            )

        # Log the delegation request
        self._log_message(AgentMessage(
            from_agent=from_agent_id,
            to_agent=to_agent_id,
            message_type="delegation",
            content=task,
            metadata={"depth": current_depth + 1},
        ))

        # Increase depth for the target agent's execution
        self._set_depth(current_depth + 1)
        try:
            result = target_agent.invoke(task, context)
            result_text = result.get("result", str(result)) if isinstance(result, dict) else str(result)
        except Exception as e:
            result_text = f"Error during delegation to '{to_agent_id}': {type(e).__name__}: {e}"
            logger.error(result_text)
        finally:
            self._set_depth(current_depth)

        # Log the response
        self._log_message(AgentMessage(
            from_agent=to_agent_id,
            to_agent=from_agent_id,
            message_type="response",
            content=result_text[:500],
            metadata={"depth": current_depth + 1},
        ))

        return result_text

    def request_via_orchestrator(self, from_agent_id: str, task: str) -> str:
        """Master-mediated routing — agent requests the orchestrator to route a task.

        The orchestrator's routing function classifies the request and dispatches it
        to the most appropriate agent(s).

        Args:
            from_agent_id: The ID of the agent making the request.
            task: The task to route through the orchestrator.

        Returns:
            The orchestrator's combined result as a string.
        """
        current_depth = self._get_depth()

        if current_depth >= self.max_delegation_depth:
            error_msg = (
                f"Delegation depth limit reached ({self.max_delegation_depth}). "
                f"Cannot route from '{from_agent_id}' through orchestrator."
            )
            self._log_message(AgentMessage(
                from_agent=from_agent_id,
                to_agent="orchestrator",
                message_type="route_blocked",
                content=error_msg,
            ))
            raise DelegationDepthExceeded(error_msg)

        if not self._orchestrator_route_fn:
            return "Error: Orchestrator routing function not configured on the communication bus."

        self._log_message(AgentMessage(
            from_agent=from_agent_id,
            to_agent="orchestrator",
            message_type="route_request",
            content=task,
            metadata={"depth": current_depth + 1},
        ))

        self._set_depth(current_depth + 1)
        try:
            result = self._orchestrator_route_fn(task)
            result_text = result if isinstance(result, str) else str(result)
        except Exception as e:
            result_text = f"Error during orchestrator routing: {type(e).__name__}: {e}"
            logger.error(result_text)
        finally:
            self._set_depth(current_depth)

        self._log_message(AgentMessage(
            from_agent="orchestrator",
            to_agent=from_agent_id,
            message_type="route_response",
            content=result_text[:500],
            metadata={"depth": current_depth + 1},
        ))

        return result_text

    def broadcast(self, from_agent_id: str, message: str) -> None:
        """Broadcast a message from one agent to all others (logged, non-blocking)."""
        self._log_message(AgentMessage(
            from_agent=from_agent_id,
            to_agent="*",
            message_type="broadcast",
            content=message,
        ))
