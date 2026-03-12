"""Refactoring Agent — identifies code smells and suggests improvements."""

from agents.base_agent import BaseAgent
from prompts.refactoring_prompt import REFACTORING_SYSTEM_PROMPT
from tools.file_tools import read_file, list_directory, read_multiple_files
from tools.git_tools import git_diff
from tools.code_analysis_tools import analyze_complexity, find_imports, count_lines


class RefactoringAgent(BaseAgent):
    """Specialist agent for code refactoring and smell detection."""

    def __init__(self) -> None:
        super().__init__(
            agent_id="refactoring",
            name="Refactoring",
            tools=[read_file, list_directory, read_multiple_files, git_diff, analyze_complexity, find_imports, count_lines],
        )

    def get_system_prompt(self) -> str:
        return REFACTORING_SYSTEM_PROMPT
