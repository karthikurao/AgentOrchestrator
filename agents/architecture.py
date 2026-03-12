"""Architecture Agent — evaluates system design, patterns, and structural decisions."""

from typing import Any

from agents.base_agent import BaseAgent
from prompts.architecture_prompt import ARCHITECTURE_SYSTEM_PROMPT
from tools.file_tools import read_file, list_directory, read_multiple_files, search_in_files
from tools.code_analysis_tools import (
    find_imports, count_lines, analyze_complexity, find_function_definitions,
    detect_code_smells,
)


class ArchitectureAgent(BaseAgent):
    """Specialist agent for architecture evaluation and design recommendations.

    Performs holistic architectural analysis:
    - Dependency graph construction and circular dependency detection
    - Layer violation detection (presentation → data, etc.)
    - Coupling and cohesion metrics at module and package level
    - Design pattern identification and appropriateness evaluation
    - Single Responsibility analysis for classes and modules
    - API surface area assessment and contract consistency
    - Scalability bottleneck identification
    - Data flow and state management evaluation
    - Technology stack fitness assessment
    - Migration path planning with phased roadmaps
    """

    def __init__(self) -> None:
        super().__init__(
            agent_id="architecture",
            name="Architecture",
            tools=[
                read_file, list_directory, read_multiple_files, search_in_files,
                find_imports, count_lines, analyze_complexity,
                find_function_definitions, detect_code_smells,
            ],
        )

    def get_system_prompt(self) -> str:
        return ARCHITECTURE_SYSTEM_PROMPT

    def pre_process(self, user_request: str, context: dict[str, Any] | None) -> dict[str, Any]:
        return {
            "enriched_context": {
                "architecture_protocol": (
                    "1. List the full project directory tree (depth 3) to understand package structure. "
                    "2. Read key entry points (__init__.py, main.py, app.py). "
                    "3. Run find_imports on every module to build the dependency graph. "
                    "4. Identify circular dependencies and layer violations. "
                    "5. Run analyze_complexity to find God classes / overgrown modules. "
                    "6. Evaluate patterns in use vs. patterns that would improve the design. "
                    "7. Produce an ASCII architecture diagram of current and recommended state."
                ),
            }
        }
