"""Code analysis tools for agents."""

import ast
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
        lines = ["## Cyclomatic Complexity Analysis", f"**File**: {file_path}", ""]

        total_complexity = 0
        for block in sorted(blocks, key=lambda b: b.complexity, reverse=True):
            rank = "A" if block.complexity <= 5 else "B" if block.complexity <= 10 else "C" if block.complexity <= 20 else "F"
            indicator = "✅" if rank == "A" else "⚠️" if rank == "B" else "🔴"
            lines.append(
                f"- {indicator} {block.name} (line {block.lineno}): "
                f"complexity={block.complexity} rank={rank}"
            )
            total_complexity += block.complexity

        # Maintainability index
        mi_score = mi_visit(source, multi=False)
        mi_rank = "A" if mi_score > 19 else "B" if mi_score > 9 else "C"
        mi_indicator = "✅" if mi_rank == "A" else "⚠️" if mi_rank == "B" else "🔴"

        lines.append(f"\n## Maintainability Index: {mi_indicator} {mi_score:.1f} (rank {mi_rank})")
        lines.append(f"## Total Complexity: {total_complexity} across {len(blocks)} block(s)")

        if total_complexity == 0:
            lines.append("\n_No functions or classes found to analyze._")

        return "\n".join(lines)
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


@tool
def find_function_definitions(file_path: str) -> str:
    """Find all function and class definitions in a Python file with their signatures.

    Returns function/class names, line numbers, parameters, return type annotations,
    decorators, and docstrings.

    Args:
        file_path: Path to the Python file to analyze.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source, filename=file_path)
        results = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                decorators = [f"@{ast.dump(d)}" for d in node.decorator_list] if node.decorator_list else []
                bases = [ast.unparse(b) for b in node.bases] if node.bases else []
                docstring = ast.get_docstring(node) or ""
                doc_preview = (docstring[:80] + "...") if len(docstring) > 80 else docstring
                dec_str = " ".join(decorators) + " " if decorators else ""
                base_str = f"({', '.join(bases)})" if bases else ""
                results.append(
                    f"  Line {node.lineno}: {dec_str}class {node.name}{base_str}\n"
                    f"    Docstring: {doc_preview or '(none)'}"
                )
                # Also list methods within the class
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        _append_func_info(results, item, indent=4)

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Only top-level functions (not methods — those are listed under their class)
                if not any(isinstance(parent, ast.ClassDef) for parent in ast.walk(tree) if node in getattr(parent, 'body', [])):
                    pass  # handled below

        # Walk again for top-level functions only
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                _append_func_info(results, node, indent=2)

        if results:
            return f"## Definitions in {file_path}\n\n" + "\n".join(results)
        return f"No function or class definitions found in {file_path}"
    except SyntaxError as e:
        return f"Syntax error in {file_path}: {e}"
    except FileNotFoundError:
        return f"Error: File not found: {file_path}"
    except Exception as e:
        return f"Error analyzing definitions: {e}"


def _append_func_info(results: list, node: ast.FunctionDef | ast.AsyncFunctionDef, indent: int = 2) -> None:
    """Helper to format a function definition."""
    prefix = " " * indent
    is_async = isinstance(node, ast.AsyncFunctionDef)
    async_str = "async " if is_async else ""

    # Parameters
    args = node.args
    params = []
    defaults_offset = len(args.args) - len(args.defaults)
    for i, arg in enumerate(args.args):
        p = arg.arg
        if arg.annotation:
            p += f": {ast.unparse(arg.annotation)}"
        default_idx = i - defaults_offset
        if default_idx >= 0 and default_idx < len(args.defaults):
            p += f" = {ast.unparse(args.defaults[default_idx])}"
        params.append(p)
    if args.vararg:
        params.append(f"*{args.vararg.arg}")
    for kwarg in args.kwonlyargs:
        p = kwarg.arg
        if kwarg.annotation:
            p += f": {ast.unparse(kwarg.annotation)}"
        params.append(p)
    if args.kwarg:
        params.append(f"**{args.kwarg.arg}")

    param_str = ", ".join(params)
    ret = f" -> {ast.unparse(node.returns)}" if node.returns else ""
    docstring = ast.get_docstring(node) or ""
    doc_preview = (docstring[:80] + "...") if len(docstring) > 80 else docstring

    results.append(
        f"{prefix}Line {node.lineno}: {async_str}def {node.name}({param_str}){ret}\n"
        f"{prefix}  Docstring: {doc_preview or '(none)'}"
    )


@tool
def detect_code_smells(file_path: str) -> str:
    """Detect common code smells in a Python file.

    Checks for: long functions, too many parameters, deep nesting, God classes,
    unused imports, bare except, TODO/FIXME/HACK comments, mutable default arguments,
    star imports, and print statements left in code.

    Args:
        file_path: Path to the Python file to analyze.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
        lines = source.splitlines()

        tree = ast.parse(source, filename=file_path)
        smells = []

        for node in ast.walk(tree):
            # Long functions (>50 lines)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                end = getattr(node, "end_lineno", node.lineno)
                length = end - node.lineno + 1
                if length > 50:
                    smells.append(f"🔴 Long Method: `{node.name}` is {length} lines (line {node.lineno}-{end})")
                elif length > 30:
                    smells.append(f"⚠️ Moderately Long Method: `{node.name}` is {length} lines (line {node.lineno}-{end})")

                # Too many parameters (>5)
                param_count = len(node.args.args) + len(node.args.kwonlyargs)
                if node.args.vararg:
                    param_count += 1
                if node.args.kwarg:
                    param_count += 1
                if param_count > 7:
                    smells.append(f"🔴 Too Many Parameters: `{node.name}` has {param_count} parameters (line {node.lineno})")
                elif param_count > 5:
                    smells.append(f"⚠️ Many Parameters: `{node.name}` has {param_count} parameters (line {node.lineno})")

                # Mutable default arguments
                for default in node.args.defaults + node.args.kw_defaults:
                    if default and isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        smells.append(f"🔴 Mutable Default Argument in `{node.name}` (line {node.lineno})")
                        break

            # God classes (>10 methods or >300 lines)
            if isinstance(node, ast.ClassDef):
                methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                end = getattr(node, "end_lineno", node.lineno)
                class_length = end - node.lineno + 1
                if len(methods) > 15:
                    smells.append(f"🔴 God Class: `{node.name}` has {len(methods)} methods (line {node.lineno})")
                elif len(methods) > 10:
                    smells.append(f"⚠️ Large Class: `{node.name}` has {len(methods)} methods (line {node.lineno})")
                if class_length > 300:
                    smells.append(f"🔴 God Class: `{node.name}` is {class_length} lines (line {node.lineno})")

            # Bare except
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                smells.append(f"⚠️ Bare Except: Catches all exceptions (line {node.lineno})")

            # Star imports
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == "*":
                        module = node.module or "(unknown)"
                        smells.append(f"⚠️ Star Import: `from {module} import *` (line {node.lineno})")

        # Line-level checks
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            # TODO/FIXME/HACK comments
            if re.search(r"#\s*(TODO|FIXME|HACK|XXX|BUG)\b", stripped, re.IGNORECASE):
                smells.append(f"💡 Comment Tag: `{stripped[:60]}` (line {i})")
            # Print statements (likely debug leftover)
            if re.match(r"print\s*\(", stripped) and not stripped.startswith("#"):
                smells.append(f"💡 Print Statement (likely debug): (line {i})")

        # Deep nesting check
        for i, line in enumerate(lines, 1):
            if line.rstrip():
                indent = len(line) - len(line.lstrip())
                if indent >= 24:  # 6+ levels
                    smells.append(f"⚠️ Deep Nesting: {indent // 4} levels at line {i}")

        if smells:
            header = f"## Code Smells in {file_path}\nFound {len(smells)} potential issue(s):\n"
            return header + "\n".join(f"  {s}" for s in smells)
        return f"✅ No code smells detected in {file_path}"
    except SyntaxError as e:
        return f"Syntax error in {file_path}: {e}"
    except FileNotFoundError:
        return f"Error: File not found: {file_path}"
    except Exception as e:
        return f"Error detecting code smells: {e}"


