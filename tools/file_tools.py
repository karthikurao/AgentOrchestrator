"""File system tools for agents."""

import os
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
def list_directory(directory_path: str, max_depth: int = 2) -> str:
    """List files and directories up to a specified depth.

    Args:
        directory_path: Path to the directory to list.
        max_depth: Maximum depth to recurse (default 2).
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
                "node_modules", "__pycache__", "venv", ".venv", "target", "bin", "obj"
            }]
            indent = "  " * current_depth
            folder_name = os.path.basename(root) or root
            lines.append(f"{indent}{folder_name}/")
            file_indent = "  " * (current_depth + 1)
            for fname in sorted(files)[:50]:
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
