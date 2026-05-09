"""
Tests for root cause analysis and patch generation.
Uses mocked LLM client to avoid needing API keys in CI.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from backend.models import (
    TraceResult, ExceptionInfo, StaticAnalysisResult,
    CodeIssue, RootCauseResult, BugSeverity,
)
from backend.llm.root_cause import analyze_root_cause, _format_variables, _format_static_warnings
from backend.patcher.generator import generate_patch, _generate_diff, _extract_changes


# --- Helper function tests (no LLM needed) ---

def test_format_variables_empty():
    assert "No variables" in _format_variables({})


def test_format_variables_with_data():
    result = _format_variables({"x": "42", "name": "'hello'"})
    assert "x = 42" in result
    assert "name = 'hello'" in result


def test_format_static_warnings_none():
    result = _format_static_warnings(None)
    assert "No static analysis" in result


def test_format_static_warnings_with_issues():
    analysis = StaticAnalysisResult(
        pylint_issues=[CodeIssue(line=5, message="Undefined variable 'x'", source="pylint")]
    )
    result = _format_static_warnings(analysis)
    assert "Line 5" in result
    assert "Undefined" in result


def test_generate_diff():
    original = "x = 1\nprint(x[5])"
    patched = "x = 1\nif len(x) > 5:\n    print(x[5])"
    diff = _generate_diff(original, patched)
    assert "---" in diff
    assert "+++" in diff


def test_extract_changes():
    original = "x = 1\nprint(x[5])"
    patched = "x = 1\nif len(x) > 5:\n    print(x[5])"
    changes = _extract_changes(original, patched)
    assert len(changes) > 0


# --- Root cause analysis tests (mocked LLM) ---

@pytest.mark.asyncio
async def test_root_cause_no_error():
    """Code without error should return 'no error detected'."""
    trace = TraceResult()
    result = await analyze_root_cause("x = 1", trace)
    assert result.bug_type == "No error detected"
    assert result.confidence == 1.0


@pytest.mark.asyncio
async def test_root_cause_with_llm_mock():
    """Root cause should parse LLM JSON response correctly."""
    trace = TraceResult(
        exception=ExceptionInfo(type="IndexError", message="list index out of range"),
        crash_line=2,
        variables_at_crash={"nums": "[1, 2, 3]"},
    )

    mock_response = {
        "bug_type": "IndexError",
        "faulty_line": 2,
        "root_cause": "List has 3 elements but index 5 was accessed",
        "reasoning_steps": ["List has 3 items", "Index 5 is out of bounds"],
        "severity": "high",
        "confidence": 0.92,
    }

    with patch("backend.llm.root_cause.get_llm_client") as mock_get:
        mock_client = MagicMock()
        mock_client.achat_json = AsyncMock(return_value=mock_response)
        mock_get.return_value = mock_client

        result = await analyze_root_cause("nums = [1,2,3]\nprint(nums[5])", trace)

        assert result.bug_type == "IndexError"
        assert result.faulty_line == 2
        assert "index 5" in result.root_cause.lower() or "out of bounds" in result.root_cause.lower()
        assert result.confidence == 0.92
        assert result.severity == BugSeverity.HIGH
        assert len(result.reasoning_steps) == 2


@pytest.mark.asyncio
async def test_root_cause_llm_failure_fallback():
    """If LLM fails, should fallback to trace-based info."""
    trace = TraceResult(
        exception=ExceptionInfo(type="ValueError", message="invalid literal"),
        crash_line=3,
    )

    with patch("backend.llm.root_cause.get_llm_client") as mock_get:
        mock_client = MagicMock()
        mock_client.achat_json = AsyncMock(side_effect=Exception("API key invalid"))
        mock_get.return_value = mock_client

        result = await analyze_root_cause("int('abc')", trace)

        assert result.bug_type == "ValueError"
        assert result.faulty_line == 3
        assert result.confidence == 0.2
        assert "LLM analysis failed" in result.root_cause


# --- Patch generation tests (mocked LLM) ---

@pytest.mark.asyncio
async def test_patch_generation_with_mock():
    """Patch should be generated from LLM response."""
    root_cause = RootCauseResult(
        bug_type="IndexError",
        faulty_line=2,
        root_cause="Index out of bounds",
    )

    mock_response = {
        "patched_code": "nums = [1,2,3]\nif len(nums) > 5:\n    print(nums[5])",
        "explanation": "Added bounds check",
        "diff_summary": "Added if-check before index access",
    }

    with patch("backend.patcher.generator.get_llm_client") as mock_get:
        mock_client = MagicMock()
        mock_client.achat_json = AsyncMock(return_value=mock_response)
        mock_get.return_value = mock_client

        result = await generate_patch("nums = [1,2,3]\nprint(nums[5])", root_cause)

        assert "if len(nums)" in result.patched_code
        assert result.explanation == "Added bounds check"
        assert len(result.diff) > 0
        assert len(result.changes) > 0


@pytest.mark.asyncio
async def test_patch_generation_empty_response():
    """Empty LLM response should return original code."""
    root_cause = RootCauseResult(bug_type="Error", root_cause="something")

    mock_response = {"patched_code": "", "explanation": ""}

    with patch("backend.patcher.generator.get_llm_client") as mock_get:
        mock_client = MagicMock()
        mock_client.achat_json = AsyncMock(return_value=mock_response)
        mock_get.return_value = mock_client

        result = await generate_patch("x = 1", root_cause)
        assert result.patched_code == "x = 1"


@pytest.mark.asyncio
async def test_patch_generation_llm_failure():
    """If LLM fails, should return original code with error message."""
    root_cause = RootCauseResult(bug_type="Error", root_cause="something")

    with patch("backend.patcher.generator.get_llm_client") as mock_get:
        mock_client = MagicMock()
        mock_client.achat_json = AsyncMock(side_effect=Exception("timeout"))
        mock_get.return_value = mock_client

        result = await generate_patch("x = 1", root_cause)
        assert result.patched_code == "x = 1"
        assert "failed" in result.explanation.lower()


@pytest.mark.asyncio
async def test_patch_retry_uses_failure_context():
    """Retry attempt should include previous failure in prompt."""
    root_cause = RootCauseResult(bug_type="Error", root_cause="test")

    mock_response = {
        "patched_code": "fixed code",
        "explanation": "Fixed on retry",
        "diff_summary": "retried fix",
    }

    with patch("backend.patcher.generator.get_llm_client") as mock_get:
        mock_client = MagicMock()
        mock_client.achat_json = AsyncMock(return_value=mock_response)
        mock_get.return_value = mock_client

        result = await generate_patch(
            "x = 1", root_cause,
            attempt=2,
            previous_patch="bad fix",
            failure_reason="NameError in patched code",
        )
        assert result.patched_code == "fixed code"

        # verify the retry prompt was used (includes previous_patch)
        call_args = mock_client.achat_json.call_args
        messages = call_args[0][0]
        user_msg = messages[1]["content"]
        assert "bad fix" in user_msg
        assert "NameError" in user_msg
