"""
NeuroTrace - Runtime Trace Collector
Injects tracing code around user code to capture exception details,
variable state at crash point, and call stack.
"""

import subprocess
import tempfile
import os
import sys
import json
import textwrap

from backend.config import get_settings
from backend.models import TraceResult, ExceptionInfo

settings = get_settings()

# Number of lines the wrapper adds BEFORE user code (the "try:" line is line 14)
_WRAPPER_OFFSET = 14

TRACE_WRAPPER = textwrap.dedent('''\
import sys as _sys
import traceback as _traceback
import json as _json
import types as _types

_trace_data = {
    "exception": None,
    "traceback_str": "",
    "crash_line": None,
    "variables_at_crash": {},
    "call_stack": []
}

try:
{user_code}
except Exception as _e:
    _tb = _sys.exc_info()[2]
    _trace_data["exception"] = {
        "type": type(_e).__name__,
        "message": str(_e)
    }
    _trace_data["traceback_str"] = _traceback.format_exc()

    _frames = _traceback.extract_tb(_tb)
    if _frames:
        _last = _frames[-1]
        _trace_data["crash_line"] = _last.lineno

    _frame = _tb
    while _frame.tb_next:
        _frame = _frame.tb_next
    _locals = dict(_frame.tb_frame.f_locals)
    for _k, _v in _locals.items():
        if _k.startswith("_"):
            continue
        if isinstance(_v, _types.ModuleType):
            continue
        try:
            _trace_data["variables_at_crash"][_k] = repr(_v)
        except Exception:
            _trace_data["variables_at_crash"][_k] = "<unrepresentable>"

    _stack_frames = _traceback.extract_tb(_tb)
    _trace_data["call_stack"] = [_f.name for _f in _stack_frames]

print("__NEUROTRACE__:" + _json.dumps(_trace_data))
''')


def _build_trace_code(source_code: str) -> str:
    """Wrap user code with the trace template."""
    indented = textwrap.indent(source_code, "    ")
    return TRACE_WRAPPER.replace("{user_code}", indented)


def _parse_trace_output(stdout: str) -> TraceResult:
    """Extract trace data from the subprocess stdout."""
    for line in stdout.strip().split("\n"):
        if line.startswith("__NEUROTRACE__:"):
            json_str = line[len("__NEUROTRACE__:"):]
            try:
                data = json.loads(json_str)
                exception = None
                if data.get("exception"):
                    exception = ExceptionInfo(
                        type=data["exception"]["type"],
                        message=data["exception"]["message"],
                    )

                crash_line = data.get("crash_line")
                if crash_line is not None:
                    crash_line = max(1, crash_line - _WRAPPER_OFFSET)

                return TraceResult(
                    exception=exception,
                    traceback_str=data.get("traceback_str", ""),
                    crash_line=crash_line,
                    variables_at_crash=data.get("variables_at_crash", {}),
                    call_stack=data.get("call_stack", []),
                )
            except (json.JSONDecodeError, KeyError):
                pass

    return TraceResult()


async def collect_trace(source_code: str, timeout: int | None = None) -> TraceResult:
    """
    Execute user code with tracing wrapper and return structured trace data.
    Captures exception info, crash line, variables, and call stack.
    """
    timeout = timeout or settings.sandbox_timeout
    tmp_dir = None

    try:
        tmp_dir = tempfile.mkdtemp(prefix="neurotrace_trace_")
        trace_code = _build_trace_code(source_code)
        code_file = os.path.join(tmp_dir, "trace_run.py")

        with open(code_file, "w", encoding="utf-8") as f:
            f.write(trace_code)

        result = subprocess.run(
            [sys.executable, code_file],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=tmp_dir,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )

        return _parse_trace_output(result.stdout)

    except subprocess.TimeoutExpired:
        return TraceResult(
            exception=ExceptionInfo(type="TimeoutError", message=f"Execution timed out after {timeout}s"),
        )

    except Exception as e:
        return TraceResult(
            exception=ExceptionInfo(type=type(e).__name__, message=str(e)),
        )

    finally:
        if tmp_dir:
            _cleanup(tmp_dir)


def _cleanup(tmp_dir: str):
    """Remove temp directory and all contents."""
    try:
        for root, dirs, files in os.walk(tmp_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(tmp_dir)
    except OSError:
        pass
