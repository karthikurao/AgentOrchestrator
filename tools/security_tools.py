"""Security-focused analysis tools for exploit detection and vulnerability scanning."""

import os
import re

from langchain_core.tools import tool

# ---------------------------------------------------------------------------
# Patterns used by multiple tools
# ---------------------------------------------------------------------------

_SECRET_PATTERNS: list[tuple[str, str]] = [
    (r"""(?i)(?:password|passwd|pwd)\s*[=:]\s*['"][^'"]{4,}['"]""", "Hardcoded password"),
    (r"""(?i)(?:api[_-]?key|apikey)\s*[=:]\s*['"][^'"]{8,}['"]""", "Hardcoded API key"),
    (r"""(?i)(?:secret|secret[_-]?key)\s*[=:]\s*['"][^'"]{8,}['"]""", "Hardcoded secret"),
    (r"""(?i)(?:token|auth[_-]?token|access[_-]?token|bearer)\s*[=:]\s*['"][^'"]{8,}['"]""", "Hardcoded token"),
    (r"""(?i)(?:private[_-]?key)\s*[=:]\s*['"][^'"]{8,}['"]""", "Hardcoded private key"),
    (r"""-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----""", "Embedded private key"),
    (r"""(?i)(?:aws[_-]?access[_-]?key[_-]?id)\s*[=:]\s*['"]?[A-Z0-9]{16,}""", "AWS access key ID"),
    (r"""(?i)(?:aws[_-]?secret[_-]?access[_-]?key)\s*[=:]\s*['"]?[A-Za-z0-9/+=]{30,}""", "AWS secret key"),
    (r"""(?i)(?:connection[_-]?string|conn[_-]?str)\s*[=:]\s*['"][^'"]{10,}['"]""", "Hardcoded connection string"),
    (r"""(?i)(?:database[_-]?url|db[_-]?url|db[_-]?uri)\s*[=:]\s*['"][^'"]{10,}['"]""", "Hardcoded database URL"),
    (r"""ghp_[A-Za-z0-9]{36}""", "GitHub personal access token"),
    (r"""gho_[A-Za-z0-9]{36}""", "GitHub OAuth token"),
    (r"""sk-[A-Za-z0-9]{20,}""", "OpenAI API key"),
    (r"""xox[bpors]-[A-Za-z0-9-]{10,}""", "Slack token"),
]

_INJECTION_PATTERNS: list[tuple[str, str, str]] = [
    # SQL injection sinks
    (r"""(?:execute|executemany|raw)\s*\(.*?[%f]['"]""", "SQL Injection", "CWE-89"),
    (r"""(?:cursor\.execute|\.query)\s*\(\s*f['"]""", "SQL Injection (f-string)", "CWE-89"),
    (r"""(?:cursor\.execute|\.query)\s*\(.*?%\s""", "SQL Injection (% format)", "CWE-89"),
    (r"""\.format\s*\(.*?\).*?(?:execute|query)""", "SQL Injection (.format)", "CWE-89"),
    (r"""(?i)text\s*\(\s*f['"].*?(?:SELECT|INSERT|UPDATE|DELETE|DROP)""", "SQL Injection (SQLAlchemy text)", "CWE-89"),
    # Command injection sinks
    (
        r"""subprocess\.(?:call|run|Popen|check_output)\s*\(.*?(?:shell\s*=\s*True)""",
        "Command Injection (shell=True)",
        "CWE-78",
    ),
    (r"""os\.(?:system|popen)\s*\(""", "OS Command Injection", "CWE-78"),
    (r"""os\.(?:system|popen)\s*\(.*?f['"]""", "OS Command Injection (f-string)", "CWE-78"),
    # XSS sinks
    (r"""(?:innerHTML|outerHTML|document\.write)\s*[=(]""", "DOM XSS Sink", "CWE-79"),
    (r"""\|\s*safe\b""", "Template XSS (|safe filter)", "CWE-79"),
    (r"""Markup\s*\(.*?f['"]""", "Template XSS (Markup f-string)", "CWE-79"),
    (r"""render_template_string\s*\(""", "SSTI / XSS (render_template_string)", "CWE-79"),
    # LDAP injection
    (r"""(?:ldap|ldap3).*?(?:search|modify|add)\s*\(.*?f['"]""", "LDAP Injection", "CWE-90"),
    # XPath injection
    (r"""xpath\s*\(.*?f['"]""", "XPath Injection", "CWE-643"),
    # Eval / exec
    (r"""\beval\s*\(""", "Code Injection (eval)", "CWE-94"),
    (r"""\bexec\s*\(""", "Code Injection (exec)", "CWE-94"),
    (r"""\bcompile\s*\(.*?,\s*['"]exec['"]""", "Code Injection (compile+exec)", "CWE-94"),
]

