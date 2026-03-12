"""Abstract base class for all specialist agents."""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage

from config.settings import settings

logger = logging.getLogger(__name__)

MAX_TOOL_ITERATIONS = 10
RETRY_ATTEMPTS = 2
RETRY_DELAY_SECONDS = 2


class BaseAgent(ABC):
    """Base class that all specialist agents must extend.

    Provides:
    - LLM initialization via GitHub Models API
    - Agentic tool-use loop that iterates until the LLM stops calling tools
    - Automatic retries on transient failures
    - Structured output with task descriptions, confidence, and metadata
    - Pre/post processing hooks for specialist agents
    """

    def __init__(self, agent_id: str, name: str, tools: list | None = None) -> None:
        self.agent_id = agent_id
        self.name = name
        self.tools = tools or []
        self._tool_map: dict[str, Any] = {t.name: t for t in self.tools}
        self._llm = ChatOpenAI(**settings.get_llm_kwargs())
        if self.tools:
            self._llm_with_tools = self._llm.bind_tools(self.tools)
        else:
            self._llm_with_tools = self._llm

    # ------------------------------------------------------------------
    # Abstract / hook methods
    # ------------------------------------------------------------------

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt that defines this agent's persona and behavior."""

    def pre_process(self, user_request: str, context: dict[str, Any] | None) -> dict[str, Any]:
        """Hook called before execution. Agents can enrich context or modify the request.

        Returns a dict with optional keys: enriched_context, modified_request.
        """
        return {}

    def post_process(self, result: str, user_request: str) -> str:
        """Hook called after execution. Agents can clean up, validate, or enrich the result."""
        return result

    # ------------------------------------------------------------------
    # Task description
    # ------------------------------------------------------------------

    def describe_task(self, user_request: str) -> str:
        """Generate a thorough, detailed description of what this agent will do for the given request."""
        description_prompt = (
            f"You are the {self.name} agent. A user has made the following request:\n\n"
            f'"{user_request}"\n\n'
            "Provide a thorough, detailed description of EXACTLY what you will do to address "
            "this request. Include:\n"
            "1. The specific steps you will take (be granular — list every sub-step)\n"
            "2. What aspects you will analyze, review, or generate\n"
            "3. What tools/data sources you will use\n"
            "4. What kind of output/deliverables the user can expect\n"
            "5. Edge cases, risks, or caveats you will watch for\n"
            "6. Any assumptions you are making\n\n"
            "Be specific and actionable — this description tells the user what work is being performed."
        )
        response = self._call_llm_with_retry([
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=description_prompt),
        ])
        return response.content

    # ------------------------------------------------------------------
    # Core execution with agentic tool loop
    # ------------------------------------------------------------------

    def invoke(self, user_request: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute this agent's task with full tool-use loop and return structured results.

        The agent will:
        1. Call pre_process() for context enrichment
        2. Generate a task description
        3. Enter an agentic loop: call LLM → execute tool calls → feed results back
        4. Call post_process() on the final result
        5. Generate a self-assessed confidence score
        """
        start_time = time.time()

        # --- Pre-processing ---
        pre = self.pre_process(user_request, context)
        effective_request = pre.get("modified_request", user_request)
        merged_context = {**(context or {}), **(pre.get("enriched_context", {}))}

        # --- Task description ---
        task_description = self.describe_task(effective_request)

        # --- Build execution prompt ---
        context_block = ""
        if merged_context:
            context_parts = []
            for key, value in merged_context.items():
                context_parts.append(f"### {key}\n```\n{value}\n```")
            context_block = "\n\n## Provided Context\n" + "\n\n".join(context_parts)

        execution_prompt = (
            f"## Task\n{effective_request}\n\n"
            f"## Your Plan\n{task_description}"
            f"{context_block}\n\n"
            "## Instructions\n"
            "Execute the task thoroughly. Use your tools to gather real data before drawing conclusions.\n"
            "- Call tools to read files, analyze code, inspect git state, etc. — do NOT guess.\n"
            "- After gathering data, provide a detailed, actionable, and well-structured response.\n"
            "- Cover every relevant detail — edge cases, caveats, specific line references.\n"
            "- End with a clear summary of findings and prioritized recommendations.\n"
        )

        # --- Agentic tool-use loop ---
        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=execution_prompt),
        ]

        final_text = ""
        iterations = 0

        while iterations < MAX_TOOL_ITERATIONS:
            iterations += 1
            response = self._call_llm_with_retry(messages, use_tools=True)
            messages.append(response)

            # If the model made tool calls, execute them and feed results back
            if hasattr(response, "tool_calls") and response.tool_calls:
                for tool_call in response.tool_calls:
                    tool_result = self._execute_tool_call(tool_call)
                    messages.append(ToolMessage(
                        content=tool_result,
                        tool_call_id=tool_call["id"],
                    ))
                # Accumulate any intermediate text
                if response.content:
                    final_text += response.content + "\n"
            else:
                # No more tool calls — this is the final response
                final_text = response.content
                break

        # --- Post-processing ---
        final_text = self.post_process(final_text, effective_request)

        elapsed = round(time.time() - start_time, 2)

        return self.format_output(
            task_description=task_description,
            result=final_text,
            status="success",
            metadata={
                "tool_iterations": iterations,
                "execution_time_seconds": elapsed,
            },
        )

    # ------------------------------------------------------------------
    # Tool execution
    # ------------------------------------------------------------------

    def _execute_tool_call(self, tool_call: dict) -> str:
        """Execute a single tool call and return the string result."""
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        tool_fn = self._tool_map.get(tool_name)
        if not tool_fn:
            return f"Error: Unknown tool '{tool_name}'. Available: {list(self._tool_map.keys())}"

        try:
            result = tool_fn.invoke(tool_args)
            # Truncate very large tool outputs to keep context manageable
            if isinstance(result, str) and len(result) > 30000:
                result = result[:30000] + f"\n\n... [TRUNCATED — output was {len(result)} chars]"
            return result
        except Exception as e:
            logger.warning("Tool %s raised %s: %s", tool_name, type(e).__name__, e)
            return f"Error executing tool '{tool_name}': {type(e).__name__}: {e}"

    # ------------------------------------------------------------------
    # LLM call with retry
    # ------------------------------------------------------------------

    def _call_llm_with_retry(self, messages: list, use_tools: bool = False) -> AIMessage:
        """Call the LLM with automatic retry on transient failures."""
        llm = self._llm_with_tools if use_tools else self._llm
        last_error = None

        for attempt in range(1, RETRY_ATTEMPTS + 1):
            try:
                return llm.invoke(messages)
            except Exception as e:
                last_error = e
                logger.warning(
                    "LLM call attempt %d/%d failed for %s: %s",
                    attempt, RETRY_ATTEMPTS, self.name, e,
                )
                if attempt < RETRY_ATTEMPTS:
                    time.sleep(RETRY_DELAY_SECONDS * attempt)

        raise RuntimeError(
            f"{self.name} agent: LLM call failed after {RETRY_ATTEMPTS} attempts. "
            f"Last error: {last_error}"
        )

    # ------------------------------------------------------------------
    # Output formatting
    # ------------------------------------------------------------------

    def format_output(
        self, task_description: str, result: str, status: str, metadata: dict | None = None,
    ) -> dict[str, Any]:
        """Format the agent's output into a consistent structure."""
        output = {
            "agent_id": self.agent_id,
            "agent_name": self.name,
            "task_description": task_description,
            "result": result,
            "status": status,
        }
        if metadata:
            output["metadata"] = metadata
        return output

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.agent_id}, name={self.name})>"
