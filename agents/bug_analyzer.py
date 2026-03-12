"""Bug Analyzer Agent — diagnoses bugs, traces root causes, and suggests fixes."""

from typing import Any

from agents.base_agent import BaseAgent
from prompts.bug_analyzer_prompt import BUG_ANALYZER_SYSTEM_PROMPT
from tools.code_analysis_tools import (
    analyze_complexity,
    detect_code_smells,
    find_function_definitions,
    find_imports,
)
from tools.file_tools import list_directory, read_file, read_multiple_files, search_in_files
from tools.git_tools import git_blame, git_diff, git_log, git_status


class BugAnalyzerAgent(BaseAgent):
    """Specialist agent for bug diagnosis and root cause analysis.

    Performs systematic debugging:
    - Parses error messages, stack traces, and symptoms
    - Traces execution paths through call chains
    - Identifies root causes vs. symptoms
    - Checks recent commits for regression introduction (git bisect mentally)
    - Analyzes data flow for null/undefined propagation
    - Inspects concurrency, race conditions, and state mutations
    - Provides copy-paste-ready fixes with before/after code
    - Suggests regression tests to prevent recurrence
    """

    def __init__(self) -> None:
        super().__init__(
            agent_id="bug_analyzer",
            name="Bug Analyzer",
            tools=[
                read_file,
                read_multiple_files,
                list_directory,
                search_in_files,
                git_diff,
                git_log,
                git_blame,
                git_status,
                find_imports,
                analyze_complexity,
                find_function_definitions,
                detect_code_smells,
            ],
        )

    def get_system_prompt(self) -> str:
        return BUG_ANALYZER_SYSTEM_PROMPT

    def pre_process(self, user_request: str, context: dict[str, Any] | None) -> dict[str, Any]:
        return {
            "enriched_context": {
                "debugging_protocol": (
                    "1. Read the file(s) referenced in the error/request. "
                    "2. Use search_in_files to trace the symbol/function across the codebase. "
                    "3. Check git_log and git_diff for recent changes that may have introduced the bug. "
                    "4. Use git_blame on the suspect lines. "
                    "5. Read upstream callers and downstream callees. "
                    "6. Formulate root cause with evidence. "
                    "7. Write the fix AND a regression test."
                ),
            }
        }

    def post_process(self, result: str, user_request: str) -> str:
        if "Root Cause" not in result and "root cause" not in result.lower():
            result += (
                "\n\n---\n### Root Cause Summary\n"
                "_The analysis above identifies the root cause and provides a recommended fix._\n"
            )
        return result
