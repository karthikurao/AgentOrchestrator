"""Security Agent — scans for vulnerabilities and reviews security practices."""

from agents.base_agent import BaseAgent
from prompts.security_prompt import SECURITY_SYSTEM_PROMPT
from tools.file_tools import read_file, list_directory, read_multiple_files
from tools.git_tools import git_status
from tools.code_analysis_tools import find_imports


class SecurityAgent(BaseAgent):
    """Specialist agent for security vulnerability assessment."""

    def __init__(self) -> None:
        super().__init__(
            agent_id="security",
            name="Security",
            tools=[read_file, list_directory, read_multiple_files, git_status, find_imports],
        )

    def get_system_prompt(self) -> str:
        return SECURITY_SYSTEM_PROMPT
