"""Agent registry — metadata and discovery for all specialist agents."""

from dataclasses import dataclass


@dataclass
class AgentInfo:
    """Metadata for a registered agent."""

    name: str
    agent_id: str
    description: str
    capabilities: list[str]
    keywords: list[str]


AGENT_REGISTRY: list[AgentInfo] = [
    AgentInfo(
        name="Code Reviewer",
        agent_id="code_reviewer",
        description=(
            "Reviews code for quality, readability, and adherence to best practices. "
            "Checks for SOLID principles, DRY/KISS violations, naming conventions, "
            "error handling, and code style consistency."
        ),
        capabilities=[
            "Pull request review",
            "Code quality assessment",
            "SOLID/DRY/KISS analysis",
            "Naming convention checks",
            "Error handling review",
            "Style consistency validation",
        ],
        keywords=[
            "review", "code review", "pull request", "PR", "quality", "readability",
            "naming", "style", "conventions", "SOLID", "DRY", "KISS", "clean code",
        ],
    ),
    AgentInfo(
        name="Bug Analyzer",
        agent_id="bug_analyzer",
        description=(
            "Diagnoses bugs by analyzing code, stack traces, and error patterns. "
            "Performs root cause analysis and suggests targeted fixes with code examples."
        ),
        capabilities=[
            "Root cause analysis",
            "Stack trace parsing",
            "Error pattern recognition",
            "Reproduction step generation",
            "Fix suggestions with code",
        ],
        keywords=[
            "bug", "error", "exception", "crash", "fix", "debug", "trace",
            "stacktrace", "issue", "broken", "failing", "500", "404", "null",
        ],
    ),
    AgentInfo(
        name="Architecture",
        agent_id="architecture",
        description=(
            "Evaluates system architecture, design patterns, and structural decisions. "
            "Analyzes coupling, cohesion, dependency graphs, and scalability concerns."
        ),
        capabilities=[
            "Design pattern evaluation",
            "Dependency analysis",
            "Coupling/cohesion review",
            "Scalability assessment",
            "Technology stack recommendations",
            "Migration path planning",
        ],
        keywords=[
            "architecture", "design", "pattern", "structure", "scalability",
            "microservice", "monolith", "dependency", "coupling", "cohesion",
            "layer", "module", "component", "system design",
        ],
    ),
    AgentInfo(
        name="Testing",
        agent_id="testing",
        description=(
            "Designs test strategies, identifies coverage gaps, and generates test cases. "
            "Supports unit, integration, and E2E testing across frameworks."
        ),
        capabilities=[
            "Test strategy design",
            "Coverage gap analysis",
            "Unit test generation",
            "Integration test planning",
            "BDD scenario writing",
            "Test pyramid evaluation",
        ],
        keywords=[
            "test", "testing", "unit test", "integration", "coverage", "TDD", "BDD",
            "pytest", "junit", "selenium", "mock", "assertion", "test case",
        ],
    ),
    AgentInfo(
        name="Security",
        agent_id="security",
        description=(
            "Scans code for security vulnerabilities following OWASP Top 10. "
            "Reviews authentication, authorization, input validation, and dependency safety."
        ),
        capabilities=[
            "OWASP Top 10 scanning",
            "Dependency vulnerability audit",
            "Secrets detection",
            "Authentication/authorization review",
            "Input validation checks",
            "Security header analysis",
        ],
        keywords=[
            "security", "vulnerability", "OWASP", "XSS", "SQL injection", "CSRF",
            "authentication", "authorization", "secrets", "CVE", "exploit", "injection",
        ],
    ),
    AgentInfo(
        name="Documentation",
        agent_id="documentation",
        description=(
            "Generates and reviews technical documentation including READMEs, "
            "API docs, inline comments, changelogs, and architecture decision records."
        ),
        capabilities=[
            "README generation",
            "API documentation",
            "Inline comment review",
            "Changelog creation",
            "Architecture Decision Records (ADRs)",
            "Code documentation assessment",
        ],
        keywords=[
            "documentation", "docs", "README", "API docs", "comment", "changelog",
            "ADR", "javadoc", "docstring", "document", "explain", "describe",
        ],
    ),
    AgentInfo(
        name="Refactoring",
        agent_id="refactoring",
        description=(
            "Identifies code smells and suggests refactoring improvements. "
            "Detects complexity hotspots, dead code, and proposes structural improvements."
        ),
        capabilities=[
            "Code smell detection",
            "Complexity reduction",
            "Extract method/class suggestions",
            "Dead code identification",
            "Dependency injection improvements",
            "Before/after code examples",
        ],
        keywords=[
            "refactor", "refactoring", "code smell", "complexity", "simplify",
            "extract", "clean up", "improve", "dead code", "duplicate", "DRY",
        ],
    ),
    AgentInfo(
        name="DevOps/CI-CD",
        agent_id="devops",
        description=(
            "Reviews CI/CD pipelines, Dockerfiles, and deployment configurations. "
            "Optimizes build processes and evaluates infrastructure-as-code."
        ),
        capabilities=[
            "Pipeline review (GitHub Actions, Jenkins)",
            "Dockerfile analysis",
            "Deployment strategy evaluation",
            "Infrastructure-as-code review",
            "Build optimization",
            "Environment configuration",
        ],
        keywords=[
            "devops", "CI/CD", "pipeline", "docker", "deployment", "github actions",
            "jenkins", "kubernetes", "terraform", "build", "deploy", "infrastructure",
        ],
    ),
    AgentInfo(
        name="Performance",
        agent_id="performance",
        description=(
            "Identifies performance bottlenecks and optimization opportunities. "
            "Analyzes query efficiency, memory usage, caching strategies, and load handling."
        ),
        capabilities=[
            "Bottleneck identification",
            "Query optimization",
            "Memory leak detection",
            "Caching strategy design",
            "Load testing recommendations",
            "Algorithmic complexity analysis",
        ],
        keywords=[
            "performance", "slow", "bottleneck", "optimize", "cache", "memory",
            "latency", "throughput", "query", "N+1", "load", "speed", "fast",
        ],
    ),
]


class AgentRegistry:
    """Provides lookup and discovery of registered agents."""

    def __init__(self) -> None:
        self._agents = {agent.agent_id: agent for agent in AGENT_REGISTRY}

    def get(self, agent_id: str) -> AgentInfo | None:
        return self._agents.get(agent_id)

    def list_all(self) -> list[AgentInfo]:
        return list(self._agents.values())

    def get_ids(self) -> list[str]:
        return list(self._agents.keys())

    def get_registry_summary(self) -> str:
        """Return a formatted summary for the orchestrator's system prompt."""
        lines = []
        for agent in self._agents.values():
            caps = ", ".join(agent.capabilities)
            lines.append(f"- **{agent.name}** (id: `{agent.agent_id}`): {agent.description}\n  Capabilities: {caps}")
        return "\n".join(lines)
