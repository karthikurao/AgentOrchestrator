"""Documentation Agent — generates and reviews technical documentation."""

from typing import Any

from agents.base_agent import BaseAgent
from prompts.documentation_prompt import DOCUMENTATION_SYSTEM_PROMPT
from tools.file_tools import read_file, list_directory, read_multiple_files, search_in_files
from tools.git_tools import git_log, git_status
from tools.code_analysis_tools import (
    find_imports, count_lines, find_function_definitions, analyze_type_hints,
)


class DocumentationAgent(BaseAgent):
    """Specialist agent for documentation generation and review.

    Produces comprehensive, accurate documentation by:
    - Reading every source file to understand actual behavior (not guessing)
    - Extracting function/class signatures and type hints for API docs
    - Analyzing the dependency graph for architecture documentation
    - Reviewing git history for changelog generation
    - Generating usage examples derived from test files
    - Creating Mermaid diagrams for architecture and data flow
    - Writing in audience-appropriate language (developer / user / ops)
    - Ensuring examples are syntactically correct and runnable
    """

    def __init__(self) -> None:
        super().__init__(
            agent_id="documentation",
            name="Documentation",
            tools=[
                read_file, list_directory, read_multiple_files, search_in_files,
                git_log, git_status,
                find_imports, count_lines, find_function_definitions, analyze_type_hints,
            ],
        )

    def get_system_prompt(self) -> str:
        return DOCUMENTATION_SYSTEM_PROMPT

    def pre_process(self, user_request: str, context: dict[str, Any] | None) -> dict[str, Any]:
        return {
            "enriched_context": {
                "documentation_protocol": (
                    "1. List the full project tree to understand structure. "
                    "2. Read README.md (if exists) to assess current docs. "
                    "3. Read all source files to understand actual behavior. "
                    "4. Run find_function_definitions on key modules for API reference. "
                    "5. Run analyze_type_hints for accurate parameter documentation. "
                    "6. Read test files for usage example extraction. "
                    "7. Check git_log for recent changes to generate changelog entries. "
                    "8. Generate Mermaid diagrams where architecture is complex."
                ),
            }
        }