_UNSAFE_DESER_PATTERNS: list[tuple[str, str, str]] = [
    (r"""pickle\.(?:load|loads)\s*\(""", "Pickle deserialization", "CWE-502"),
    (r"""cPickle\.(?:load|loads)\s*\(""", "cPickle deserialization", "CWE-502"),
    (r"""shelve\.open\s*\(""", "Shelve deserialization", "CWE-502"),
    (r"""marshal\.(?:load|loads)\s*\(""", "Marshal deserialization", "CWE-502"),
    (r"""yaml\.load\s*\((?!.*Loader\s*=\s*(?:yaml\.)?SafeLoader)""", "Unsafe YAML load (no SafeLoader)", "CWE-502"),
    (r"""yaml\.unsafe_load\s*\(""", "Explicit unsafe YAML load", "CWE-502"),
    (r"""jsonpickle\.(?:decode|loads)\s*\(""", "jsonpickle deserialization", "CWE-502"),
    (r"""dill\.(?:load|loads)\s*\(""", "Dill deserialization", "CWE-502"),
    (r"""cloudpickle\.(?:load|loads)\s*\(""", "cloudpickle deserialization", "CWE-502"),
    (r"""torch\.load\s*\((?!.*weights_only\s*=\s*True)""", "PyTorch load (RCE via pickle)", "CWE-502"),
    (r"""unserialize\s*\(""", "PHP-style unserialize", "CWE-502"),
    (r"""ObjectInputStream""", "Java ObjectInputStream deserialization", "CWE-502"),
    (r"""readObject\s*\(""", "Java readObject deserialization", "CWE-502"),
]

_CRYPTO_WEAK_PATTERNS: list[tuple[str, str, str]] = [
    (r"""(?i)hashlib\.md5\s*\(""", "Weak hash: MD5", "CWE-328"),
    (r"""(?i)hashlib\.sha1\s*\(""", "Weak hash: SHA-1", "CWE-328"),
    (r"""(?i)MD5\s*\(""", "Weak hash: MD5", "CWE-328"),
    (r"""(?i)SHA1\s*\(""", "Weak hash: SHA-1", "CWE-328"),
    (r"""(?i)DES\b""", "Weak cipher: DES", "CWE-327"),
    (r"""(?i)RC4\b""", "Weak cipher: RC4", "CWE-327"),
    (r"""(?i)Blowfish\b""", "Weak cipher: Blowfish", "CWE-327"),
    (r"""(?i)ECB\b""", "Insecure mode: ECB", "CWE-327"),
    (r"""random\.(?:random|randint|choice|randrange)\s*\(""", "Insecure PRNG for security context", "CWE-338"),
    (r"""(?i)(?:verify\s*=\s*False|CERT_NONE)""", "SSL verification disabled", "CWE-295"),
    (r"""(?i)(?:check_hostname\s*=\s*False)""", "Hostname verification disabled", "CWE-295"),
]

_PATH_TRAVERSAL_PATTERNS: list[tuple[str, str, str]] = [
    (r"""open\s*\(.*?(?:request\.|user_|input|param|arg|query)""", "User-controlled file open", "CWE-22"),
    (r"""os\.path\.join\s*\(.*?(?:request\.|user_|input|param|arg|query)""", "User-controlled path join", "CWE-22"),
    (r"""send_file\s*\(.*?(?:request\.|user_|input|param|arg|query)""", "User-controlled send_file", "CWE-22"),
    (r"""send_from_directory\s*\(""", "send_from_directory (verify safe usage)", "CWE-22"),
    (r"""os\.path\.join\s*\((?!.*os\.path\.abspath|.*secure_filename)""", "Path join without sanitization", "CWE-22"),
    (
        r"""shutil\.(?:copy|move|rmtree)\s*\(.*?(?:request\.|user_|input|param)""",
        "User-controlled file operation",
        "CWE-22",
    ),
    (r"""(?:\.\./)""", "Relative path traversal pattern", "CWE-22"),
    (r"""redirect\s*\(.*?(?:request\.|user_|input|param|url|next)""", "Open redirect", "CWE-601"),
]


