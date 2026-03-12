"""DevOps/CI-CD Agent — reviews pipelines, Dockerfiles, and deployment configs."""

from agents.base_agent import BaseAgent
from prompts.devops_prompt import DEVOPS_SYSTEM_PROMPT
from tools.file_tools import read_file, list_directory, read_multiple_files
from tools.git_tools import git_status, git_log


class DevOpsAgent(BaseAgent):
    """Specialist agent for CI/CD pipeline and DevOps review."""

    def __init__(self) -> None:
        super().__init__(
            agent_id="devops",
            name="DevOps/CI-CD",
            tools=[read_file, list_directory, read_multiple_files, git_status, git_log],
        )

    def get_system_prompt(self) -> str:
        return DEVOPS_SYSTEM_PROMPT
