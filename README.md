# Cortex 🧠

A **parallel multi-agent orchestration system** with 10 specialized AI agents for software development and security analysis. Agents run concurrently and can communicate with each other.

## Architecture

```
                      ┌─────────────────────┐
                      │  Master Orchestrator │
                      └────────┬────────────┘
                               │
                     ┌─────────┴──────────┐
                     │ AgentCommunicationBus │
                     │ (thread-safe broker)  │
                     └─────────┬──────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                      │
   Priority Group 1      Priority Group 1       Priority Group 2
   (⚡ parallel)         (⚡ parallel)          (waits for group 1)
  ┌──────────┐          ┌──────────┐           ┌──────────┐
  │ Agent A  │◄────────►│ Agent B  │           │ Agent C  │
  └──────────┘  direct  └──────────┘           └──────────┘
       │          delegation                        │
       └──── can also delegate via master ──────────┘
```

### Execution Model

- **Priority-grouped parallelism** — Agents at the same priority level run concurrently using `ThreadPoolExecutor`
- **Barrier between groups** — Higher-priority groups complete before lower-priority groups start
- **Context passing** — Results from earlier groups are available as context for later groups
- **Inter-agent communication** — Any agent can delegate to any other agent during execution

## Agents

| # | Agent | Responsibility |
|---|-------|----------------|
| 1 | **Code Reviewer** | PR review, code quality, SOLID/DRY/KISS checks |
| 2 | **Bug Analyzer** | Root cause analysis, stack trace parsing, fix suggestions |
| 3 | **Architecture** | Design patterns, scalability, dependency analysis |
| 4 | **Testing** | Test strategies, coverage gaps, test case generation |
| 5 | **Security** | OWASP Top 10, vulnerability scanning, secrets detection |
| 6 | **Documentation** | README generation, API docs, inline comment review |
| 7 | **Refactoring** | Code smells, complexity reduction, dead code detection |
| 8 | **DevOps/CI-CD** | Pipeline review, Dockerfile analysis, deployment strategy |
| 9 | **Performance** | Bottleneck identification, query optimization, caching |
| 10 | **Exploit Analyzer** | Attack surface mapping, exploit chains, CVSS scoring, threat modeling |

## Parallel Execution

When the orchestrator routes a request to multiple agents, it groups them by priority and executes same-priority agents **in parallel**:

```
Request: "Review code quality and check for security issues"

  ⚡ Priority 1 (parallel):
     ├── Code Reviewer  ──┐
     └── Security Agent ──┤── both run concurrently
                          │
  → Priority 2 (sequential, waits for group 1):
     └── Exploit Analyzer ── runs after group 1 completes
```

### Parallel Settings

| Setting | Env Variable | Default | Description |
|---------|-------------|---------|-------------|
| Parallel execution | `PARALLEL_EXECUTION` | `true` | Enable/disable parallel agent execution |
| Max parallel agents | `MAX_PARALLEL_AGENTS` | `4` | Maximum concurrent agent threads |
| Max delegation depth | `MAX_DELEGATION_DEPTH` | `3` | Max inter-agent recursion depth |

## Inter-Agent Communication

Agents can communicate with each other during execution through two modes:

### 1. Direct Delegation
An agent directly invokes another specialist agent:
```
Code Reviewer → delegate_to_agent("security", "Check this auth code for SQL injection")
                → Security Agent executes and returns result
```

### 2. Master-Mediated Routing
An agent routes a task through the orchestrator for intelligent dispatch:
```
Bug Analyzer → request_via_orchestrator("Analyze performance of this database query")
               → Orchestrator classifies → dispatches to Performance Agent
```

### Recursion Protection
A configurable max delegation depth (default: 3) prevents infinite agent-to-agent loops. The `AgentCommunicationBus` tracks delegation depth per-thread.

## Exploit Analyzer — Offensive Security Features

The **Exploit Analyzer** agent (agent #10) performs offensive security analysis with:

- 🎯 **Attack Surface Mapping** — Discovers all entry points (routes, APIs, CLI, file uploads, WebSockets)
- 🔗 **Exploit Chain Construction** — Chains multiple low-severity findings into critical attack paths
- 📊 **CVSS v3.1 Scoring** — Calculates base scores for every finding (AV/AC/PR/UI/S/C/I/A)
- 🛡️ **STRIDE Threat Modeling** — Spoofing, Tampering, Repudiation, Information Disclosure, DoS, Elevation
- 💀 **Proof-of-Concept Scenarios** — Step-by-step attack descriptions for each exploitable finding
- 🔍 **Automated Scanning** — Injection sinks, unsafe deserialization, hardcoded secrets, weak crypto, path traversal
- 📋 **CWE/OWASP References** — Industry-standard vulnerability classification for every finding
- 🔧 **Defense-in-Depth Remediation** — Multi-layered fix recommendations

### Security Tools

| Tool | What It Detects |
|------|----------------|
| `scan_for_secrets` | Hardcoded passwords, API keys, tokens, private keys, AWS credentials |
| `detect_injection_sinks` | SQL injection, XSS, command injection, LDAP injection, SSTI, eval/exec |
| `analyze_attack_surface` | HTTP routes, API endpoints, CLI parsers, file uploads, WebSockets |
| `detect_unsafe_deserialization` | pickle, YAML.load, marshal, dill, jsonpickle — RCE vectors |
| `check_crypto_weaknesses` | MD5/SHA-1, DES/RC4, ECB mode, insecure PRNG, disabled SSL verification |
| `detect_path_traversal` | User-controlled file ops, unsanitized path joins, open redirects |

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate   # Windows
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure environment:
   ```bash
   copy .env.example .env
   # Edit .env with your GITHUB_TOKEN
   ```
4. (Optional) Configure parallel settings in `.env`:
   ```env
   PARALLEL_EXECUTION=true
   MAX_PARALLEL_AGENTS=4
   MAX_DELEGATION_DEPTH=3
   ```

## Usage

```bash
python -m cli.main
```

### Example Commands
```
> Review this pull request for code quality issues
> Analyze the bug in src/auth/login.py - users get 500 errors
> What design patterns should we use for the payment service?
> Generate unit tests for the UserService class
> Scan this project for security vulnerabilities
> Find exploitable vulnerabilities and build attack chains with CVSS scores
> Run a full exploit analysis on the authentication module
> Check for hardcoded secrets and injection sinks in the codebase
> Perform STRIDE threat modeling on our API endpoints
```

### Quick Exploit Scan
```bash
# From the CLI, use the /exploit shortcut:
> /exploit              # Scan current directory
> /exploit src/auth/    # Scan specific path
```

## Tech Stack
- **Python 3.11+** with LangChain + LangGraph
- **GitHub Copilot** via GitHub Models API
- **Rich** for terminal UI
- **ThreadPoolExecutor** for parallel agent execution
- **AgentCommunicationBus** for inter-agent messaging