def _scan_files(
    directory: str,
    patterns: list[tuple[str, str, str]] | list[tuple[str, str]],
    extensions: set[str] | None = None,
    max_matches: int = 300,
) -> list[dict[str, str]]:
    """Internal scanner that applies regex patterns across a directory."""
    if extensions is None:
        extensions = {
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".java",
            ".go",
            ".rs",
            ".rb",
            ".php",
            ".cs",
            ".yml",
            ".yaml",
            ".json",
            ".toml",
            ".cfg",
            ".ini",
            ".env",
            ".sh",
            ".bash",
            ".ps1",
            ".tf",
        }

    findings: list[dict[str, str]] = []
    skip_dirs = {
        "node_modules",
        "__pycache__",
        "venv",
        ".venv",
        ".git",
        ".tox",
        "dist",
        "build",
        ".mypy_cache",
        ".pytest_cache",
        ".eggs",
    }

    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in skip_dirs]
        for fname in files:
            if not any(fname.endswith(ext) for ext in extensions):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, encoding="utf-8", errors="replace") as f:
                    for line_num, line in enumerate(f, 1):
                        for pattern_tuple in patterns:
                            regex_str = pattern_tuple[0]
                            label = pattern_tuple[1]
                            cwe = pattern_tuple[2] if len(pattern_tuple) > 2 else ""
                            if re.search(regex_str, line):
                                rel_path = os.path.relpath(fpath, directory)
                                findings.append(
                                    {
                                        "file": rel_path,
                                        "line": str(line_num),
                                        "code": line.strip()[:120],
                                        "finding": label,
                                        "cwe": cwe,
                                    }
                                )
                                if len(findings) >= max_matches:
                                    return findings
            except (PermissionError, OSError):
                continue
    return findings


def _format_findings(findings: list[dict[str, str]], title: str, directory: str) -> str:
    """Format scan findings into a structured report."""
    if not findings:
        return f"✅ {title}: No issues found in {directory}"

    lines = [f"## {title}", f"Found **{len(findings)}** potential issue(s) in `{directory}`:\n"]

    for i, f in enumerate(findings, 1):
        cwe_ref = f" ({f['cwe']})" if f.get("cwe") else ""
        lines.append(
            f"  {i}. 🔴 **{f['finding']}**{cwe_ref}\n"
            f"     📍 `{f['file']}:{f['line']}`\n"
            f"     ```\n     {f['code']}\n     ```"
        )
    return "\n".join(lines)


# ===================================================================
# Public tools
# ===================================================================


@tool
def scan_for_secrets(directory: str) -> str:
    """Scan a directory recursively for hardcoded secrets, credentials, API keys, and tokens.

    Detects: passwords, API keys, tokens, private keys, AWS credentials, GitHub tokens,
    OpenAI keys, Slack tokens, database URLs, connection strings, and more.

    Args:
        directory: Root directory to scan for secrets.
    """
    secret_patterns = [(p, label) for p, label in _SECRET_PATTERNS]
    findings = _scan_files(directory, secret_patterns)
    return _format_findings(findings, "Secrets & Credentials Scan", directory)


@tool
def detect_injection_sinks(directory: str) -> str:
    """Detect potential injection vulnerabilities: SQL injection, command injection, XSS,
    LDAP injection, XPath injection, eval/exec code injection, and SSTI.

    Searches for patterns where user-controlled input flows into dangerous sinks
    without proper sanitization or parameterization.

    Args:
        directory: Root directory to scan for injection sinks.
    """
    findings = _scan_files(directory, _INJECTION_PATTERNS)
    return _format_findings(findings, "Injection Vulnerability Scan", directory)


