"""File system tools for agents."""

import os
import re
from langchain_core.tools import tool


@tool
def read_file(file_path: str) -> str:
    """Read the contents of a file and return it as a string.

    Args:
        file_path: Absolute or relative path to the file to read.
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        if len(content) > 50000:
            return content[:50000] + f"\n\n... [TRUNCATED — file is {len(content)} chars total]"
        return content
    except FileNotFoundError:
        return f"Error: File not found: {file_path}"
    except PermissionError:
        return f"Error: Permission denied: {file_path}"
    except Exception as e:
        return f"Error reading file: {e}"


@tool
def list_directory(directory_path: str, max_depth: int = 3) -> str:
    """List files and directories up to a specified depth.

    Args:
        directory_path: Path to the directory to list.
        max_depth: Maximum depth to recurse (default 3).
    """
    try:
        lines = []
        base_depth = directory_path.rstrip(os.sep).count(os.sep)
        for root, dirs, files in os.walk(directory_path):
            current_depth = root.rstrip(os.sep).count(os.sep) - base_depth
            if current_depth >= max_depth:
                dirs.clear()
                continue
            # Skip hidden and common noise directories
            dirs[:] = [d for d in sorted(dirs) if not d.startswith(".") and d not in {
                "node_modules", "__pycache__", "venv", ".venv", "target", "bin", "obj",
                ".git", ".tox", ".mypy_cache", ".pytest_cache", ".eggs", "dist", "build",
                "htmlcov", ".ruff_cache", "egg-info",
            }]
            indent = "  " * current_depth
            folder_name = os.path.basename(root) or root
            lines.append(f"{indent}{folder_name}/")
            file_indent = "  " * (current_depth + 1)
            for fname in sorted(files)[:100]:
                lines.append(f"{file_indent}{fname}")
        return "\n".join(lines) if lines else "Empty directory"
    except FileNotFoundError:
        return f"Error: Directory not found: {directory_path}"
    except Exception as e:
        return f"Error listing directory: {e}"


@tool
def read_multiple_files(file_paths: list[str]) -> str:
    """Read multiple files and return their contents concatenated with headers.

    Args:
        file_paths: List of file paths to read.
    """
    results = []
    for path in file_paths:
        results.append(f"=== {path} ===")
        results.append(read_file.invoke({"file_path": path}))
        results.append("")
    return "\n".join(results)


@tool
def search_in_files(directory: str, pattern: str, file_extensions: str = ".py,.js,.ts,.java,.go,.rs,.yml,.yaml,.json,.toml,.cfg,.ini,.md,.txt") -> str:
    """Search for a text pattern across all files in a directory (recursive grep).

    Returns matching lines with file paths and line numbers. Useful for tracing
    function calls, finding variable references, detecting hardcoded strings, etc.

    Args:
        directory: Root directory to search in.
        pattern: Text or regex pattern to search for (case-insensitive).
        file_extensions: Comma-separated list of file extensions to search (default: common code files).
    """
    try:
        extensions = set(ext.strip() for ext in file_extensions.split(","))
        regex = re.compile(pattern, re.IGNORECASE)
        matches = []
        files_searched = 0

        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in {
                "node_modules", "__pycache__", "venv", ".venv", ".git", ".tox",
                "dist", "build", ".mypy_cache", ".pytest_cache",
            }]
            for fname in files:
                if not any(fname.endswith(ext) for ext in extensions):
                    continue
                fpath = os.path.join(root, fname)
                files_searched += 1
                try:
                    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                        for line_num, line in enumerate(f, 1):
                            if regex.search(line):
                                rel_path = os.path.relpath(fpath, directory)
                                matches.append(f"  {rel_path}:{line_num}: {line.rstrip()}")
                                if len(matches) >= 200:
                                    matches.append(f"\n... [TRUNCATED — more than 200 matches. Searched {files_searched} files.]")
                                    return f"Found {len(matches)} matches for '{pattern}':\n" + "\n".join(matches)
                except (PermissionError, OSError):
                    continue

        if matches:
            return f"Found {len(matches)} match(es) for '{pattern}' across {files_searched} files:\n" + "\n".join(matches)
        return f"No matches found for '{pattern}' across {files_searched} files in {directory}"
    except Exception as e:
        return f"Error searching files: {e}"
