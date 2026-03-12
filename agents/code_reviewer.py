"""Code Reviewer Agent — reviews code for quality, readability, and best practices."""

from typing import Any

from agents.base_agent import BaseAgent
from prompts.code_reviewer_prompt import CODE_REVIEWER_SYSTEM_PROMPT
from tools.code_analysis_tools import (
    analyze_complexity,
    analyze_type_hints,
    count_lines,
    detect_code_smells,
    find_function_definitions,
    find_imports,
)
from tools.file_tools import list_directory, read_file, read_multiple_files, search_in_files
from tools.git_tools import git_blame, git_diff, git_log, git_status


class CodeReviewerAgent(BaseAgent):
    """Specialist agent for code review and quality assessment.

    Performs deep, multi-dimensional code reviews covering:
    - Structural quality (SOLID, DRY, KISS, cohesion, coupling)
    - Logic correctness (control flow, boundary conditions, null safety)
    - Error handling completeness (exception paths, resource cleanup)
    - Naming and readability (consistency, descriptiveness)
    - Performance pitfalls (algorithmic complexity, unnecessary allocations)
    - Security surface (input validation, injection vectors)
    - Test adequacy (coverage gaps, missing edge-case tests)
    """

    def __init__(self) -> None:
        super().__init__(
            agent_id="code_reviewer",
            name="Code Reviewer",
            tools=[
                read_file,
                list_directory,
                read_multiple_files,
                search_in_files,
                git_diff,
                git_log,
                git_status,
                git_blame,
                analyze_complexity,
                count_lines,
                find_imports,
                detect_code_smells,
                find_function_definitions,
                analyze_type_hints,
            ],
        )

    def get_system_prompt(self) -> str:
        return CODE_REVIEWER_SYSTEM_PROMPT

    def pre_process(self, user_request: str, context: dict[str, Any] | None) -> dict[str, Any]:
        """Enrich context with a reminder to use tools for real data gathering."""
        return {
            "enriched_context": {
                "review_checklist": (
                    "1. Read every file mentioned or changed. "
                    "2. Run analyze_complexity and detect_code_smells on each. "
                    "3. Check git_diff for recent changes. "
                    "4. Inspect git_blame for high-churn areas. "
                    "5. Verify imports and type hints. "
                    "6. Cross-reference function signatures for consistency."
                ),
            }
        }

    def post_process(self, result: str, user_request: str) -> str:
        """Ensure the review ends with a severity-ordered summary."""
        if "## Summary" not in result and "### Summary" not in result:
            result += (
                "\n\n---\n### Review Summary\n"
                "_See above for the full categorized review with "
                "Critical / Warning / Suggestion / Positive findings._\n"
            )
        return result
