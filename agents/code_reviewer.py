"""Code Reviewer Agent — reviews code for quality, readability, and best practices."""

from agents.base_agent import BaseAgent
from prompts.code_reviewer_prompt import CODE_REVIEWER_SYSTEM_PROMPT
from tools.file_tools import read_file, list_directory, read_multiple_files
from tools.git_tools import git_diff, git_log, git_status
from tools.code_analysis_tools import analyze_complexity, count_lines


class CodeReviewerAgent(BaseAgent):
    """Specialist agent for code review and quality assessment."""

    def __init__(self) -> None:
        super().__init__(
            agent_id="code_reviewer",
            name="Code Reviewer",
            tools=[read_file, list_directory, read_multiple_files, git_diff, git_log, git_status, analyze_complexity, count_lines],
        )

    def get_system_prompt(self) -> str:
        return CODE_REVIEWER_SYSTEM_PROMPT
