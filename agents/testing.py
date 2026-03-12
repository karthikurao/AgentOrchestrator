"""Testing Agent — designs test strategies, identifies gaps, generates test cases."""

from agents.base_agent import BaseAgent
from prompts.testing_prompt import TESTING_SYSTEM_PROMPT
from tools.file_tools import read_file, list_directory, read_multiple_files
from tools.code_analysis_tools import analyze_complexity, count_lines


class TestingAgent(BaseAgent):
    """Specialist agent for test strategy and test case generation."""

    def __init__(self) -> None:
        super().__init__(
            agent_id="testing",
            name="Testing",
            tools=[read_file, list_directory, read_multiple_files, analyze_complexity, count_lines],
        )

    def get_system_prompt(self) -> str:
        return TESTING_SYSTEM_PROMPT
