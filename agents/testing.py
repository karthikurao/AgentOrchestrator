"""Testing Agent — designs test strategies, identifies gaps, generates test cases."""

from typing import Any

from agents.base_agent import BaseAgent
from prompts.testing_prompt import TESTING_SYSTEM_PROMPT
from tools.file_tools import read_file, list_directory, read_multiple_files, search_in_files
from tools.code_analysis_tools import (
    analyze_complexity, count_lines, find_imports, find_function_definitions,
    detect_code_smells,
)


class TestingAgent(BaseAgent):
    """Specialist agent for test strategy and test case generation.

    Performs comprehensive test engineering:
    - Test pyramid analysis (unit / integration / E2E balance)
    - Coverage gap identification by tracing all code paths
    - Edge case and boundary condition enumeration
    - Negative test case generation (invalid inputs, error paths)
    - Mock/stub strategy for external dependencies
    - Parameterized test design for combinatorial coverage
    - Regression test suite creation
    - Performance test scenario design
    - Test data factory / fixture generation
    - Mutation testing recommendations
    """

    def __init__(self) -> None:
        super().__init__(
            agent_id="testing",
            name="Testing",
            tools=[
                read_file, list_directory, read_multiple_files, search_in_files,
                analyze_complexity, count_lines, find_imports,
                find_function_definitions, detect_code_smells,
            ],
        )

    def get_system_prompt(self) -> str:
        return TESTING_SYSTEM_PROMPT

    def pre_process(self, user_request: str, context: dict[str, Any] | None) -> dict[str, Any]:
        return {
            "enriched_context": {
                "test_design_protocol": (
                    "1. Read the source file(s) to understand all functions and branches. "
                    "2. Run find_function_definitions to enumerate every testable unit. "
                    "3. Run analyze_complexity to identify high-complexity functions needing more tests. "
                    "4. List the tests/ directory and read existing tests. "
                    "5. Identify coverage gaps: untested functions, missing edge cases, no error-path tests. "
                    "6. Generate complete, runnable test code with descriptive names. "
                    "7. Include parameterized tests for functions with multiple input scenarios. "
                    "8. Include mock/patch setup for external dependencies."
                ),
            }
        }
