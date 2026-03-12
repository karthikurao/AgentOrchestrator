"""Security Agent — scans for vulnerabilities and reviews security practices."""

from typing import Any

from agents.base_agent import BaseAgent
from prompts.security_prompt import SECURITY_SYSTEM_PROMPT
from tools.file_tools import read_file, list_directory, read_multiple_files, search_in_files
from tools.git_tools import git_status, git_diff, git_log
from tools.code_analysis_tools import (
    find_imports, find_function_definitions, detect_code_smells, analyze_dependency_security,
)


class SecurityAgent(BaseAgent):
    """Specialist agent for security vulnerability assessment.

    Performs comprehensive security auditing:
    - OWASP Top 10 vulnerability scanning (injection, XSS, CSRF, SSRF, etc.)
    - Authentication & authorization flow analysis
    - Secrets/credential detection in code and config files
    - Dependency CVE auditing (requirements.txt, package.json, etc.)
    - Input validation and output encoding checks
    - Cryptography usage review (weak algorithms, key management)
    - Security header and CORS configuration analysis
    - Privilege escalation and broken access control detection
    - Data exposure in logs, errors, and API responses
    """

    def __init__(self) -> None:
        super().__init__(
            agent_id="security",
            name="Security",
            tools=[
                read_file, list_directory, read_multiple_files, search_in_files,
                git_status, git_diff, git_log,
                find_imports, find_function_definitions, detect_code_smells,
                analyze_dependency_security,
            ],
        )

    def get_system_prompt(self) -> str:
        return SECURITY_SYSTEM_PROMPT

    def pre_process(self, user_request: str, context: dict[str, Any] | None) -> dict[str, Any]:
        return {
            "enriched_context": {
                "security_scan_protocol": (
                    "1. List the project structure to identify config files, env files, and entry points. "
                    "2. Read requirements.txt / package.json and run analyze_dependency_security. "
                    "3. Search for hardcoded secrets: search_in_files for 'password', 'secret', 'api_key', 'token'. "
                    "4. Search for SQL/command injection patterns: search_in_files for 'execute(', 'subprocess', 'eval(', 'exec('. "
                    "5. Read auth-related files and trace the authentication flow. "
                    "6. Check for input validation on all user-facing endpoints. "
                    "7. Inspect error handlers for data leakage. "
                    "8. Review CORS, CSP, and security headers if applicable."
                ),
            }
        }

    def post_process(self, result: str, user_request: str) -> str:
        if "Risk Level" not in result and "risk level" not in result.lower():
            result += (
                "\n\n---\n### Overall Risk Assessment\n"
                "_See the detailed findings above for the full vulnerability report._\n"
            )
        return result
