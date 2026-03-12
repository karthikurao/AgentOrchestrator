"""Performance Agent — identifies bottlenecks and suggests optimizations."""

from agents.base_agent import BaseAgent
from prompts.performance_prompt import PERFORMANCE_SYSTEM_PROMPT
from tools.file_tools import read_file, read_multiple_files
from tools.git_tools import git_diff
from tools.code_analysis_tools import analyze_complexity, count_lines


class PerformanceAgent(BaseAgent):
    """Specialist agent for performance analysis and optimization."""

    def __init__(self) -> None:
        super().__init__(
            agent_id="performance",
            name="Performance",
            tools=[read_file, read_multiple_files, git_diff, analyze_complexity, count_lines],
        )

    def get_system_prompt(self) -> str:
        return PERFORMANCE_SYSTEM_PROMPT
