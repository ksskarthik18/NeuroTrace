"""
Tests for the runtime trace collector.
"""

import pytest
from backend.debugger.trace_collector import collect_trace


@pytest.mark.asyncio
async def test_clean_code_no_exception():
    """Code without errors should return empty trace."""
    result = await collect_trace("x = 1\nprint(x)")
    assert result.exception is None
    assert result.crash_line is None
    assert result.variables_at_crash == {}


@pytest.mark.asyncio
async def test_index_error_captured():
    """IndexError should be fully captured."""
    code = "nums = [1, 2, 3]\nprint(nums[10])"
    result = await collect_trace(code)
    assert result.exception is not None
    assert result.exception.type == "IndexError"
    assert "index" in result.exception.message.lower()
    assert result.crash_line is not None


@pytest.mark.asyncio
async def test_variable_state_captured():
    """Variables at the crash frame should be captured."""
    code = "x = 42\ny = 'hello'\nz = x / 0"
    result = await collect_trace(code)
    assert result.exception is not None
    assert result.exception.type == "ZeroDivisionError"
    assert "x" in result.variables_at_crash
    assert "42" in result.variables_at_crash["x"]
    assert "y" in result.variables_at_crash
    assert "hello" in result.variables_at_crash["y"]


@pytest.mark.asyncio
async def test_key_error_captured():
    """KeyError should be captured with variable context."""
    code = "d = {'a': 1, 'b': 2}\nval = d['missing']"
    result = await collect_trace(code)
    assert result.exception is not None
    assert result.exception.type == "KeyError"
    assert "d" in result.variables_at_crash


@pytest.mark.asyncio
async def test_type_error_captured():
    """TypeError from None access should be captured."""
    code = "x = None\nx.append(1)"
    result = await collect_trace(code)
    assert result.exception is not None
    assert result.exception.type == "AttributeError"


@pytest.mark.asyncio
async def test_traceback_string_present():
    """Traceback string should contain the error details."""
    code = "raise ValueError('test error')"
    result = await collect_trace(code)
    assert result.exception is not None
    assert result.exception.type == "ValueError"
    assert "test error" in result.exception.message
    assert "Traceback" in result.traceback_str
    assert "ValueError" in result.traceback_str


@pytest.mark.asyncio
async def test_call_stack_captured():
    """Call stack should show function names."""
    code = """
def inner():
    raise RuntimeError("deep error")

def outer():
    inner()

outer()
"""
    result = await collect_trace(code)
    assert result.exception is not None
    assert result.exception.type == "RuntimeError"
    assert len(result.call_stack) > 0


@pytest.mark.asyncio
async def test_timeout_returns_timeout_error():
    """Infinite loop should return TimeoutError in trace."""
    result = await collect_trace("while True: pass", timeout=2)
    assert result.exception is not None
    assert result.exception.type == "TimeoutError"
    assert "timed out" in result.exception.message.lower()


@pytest.mark.asyncio
async def test_multiline_function_error():
    """Error inside a function should capture correct context."""
    code = """
def process(data):
    result = data["key"]
    return result

process({})
"""
    result = await collect_trace(code)
    assert result.exception is not None
    assert result.exception.type == "KeyError"
    assert "data" in result.variables_at_crash
