"""Documentation Agent — generates and reviews technical documentation."""

from agents.base_agent import BaseAgent
from prompts.documentation_prompt import DOCUMENTATION_SYSTEM_PROMPT
from tools.file_tools import read_file, list_directory, read_multiple_files
from tools.code_analysis_tools import find_imports, count_lines


class DocumentationAgent(BaseAgent):
    """Specialist agent for documentation generation and review."""

    def __init__(self) -> None:
        super().__init__(
            agent_id="documentation",
            name="Documentation",
            tools=[read_file, list_directory, read_multiple_files, find_imports, count_lines],
        )

    def get_system_prompt(self) -> str:
        return DOCUMENTATION_SYSTEM_PROMPT
