"""Bug Analyzer Agent — diagnoses bugs, traces root causes, and suggests fixes."""

from agents.base_agent import BaseAgent
from prompts.bug_analyzer_prompt import BUG_ANALYZER_SYSTEM_PROMPT
from tools.file_tools import read_file, read_multiple_files
from tools.git_tools import git_diff, git_log, git_blame
from tools.code_analysis_tools import find_imports


class BugAnalyzerAgent(BaseAgent):
    """Specialist agent for bug diagnosis and root cause analysis."""

    def __init__(self) -> None:
        super().__init__(
            agent_id="bug_analyzer",
            name="Bug Analyzer",
            tools=[read_file, read_multiple_files, git_diff, git_log, git_blame, find_imports],
        )

    def get_system_prompt(self) -> str:
        return BUG_ANALYZER_SYSTEM_PROMPT
