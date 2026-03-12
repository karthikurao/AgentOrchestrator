"""Git operation tools for agents."""

import subprocess

from langchain_core.tools import tool


def _run_git(args: list[str], cwd: str | None = None) -> str:
    """Run a git command and return its output."""
    try:
        result = subprocess.run(
            ["git", "--no-pager"] + args,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=30,
        )
        output = result.stdout.strip()
        if result.returncode != 0:
            error = result.stderr.strip()
            return f"Git error: {error}" if error else f"Git command failed with code {result.returncode}"
        return output if output else "(no output)"
    except FileNotFoundError:
        return "Error: git is not installed or not in PATH"
    except subprocess.TimeoutExpired:
        return "Error: git command timed out after 30 seconds"
    except Exception as e:
        return f"Error running git: {e}"


@tool
def git_diff(repo_path: str, target: str = "HEAD") -> str:
    """Get the git diff for a repository.

    Args:
        repo_path: Path to the git repository root.
        target: Diff target — e.g., 'HEAD', 'HEAD~1', a branch name, or a commit SHA.
    """
    return _run_git(["diff", target], cwd=repo_path)


@tool
def git_log(repo_path: str, max_count: int = 20) -> str:
    """Get recent git commit history.

    Args:
        repo_path: Path to the git repository root.
        max_count: Maximum number of commits to return (default 20).
    """
    return _run_git(
        ["log", f"--max-count={max_count}", "--oneline", "--graph", "--decorate"],
        cwd=repo_path,
    )


@tool
def git_blame(repo_path: str, file_path: str) -> str:
    """Get git blame for a specific file (shows who last modified each line).

    Args:
        repo_path: Path to the git repository root.
        file_path: Relative path to the file within the repository.
    """
    output = _run_git(["blame", "--line-porcelain", file_path], cwd=repo_path)
    if output.startswith("Git error") or output.startswith("Error"):
        return output
    # Simplify the porcelain output
    lines = []
    current_author = ""
    current_line = ""
    for line in output.split("\n"):
        if line.startswith("author "):
            current_author = line[7:]
        elif line.startswith("\t"):
            current_line = line[1:]
            lines.append(f"{current_author:20s} | {current_line}")
    return "\n".join(lines[:200]) if lines else output[:5000]


@tool
def git_status(repo_path: str) -> str:
    """Get the current git status (modified, staged, untracked files).

    Args:
        repo_path: Path to the git repository root.
    """
    return _run_git(["status", "--short"], cwd=repo_path)
