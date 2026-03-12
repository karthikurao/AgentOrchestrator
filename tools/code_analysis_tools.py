"""Code analysis tools for agents."""

import os
import re
from langchain_core.tools import tool


@tool
def analyze_complexity(file_path: str) -> str:
    """Analyze the cyclomatic complexity of a Python file using radon.

    Args:
        file_path: Path to the Python file to analyze.
    """
    try:
        from radon.complexity import cc_visit
        from radon.metrics import mi_visit

        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()

        # Cyclomatic complexity
        blocks = cc_visit(source)
        lines = ["## Cyclomatic Complexity Analysis", ""]
        for block in sorted(blocks, key=lambda b: b.complexity, reverse=True):
            rank = "A" if block.complexity <= 5 else "B" if block.complexity <= 10 else "C" if block.complexity <= 20 else "F"
            lines.append(
                f"- {block.name} (line {block.lineno}): "
                f"complexity={block.complexity} rank={rank}"
            )

        # Maintainability index
        mi_score = mi_visit(source, multi=False)
        mi_rank = "A" if mi_score > 19 else "B" if mi_score > 9 else "C"
        lines.append(f"\n## Maintainability Index: {mi_score:.1f} (rank {mi_rank})")

        return "\n".join(lines) if blocks else "No functions/classes found to analyze."
    except ImportError:
        return "Error: radon is not installed. Run: pip install radon"
    except FileNotFoundError:
        return f"Error: File not found: {file_path}"
    except Exception as e:
        return f"Error analyzing complexity: {e}"


@tool
def find_imports(file_path: str) -> str:
    """Find all import statements in a source file.

    Args:
        file_path: Path to the source file to analyze.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        imports = []
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith(("import ", "from ")):
                imports.append(f"  Line {i}: {stripped}")
            elif stripped.startswith(("using ", "require(", "const ")) and ("import" in stripped or "require" in stripped):
                imports.append(f"  Line {i}: {stripped}")
            elif stripped.startswith("#include"):
                imports.append(f"  Line {i}: {stripped}")

        if imports:
            return f"Found {len(imports)} import(s) in {file_path}:\n" + "\n".join(imports)
        return f"No imports found in {file_path}"
    except FileNotFoundError:
        return f"Error: File not found: {file_path}"
    except Exception as e:
        return f"Error finding imports: {e}"


@tool
def count_lines(file_path: str) -> str:
    """Count total lines, code lines, comment lines, and blank lines in a file.

    Args:
        file_path: Path to the file to analyze.
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        total = len(lines)
        blank = sum(1 for l in lines if not l.strip())
        comment = sum(1 for l in lines if l.strip().startswith(("#", "//", "/*", "*", "<!--")))
        code = total - blank - comment

        return (
            f"File: {file_path}\n"
            f"  Total lines:   {total}\n"
            f"  Code lines:    {code}\n"
            f"  Comment lines: {comment}\n"
            f"  Blank lines:   {blank}"
        )
    except FileNotFoundError:
        return f"Error: File not found: {file_path}"
    except Exception as e:
        return f"Error counting lines: {e}"
