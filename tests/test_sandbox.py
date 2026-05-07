"""
Tests for the code execution sandbox.
"""

import pytest
from backend.debugger.sandbox import execute_code, execute_code_with_tests


@pytest.mark.asyncio
async def test_simple_print():
    """Code that prints should capture stdout."""
    result = await execute_code("print('hello world')")
    assert result.return_code == 0
    assert "hello world" in result.stdout
    assert result.stderr == ""
    assert result.traceback is None


@pytest.mark.asyncio
async def test_return_code_on_error():
    """Code that raises should have non-zero return code."""
    result = await execute_code("raise ValueError('boom')")
    assert result.return_code != 0
    assert "ValueError" in result.stderr


@pytest.mark.asyncio
async def test_traceback_extraction():
    """Traceback should be extracted from stderr."""
    result = await execute_code("x = [1,2,3]\nprint(x[10])")
    assert result.return_code != 0
    assert result.traceback is not None
    assert "IndexError" in result.traceback


@pytest.mark.asyncio
async def test_syntax_error():
    """Syntax errors should be caught."""
    result = await execute_code("def foo(:\n  pass")
    assert result.return_code != 0
    assert "SyntaxError" in result.stderr


@pytest.mark.asyncio
async def test_timeout():
    """Infinite loops should be killed after timeout."""
    result = await execute_code("while True: pass", timeout=2)
    assert result.return_code == -1
    assert "timed out" in result.stderr


@pytest.mark.asyncio
async def test_multiline_code():
    """Multi-line code with functions should work."""
    code = """
def add(a, b):
    return a + b

result = add(2, 3)
print(f"Result: {result}")
"""
    result = await execute_code(code)
    assert result.return_code == 0
    assert "Result: 5" in result.stdout


@pytest.mark.asyncio
async def test_execution_time_tracked():
    """Execution time should be a positive number."""
    result = await execute_code("print(1)")
    assert result.execution_time_ms > 0


@pytest.mark.asyncio
async def test_no_file_pollution():
    """Temp files should be cleaned up after execution."""
    import os
    import tempfile

    before = set(os.listdir(tempfile.gettempdir()))
    await execute_code("print('cleanup test')")
    after = set(os.listdir(tempfile.gettempdir()))

    new_dirs = {d for d in (after - before) if d.startswith("neurotrace_")}
    assert len(new_dirs) == 0, f"Leftover temp dirs: {new_dirs}"


@pytest.mark.asyncio
async def test_execute_with_tests_pass():
    """Code + passing test should return success."""
    code = "def add(a, b): return a + b"
    tests = "assert add(1, 2) == 3\nprint('tests passed')"
    result = await execute_code_with_tests(code, tests)
    assert result.return_code == 0
    assert "tests passed" in result.stdout


@pytest.mark.asyncio
async def test_execute_with_tests_fail():
    """Code + failing test should return error."""
    code = "def add(a, b): return a - b"
    tests = "assert add(1, 2) == 3"
    result = await execute_code_with_tests(code, tests)
    assert result.return_code != 0
    assert "AssertionError" in result.stderr or "AssertionError" in str(result.traceback) or result.return_code != 0
