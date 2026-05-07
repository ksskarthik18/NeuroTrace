"""
NeuroTrace - Code Execution Sandbox
Safely executes user Python code in an isolated subprocess with timeout and cleanup.
"""

import subprocess
import tempfile
import os
import time
import sys
from pathlib import Path

from backend.config import get_settings
from backend.models import ExecutionResult

settings = get_settings()


def _extract_traceback(stderr: str) -> str | None:
    """Pull the traceback portion from stderr output."""
    if "Traceback" not in stderr:
        return None
    lines = stderr.split("\n")
    tb_start = None
    for i, line in enumerate(lines):
        if line.startswith("Traceback"):
            tb_start = i
    if tb_start is not None:
        return "\n".join(lines[tb_start:]).strip()
    return None


async def execute_code(
    source_code: str,
    timeout: int | None = None,
) -> ExecutionResult:
    """
    Execute Python code in a subprocess with timeout.
    Writes code to a temp file, runs it, captures output, and cleans up.
    """
    timeout = timeout or settings.sandbox_timeout
    tmp_dir = None

    try:
        tmp_dir = tempfile.mkdtemp(prefix="neurotrace_")
        code_file = os.path.join(tmp_dir, "user_code.py")

        with open(code_file, "w", encoding="utf-8") as f:
            f.write(source_code)

        start = time.perf_counter()

        result = subprocess.run(
            [sys.executable, code_file],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=tmp_dir,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )

        elapsed_ms = int((time.perf_counter() - start) * 1000)

        return ExecutionResult(
            stdout=result.stdout,
            stderr=result.stderr,
            return_code=result.returncode,
            execution_time_ms=elapsed_ms,
            traceback=_extract_traceback(result.stderr),
        )

    except subprocess.TimeoutExpired:
        return ExecutionResult(
            stdout="",
            stderr=f"Execution timed out after {timeout} seconds",
            return_code=-1,
            execution_time_ms=timeout * 1000,
            traceback=None,
        )

    except Exception as e:
        return ExecutionResult(
            stdout="",
            stderr=str(e),
            return_code=-1,
            execution_time_ms=0,
            traceback=None,
        )

    finally:
        if tmp_dir:
            _cleanup(tmp_dir)


async def execute_code_with_tests(
    source_code: str,
    test_code: str,
    timeout: int | None = None,
) -> ExecutionResult:
    """
    Execute user code followed by test code in the same file.
    Used for patch validation — runs the patched code then the tests.
    """
    combined = source_code.rstrip("\n") + "\n\n" + test_code
    return await execute_code(combined, timeout)


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
