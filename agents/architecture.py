"""Architecture Agent — evaluates system design, patterns, and structural decisions."""

from agents.base_agent import BaseAgent
from prompts.architecture_prompt import ARCHITECTURE_SYSTEM_PROMPT
from tools.file_tools import read_file, list_directory, read_multiple_files
from tools.code_analysis_tools import find_imports, count_lines


class ArchitectureAgent(BaseAgent):
    """Specialist agent for architecture evaluation and design recommendations."""

    def __init__(self) -> None:
        super().__init__(
            agent_id="architecture",
            name="Architecture",
            tools=[read_file, list_directory, read_multiple_files, find_imports, count_lines],
        )

    def get_system_prompt(self) -> str:
        return ARCHITECTURE_SYSTEM_PROMPT