@tool
def analyze_attack_surface(directory: str) -> str:
    """Map the application's attack surface by identifying all entry points.

    Discovers: HTTP route handlers, API endpoints, CLI argument parsers,
    file upload handlers, WebSocket handlers, GraphQL resolvers,
    form handlers, and authentication endpoints.

    Args:
        directory: Root directory to analyze for entry points.
    """
    entry_point_patterns: list[tuple[str, str, str]] = [
        # Flask / FastAPI / Django routes
        (r"""@(?:app|router|blueprint)\.(?:route|get|post|put|delete|patch|options)\s*\(""", "HTTP Route Handler", ""),
        (r"""@api_view\s*\(""", "Django REST API View", ""),
        (r"""path\s*\(\s*['"]""", "Django URL Pattern", ""),
        (r"""url\s*\(\s*r?['"]""", "Django URL Pattern (legacy)", ""),
        (r"""class\s+\w+(?:View|ViewSet|APIView|Mixin)""", "Class-Based View", ""),
        # Express.js / Node routes
        (r"""(?:app|router)\.(?:get|post|put|delete|patch|all|use)\s*\(""", "Express Route Handler", ""),
        # CLI / argument parsing
        (r"""(?:argparse|ArgumentParser|click\.command|typer\.command)""", "CLI Entry Point", ""),
        (r"""sys\.argv""", "Direct argv Access", ""),
        # File uploads
        (r"""(?:file|upload|multipart|FormData)""", "File Upload Handler", ""),
        (r"""request\.files""", "Flask File Upload", ""),
        # WebSocket
        (r"""(?:websocket|ws|socket\.io|socketio)""", "WebSocket Handler", ""),
        # GraphQL
        (r"""(?:graphql|Query|Mutation|Resolver|Schema)""", "GraphQL Endpoint", ""),
        # Authentication
        (r"""(?:login|signin|sign_in|authenticate|logout|signup|register|password_reset)""", "Auth Endpoint", ""),
        # Deserialization entry points
        (r"""(?:json\.loads|fromJSON|deserialize|unmarshal)\s*\(.*?request""", "Deserialization Entry", ""),
        # Middleware
        (r"""(?:middleware|before_request|after_request|before_action)""", "Middleware / Hook", ""),
    ]

    findings = _scan_files(directory, entry_point_patterns)

    if not findings:
        return f"No entry points discovered in {directory}. The project may not be a web application."

    lines = [
        "## Attack Surface Map",
        f"Discovered **{len(findings)}** entry point(s) in `{directory}`:\n",
    ]

    # Group by category
    categories: dict[str, list[dict[str, str]]] = {}
    for f in findings:
        cat = f["finding"]
        categories.setdefault(cat, []).append(f)

    for category, items in sorted(categories.items()):
        lines.append(f"### {category} ({len(items)} found)")
        for item in items:
            lines.append(f"  - `{item['file']}:{item['line']}` — `{item['code']}`")
        lines.append("")

    lines.append("### Attack Surface Summary")
    lines.append("| Category | Count |")
    lines.append("|----------|-------|")
    for category, items in sorted(categories.items(), key=lambda x: -len(x[1])):
        lines.append(f"| {category} | {len(items)} |")

    return "\n".join(lines)


@tool
def detect_unsafe_deserialization(directory: str) -> str:
    """Detect unsafe deserialization patterns that could lead to Remote Code Execution (RCE).

    Scans for: pickle.load, cPickle, shelve, marshal, unsafe YAML loading,
    jsonpickle, dill, cloudpickle, PyTorch load without weights_only,
    PHP unserialize, Java ObjectInputStream.

    Args:
        directory: Root directory to scan for unsafe deserialization.
    """
    findings = _scan_files(directory, _UNSAFE_DESER_PATTERNS)
    return _format_findings(findings, "Unsafe Deserialization Scan (RCE Risk)", directory)


@tool
def check_crypto_weaknesses(directory: str) -> str:
    """Detect weak cryptography usage, insecure random number generation, and SSL issues.

    Scans for: MD5/SHA-1 for security, DES/RC4/Blowfish, ECB mode, insecure PRNG
    (random module for security), disabled SSL verification, disabled hostname checks.

    Args:
        directory: Root directory to scan for cryptographic weaknesses.
    """
    findings = _scan_files(directory, _CRYPTO_WEAK_PATTERNS)
    return _format_findings(findings, "Cryptographic Weakness Scan", directory)


@tool
def detect_path_traversal(directory: str) -> str:
    """Detect potential path traversal and open redirect vulnerabilities.

    Scans for: user-controlled file operations, unsanitized path joins,
    send_file with user input, open redirects, and file system manipulation
    with external input.

    Args:
        directory: Root directory to scan for path traversal vulnerabilities.
    """
    findings = _scan_files(directory, _PATH_TRAVERSAL_PATTERNS)
    return _format_findings(findings, "Path Traversal & Open Redirect Scan", directory)
