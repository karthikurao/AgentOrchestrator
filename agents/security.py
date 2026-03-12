"""Security Agent — scans for vulnerabilities and reviews security practices."""

from typing import Any

from agents.base_agent import BaseAgent
from prompts.security_prompt import SECURITY_SYSTEM_PROMPT
from tools.code_analysis_tools import (
    analyze_dependency_security,
    detect_code_smells,
    find_function_definitions,
    find_imports,
)
from tools.file_tools import list_directory, read_file, read_multiple_files, search_in_files
from tools.git_tools import git_diff, git_log, git_status
from tools.security_tools import (
    analyze_attack_surface,
    check_crypto_weaknesses,
    detect_injection_sinks,
    detect_path_traversal,
    detect_unsafe_deserialization,
    scan_for_secrets,
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
    - Automated injection sink detection (SQL, XSS, command, LDAP)
    - Unsafe deserialization scanning (pickle, YAML, eval — RCE vectors)
    - Path traversal and open redirect detection
    - Attack surface enumeration
    """

    def __init__(self) -> None:
        super().__init__(
            agent_id="security",
            name="Security",
            tools=[
                read_file,
                list_directory,
                read_multiple_files,
                search_in_files,
                git_status,
                git_diff,
                git_log,
                find_imports,
                find_function_definitions,
                detect_code_smells,
                analyze_dependency_security,
                # Exploit-oriented security tools
                scan_for_secrets,
                detect_injection_sinks,
                analyze_attack_surface,
                detect_unsafe_deserialization,
                check_crypto_weaknesses,
                detect_path_traversal,
            ],
        )

    def get_system_prompt(self) -> str:
        return SECURITY_SYSTEM_PROMPT

    def pre_process(self, user_request: str, context: dict[str, Any] | None) -> dict[str, Any]:
        return {
            "enriched_context": {
                "security_scan_protocol": (
                    "=== AUTOMATED SCANNING ===\n"
                    "1. Run scan_for_secrets on the project root to find hardcoded credentials.\n"
                    "2. Run detect_injection_sinks to find SQL/XSS/command injection points.\n"
                    "3. Run detect_unsafe_deserialization to find RCE-capable deserialization.\n"
                    "4. Run check_crypto_weaknesses to find weak hashing and broken crypto.\n"
                    "5. Run detect_path_traversal to find file system vulnerabilities.\n"
                    "6. Run analyze_attack_surface to map all entry points.\n"
                    "\n"
                    "=== MANUAL REVIEW ===\n"
                    "7. Read requirements.txt / package.json and run analyze_dependency_security.\n"
                    "8. Read auth-related files and trace the authentication flow.\n"
                    "9. Check for input validation on all user-facing endpoints.\n"
                    "10. Inspect error handlers for data leakage.\n"
                    "11. Review CORS, CSP, and security headers if applicable.\n"
                    "12. Check for privilege escalation and broken access control."
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
