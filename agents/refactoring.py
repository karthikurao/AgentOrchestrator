"""Refactoring Agent — identifies code smells and suggests improvements."""

from typing import Any

from agents.base_agent import BaseAgent
from prompts.refactoring_prompt import REFACTORING_SYSTEM_PROMPT
from tools.code_analysis_tools import (
    analyze_complexity,
    analyze_type_hints,
    count_lines,
    detect_code_smells,
    find_function_definitions,
    find_imports,
)
from tools.file_tools import list_directory, read_file, read_multiple_files, search_in_files
from tools.git_tools import git_blame, git_diff, git_log


class RefactoringAgent(BaseAgent):
    """Specialist agent for code refactoring and smell detection.

    Performs methodical refactoring analysis:
    - Full Martin Fowler code smell catalog detection
    - Cyclomatic complexity hotspot mapping
    - Dead code identification (unused imports, variables, functions, files)
    - Duplicate code detection across files
    - Extract Method / Extract Class opportunity identification
    - Replace Conditional with Polymorphism candidates
    - Dependency injection improvement opportunities
    - Type hint gap analysis
    - Naming consistency audit
    - Step-by-step refactoring plan with risk assessment
    """

    def __init__(self) -> None:
        super().__init__(
            agent_id="refactoring",
            name="Refactoring",
            tools=[
                read_file,
                list_directory,
                read_multiple_files,
                search_in_files,
                git_diff,
                git_log,
                git_blame,
                analyze_complexity,
                find_imports,
                count_lines,
                find_function_definitions,
                detect_code_smells,
                analyze_type_hints,
            ],
        )

    def get_system_prompt(self) -> str:
        return REFACTORING_SYSTEM_PROMPT

    def pre_process(self, user_request: str, context: dict[str, Any] | None) -> dict[str, Any]:
        return {
            "enriched_context": {
                "refactoring_protocol": (
                    "1. Read all target files completely. "
                    "2. Run detect_code_smells and analyze_complexity on each file. "
                    "3. Run find_function_definitions to map the full API surface. "
                    "4. Run analyze_type_hints to find type annotation gaps. "
                    "5. Use search_in_files to find duplicate code patterns. "
                    "6. Check git_blame for high-churn areas (refactoring candidates). "
                    "7. Produce a prioritized refactoring plan with before/after code. "
                    "8. Classify each refactoring by risk level (safe / needs-tests / risky)."
                ),
            }
        }
