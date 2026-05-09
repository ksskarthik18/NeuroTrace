"""
NeuroTrace - Static Analysis Engine
Analyzes Python source code using AST, pylint, and mypy.
"""

import ast
import subprocess
import sys
import os
import re
import tempfile
import json

from backend.models import CodeIssue, CodeMetrics, StaticAnalysisResult


def _analyze_ast(source_code: str) -> tuple[list[CodeIssue], CodeMetrics]:
    """Parse code with AST to extract metrics and detect basic issues."""
    issues: list[CodeIssue] = []
    metrics = CodeMetrics()

    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        issues.append(CodeIssue(
            line=e.lineno or 1,
            column=e.offset or 0,
            code="E0001",
            message=f"SyntaxError: {e.msg}",
            severity="error",
            source="ast",
        ))
        return issues, metrics

    lines = source_code.strip().split("\n")
    metrics.num_lines = len(lines)

    defined_names: set[str] = set()
    used_names: set[str] = set()
    imports: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            metrics.num_functions += 1
            defined_names.add(node.name)
        elif isinstance(node, ast.ClassDef):
            metrics.num_classes += 1
            defined_names.add(node.name)
        elif isinstance(node, ast.Import):
            metrics.num_imports += 1
            for alias in node.names:
                name = alias.asname or alias.name
                imports.append(name)
                defined_names.add(name)
        elif isinstance(node, ast.ImportFrom):
            metrics.num_imports += 1
            for alias in node.names:
                name = alias.asname or alias.name
                imports.append(name)
                defined_names.add(name)
        elif isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Load):
                used_names.add(node.id)

    # detect unused imports
    for imp in imports:
        if imp not in used_names and imp != "*":
            # find the line number
            line_num = 1
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    for alias in node.names:
                        if (alias.asname or alias.name) == imp:
                            line_num = node.lineno
            issues.append(CodeIssue(
                line=line_num,
                code="W0611",
                message=f"Unused import: '{imp}'",
                severity="warning",
                source="ast",
            ))

    return issues, metrics


def _run_pylint(source_code: str) -> list[CodeIssue]:
    """Run pylint on the code and parse JSON output."""
    issues: list[CodeIssue] = []
    tmp_dir = None

    try:
        tmp_dir = tempfile.mkdtemp(prefix="neurotrace_pylint_")
        code_file = os.path.join(tmp_dir, "check.py")
        with open(code_file, "w", encoding="utf-8") as f:
            f.write(source_code)

        result = subprocess.run(
            [sys.executable, "-m", "pylint", code_file,
             "--output-format=json",
             "--disable=C0114,C0115,C0116,C0304,C0303,C0305,R,C0411"],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=tmp_dir,
        )

        if result.stdout.strip():
            try:
                entries = json.loads(result.stdout)
                for entry in entries:
                    severity = "error" if entry.get("type") in ("error", "fatal") else "warning"
                    issues.append(CodeIssue(
                        line=entry.get("line", 1),
                        column=entry.get("column", 0),
                        code=entry.get("message-id", ""),
                        message=entry.get("message", ""),
                        severity=severity,
                        source="pylint",
                    ))
            except json.JSONDecodeError:
                pass

    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    finally:
        if tmp_dir:
            _cleanup(tmp_dir)

    return issues


def _run_mypy(source_code: str) -> list[CodeIssue]:
    """Run mypy on the code and parse output."""
    issues: list[CodeIssue] = []
    tmp_dir = None

    try:
        tmp_dir = tempfile.mkdtemp(prefix="neurotrace_mypy_")
        code_file = os.path.join(tmp_dir, "check.py")
        with open(code_file, "w", encoding="utf-8") as f:
            f.write(source_code)

        result = subprocess.run(
            [sys.executable, "-m", "mypy", code_file,
             "--no-error-summary", "--no-color",
             "--ignore-missing-imports"],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=tmp_dir,
        )

        output = result.stdout + result.stderr
        # mypy output format: filename:line: level: message
        pattern = re.compile(r"check\.py:(\d+):\s*(error|warning|note):\s*(.+)")
        for match in pattern.finditer(output):
            line_num = int(match.group(1))
            level = match.group(2)
            message = match.group(3).strip()
            if level == "note":
                continue
            issues.append(CodeIssue(
                line=line_num,
                code="mypy",
                message=message,
                severity=level,
                source="mypy",
            ))

    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    finally:
        if tmp_dir:
            _cleanup(tmp_dir)

    return issues


async def analyze_code(source_code: str) -> StaticAnalysisResult:
    """Run all static analyzers and return combined results."""
    ast_issues, metrics = _analyze_ast(source_code)
    pylint_issues = _run_pylint(source_code)
    mypy_issues = _run_mypy(source_code)

    return StaticAnalysisResult(
        ast_issues=ast_issues,
        pylint_issues=pylint_issues,
        mypy_issues=mypy_issues,
        metrics=metrics,
    )


def _cleanup(tmp_dir: str):
    """Remove the temp directory and all its contents."""
    try:
        for root, dirs, files in os.walk(tmp_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(tmp_dir)
    except OSError:
        pass
