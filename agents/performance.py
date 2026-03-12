"""Performance Agent — identifies bottlenecks and suggests optimizations."""

from typing import Any

from agents.base_agent import BaseAgent
from prompts.performance_prompt import PERFORMANCE_SYSTEM_PROMPT
from tools.code_analysis_tools import (
    analyze_complexity,
    count_lines,
    detect_code_smells,
    find_function_definitions,
    find_imports,
)
from tools.file_tools import list_directory, read_file, read_multiple_files, search_in_files
from tools.git_tools import git_diff, git_log


class PerformanceAgent(BaseAgent):
    """Specialist agent for performance analysis and optimization.

    Performs deep performance profiling:
    - Algorithmic complexity analysis (Big-O for every hot path)
    - Database query efficiency (N+1, missing indexes, full table scans)
    - Memory allocation patterns and leak detection
    - I/O bottlenecks (synchronous blocking, unbuffered reads)
    - Caching opportunity identification with TTL strategies
    - Concurrency and async optimization (thread pool sizing, event loop blocking)
    - Data structure selection (list vs. set vs. dict for lookups)
    - Loop optimization (unnecessary iterations, early termination)
    - Lazy loading and pagination opportunities
    - Resource pooling (connections, threads, file handles)
    """

    def __init__(self) -> None:
        super().__init__(
            agent_id="performance",
            name="Performance",
            tools=[
                read_file,
                read_multiple_files,
                list_directory,
                search_in_files,
                git_diff,
                git_log,
                analyze_complexity,
                count_lines,
                find_imports,
                find_function_definitions,
                detect_code_smells,
            ],
        )

    def get_system_prompt(self) -> str:
        return PERFORMANCE_SYSTEM_PROMPT

    def pre_process(self, user_request: str, context: dict[str, Any] | None) -> dict[str, Any]:
        return {
            "enriched_context": {
                "performance_protocol": (
                    "1. Read all target files and run analyze_complexity on each. "
                    "2. Identify functions with complexity > 5 as hotspot candidates. "
                    "3. Search for common perf anti-patterns: nested loops, repeated DB calls, "
                    "   synchronous I/O in async contexts, unbounded list growth. "
                    "4. Check imports for heavy libraries loaded unnecessarily. "
                    "5. Look for missing caching, connection pooling, or pagination. "
                    "6. Quantify each finding with Big-O and estimated impact. "
                    "7. Provide optimized code with before/after comparisons."
                ),
            }
        }