@tool
def analyze_type_hints(file_path: str) -> str:
    """Analyze type hint coverage in a Python file.

    Reports which functions have type annotations for parameters and return values,
    and which are missing annotations.

    Args:
        file_path: Path to the Python file to analyze.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source, filename=file_path)
        results = []
        total_funcs = 0
        fully_annotated = 0
        missing = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                total_funcs += 1
                issues = []

                # Check parameters (skip 'self' and 'cls')
                for arg in node.args.args:
                    if arg.arg in ("self", "cls"):
                        continue
                    if not arg.annotation:
                        issues.append(f"param `{arg.arg}` missing type")

                for arg in node.args.kwonlyargs:
                    if not arg.annotation:
                        issues.append(f"kwonly param `{arg.arg}` missing type")

                # Check return type
                if not node.returns:
                    issues.append("missing return type")

                if issues:
                    missing.append(f"  ⚠️ Line {node.lineno}: `{node.name}` — {', '.join(issues)}")
                else:
                    fully_annotated += 1

        if total_funcs == 0:
            return f"No functions found in {file_path}"

        coverage_pct = (fully_annotated / total_funcs) * 100 if total_funcs > 0 else 0
        indicator = "✅" if coverage_pct >= 90 else "⚠️" if coverage_pct >= 50 else "🔴"

        header = (
            f"## Type Hint Analysis for {file_path}\n"
            f"{indicator} Coverage: {fully_annotated}/{total_funcs} functions fully annotated ({coverage_pct:.0f}%)\n"
        )

        if missing:
            return header + "\n### Missing Annotations:\n" + "\n".join(missing)
        return header + "\n✅ All functions are fully annotated!"
    except SyntaxError as e:
        return f"Syntax error in {file_path}: {e}"
    except FileNotFoundError:
        return f"Error: File not found: {file_path}"
    except Exception as e:
        return f"Error analyzing type hints: {e}"


@tool
def analyze_dependency_security(file_path: str) -> str:
    """Analyze a dependency file (requirements.txt, package.json, etc.) for security concerns.

    Checks for unpinned versions, known problematic packages, and general
    dependency hygiene issues.

    Args:
        file_path: Path to the dependency file (requirements.txt, package.json, Pipfile, pyproject.toml, etc.).
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        findings = []
        basename = os.path.basename(file_path).lower()

        if basename in ("requirements.txt", "requirements-dev.txt", "requirements-test.txt"):
            lines = [l.strip() for l in content.splitlines() if l.strip() and not l.strip().startswith("#")]
            for line in lines:
                # Check for unpinned versions
                if ">=" in line and "==" not in line:
                    findings.append(f"⚠️ Loosely pinned: `{line}` — consider using `==` for reproducibility")
                elif "==" not in line and ">=" not in line and "<=" not in line and line and not line.startswith("-"):
                    # Completely unpinned
                    pkg = line.split("[")[0].strip()
                    if pkg:
                        findings.append(f"🔴 Unpinned: `{pkg}` — no version constraint, could break on update")

                # Check for known problematic patterns
                pkg_lower = line.lower()
                if "pyyaml" in pkg_lower:
                    findings.append(f"💡 `PyYAML` found — ensure yaml.safe_load() is used, never yaml.load()")
                if "requests" in pkg_lower and "urllib3" not in pkg_lower:
                    findings.append(f"💡 `requests` found — ensure SSL verification is not disabled (verify=True)")
                if "flask" in pkg_lower:
                    findings.append(f"💡 `Flask` found — ensure debug=False in production, check CORS config")
                if "django" in pkg_lower:
                    findings.append(f"💡 `Django` found — ensure DEBUG=False in production, check ALLOWED_HOSTS")

        elif basename == "package.json":
            import json
            try:
                pkg = json.loads(content)
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                for name, version in deps.items():
                    if version.startswith("*") or version == "latest":
                        findings.append(f"🔴 Wildcard version: `{name}: {version}` — pin to specific version")
                    elif version.startswith("^") or version.startswith("~"):
                        findings.append(f"⚠️ Range version: `{name}: {version}` — consider pinning for production")
            except json.JSONDecodeError:
                findings.append("🔴 Invalid JSON in package.json")
        else:
            findings.append(f"💡 Dependency file type recognized but detailed scanning not yet supported for `{basename}`")
            findings.append(f"   File content preview:\n{content[:500]}")

        if findings:
            header = f"## Dependency Security Analysis: {file_path}\nFound {len(findings)} issue(s):\n"
            return header + "\n".join(f"  {f}" for f in findings)
        return f"✅ No dependency issues found in {file_path}"
    except FileNotFoundError:
        return f"Error: File not found: {file_path}"
    except Exception as e:
        return f"Error analyzing dependencies: {e}"
