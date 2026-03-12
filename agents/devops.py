"""DevOps/CI-CD Agent — reviews pipelines, Dockerfiles, and deployment configs."""

from typing import Any

from agents.base_agent import BaseAgent
from prompts.devops_prompt import DEVOPS_SYSTEM_PROMPT
from tools.file_tools import read_file, list_directory, read_multiple_files, search_in_files
from tools.git_tools import git_status, git_log, git_diff
from tools.code_analysis_tools import find_imports, analyze_dependency_security


class DevOpsAgent(BaseAgent):
    """Specialist agent for CI/CD pipeline and DevOps review.

    Performs end-to-end DevOps auditing:
    - CI/CD pipeline analysis (GitHub Actions, Jenkins, GitLab CI, Azure DevOps)
    - Dockerfile review (multi-stage builds, layer optimization, security)
    - Docker Compose service orchestration review
    - Kubernetes manifest / Helm chart analysis
    - Infrastructure-as-Code review (Terraform, CloudFormation)
    - Build caching and parallelization optimization
    - Secret management and environment variable hygiene
    - Deployment strategy evaluation (blue-green, canary, rolling)
    - Monitoring, logging, and alerting integration
    - Dependency pinning and reproducibility assessment
    """

    def __init__(self) -> None:
        super().__init__(
            agent_id="devops",
            name="DevOps/CI-CD",
            tools=[
                read_file, list_directory, read_multiple_files, search_in_files,
                git_status, git_log, git_diff,
                find_imports, analyze_dependency_security,
            ],
        )

    def get_system_prompt(self) -> str:
        return DEVOPS_SYSTEM_PROMPT

    def pre_process(self, user_request: str, context: dict[str, Any] | None) -> dict[str, Any]:
        return {
            "enriched_context": {
                "devops_protocol": (
                    "1. List root directory for Dockerfile, docker-compose.yml, .github/workflows/. "
                    "2. Read every CI/CD config file, Dockerfile, and docker-compose.yml found. "
                    "3. Read requirements.txt / package.json for dependency management review. "
                    "4. Run analyze_dependency_security on dependency files. "
                    "5. Search for hardcoded secrets or env vars in pipeline configs. "
                    "6. Check for proper caching, artifact management, and parallelization. "
                    "7. Evaluate deployment strategy and rollback procedures. "
                    "8. Provide complete, copy-paste-ready optimized configs."
                ),
            }
        }
