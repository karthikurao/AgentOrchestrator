# Agent Orchestrator 🤖

A multi-agent system with a master orchestrator controlling 9 specialized AI agents for software development tasks.

## Architecture

```
User Input (CLI)
       │
       ▼
┌─────────────────────┐
│  Orchestrator Agent  │  (Master — routes requests, aggregates responses)
└─────┬───────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────┐
│  Code Reviewer │ Bug Analyzer │ Architecture │ Testing  │
│  Security │ Documentation │ Refactoring │ DevOps │ Perf │
└─────────────────────────────────────────────────────────┘
```

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
```

## Tech Stack
- **Python 3.11+** with LangChain + LangGraph
- **GitHub Copilot** via GitHub Models API
- **Rich** for terminal UI
