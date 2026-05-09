"""
Tests for the patch validation runner.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from backend.models import (
    RootCauseResult, ExecutionResult, ValidationStatus,
)
from backend.validator.runner import (
    validate_patch, _parse_pytest_output, _calculate_confidence,
)


# --- Helper function tests ---

def test_parse_pytest_output_all_passed():
    output = "===== 5 passed in 0.3s ====="
    result = _parse_pytest_output(output)
    assert result.passed == 5
    assert result.failed == 0
    assert result.errors == 0


def test_parse_pytest_output_mixed():
    output = "3 passed, 2 failed, 1 error in 1.2s"
    result = _parse_pytest_output(output)
    assert result.passed == 3
    assert result.failed == 2
    assert result.errors == 1


def test_parse_pytest_output_no_matches():
    output = "some random output"
    result = _parse_pytest_output(output)
    assert result.passed == 0
    assert result.failed == 0


def test_confidence_perfect_patch():
    """Perfect patch on first attempt should have high confidence."""
    execution = ExecutionResult(return_code=0, stdout="5 passed")
    from backend.models import TestResults
    test_results = TestResults(passed=5, failed=0, errors=0)
    confidence = _calculate_confidence(
        execution, test_results, "x = 1", "x = 1", 1
    )
    assert confidence >= 0.8


def test_confidence_failed_execution():
    """Failed execution should have low confidence."""
    execution = ExecutionResult(return_code=1, stderr="Error")
    confidence = _calculate_confidence(
        execution, None, "x = 1", "x = 1", 1
    )
    assert confidence < 0.5


def test_confidence_degrades_with_attempts():
    """More attempts should lower confidence."""
    execution = ExecutionResult(return_code=0)
    c1 = _calculate_confidence(execution, None, "x=1", "x=1", 1)
    c3 = _calculate_confidence(execution, None, "x=1", "x=1", 3)
    assert c1 > c3


# --- Validation loop tests ---

@pytest.mark.asyncio
async def test_validate_good_patch():
    """A correct patch should be validated on first attempt."""
    original = "print(1/0)"
    patched = "print(1/1)"
    root_cause = RootCauseResult(bug_type="ZeroDivisionError", root_cause="division by zero")

    result = await validate_patch(original, patched, root_cause)

    assert result.status == ValidationStatus.VALIDATED
    assert result.attempts == 1
    assert result.confidence > 0.5
    assert result.execution_result is not None
    assert result.execution_result.return_code == 0
    assert len(result.repair_history) == 1
    assert result.repair_history[0].status == "validated"


@pytest.mark.asyncio
async def test_validate_good_patch_with_tests():
    """Patch passing inline tests should be validated."""
    original = "def add(a, b): return a - b"
    patched = "def add(a, b): return a + b"
    test_code = "assert add(1, 2) == 3\nassert add(0, 0) == 0\nprint('tests passed')"
    root_cause = RootCauseResult(bug_type="LogicError", root_cause="wrong operator")

    result = await validate_patch(original, patched, root_cause, test_code)

    assert result.status == ValidationStatus.VALIDATED
    assert result.confidence > 0.5


@pytest.mark.asyncio
async def test_validate_bad_patch_retries():
    """A bad patch should trigger retries via LLM."""
    original = "print(1/0)"
    bad_patch = "print(1/0)"  # still broken
    root_cause = RootCauseResult(bug_type="ZeroDivisionError", root_cause="division by zero")

    # mock the patch generator to return a fixed version on retry
    with patch("backend.validator.runner.generate_patch") as mock_gen:
        from backend.models import PatchResult
        mock_gen.return_value = PatchResult(
            patched_code="print('fixed')",
            explanation="Fixed division",
        )

        result = await validate_patch(
            original, bad_patch, root_cause, max_retries=2
        )

        assert result.status == ValidationStatus.VALIDATED
        assert result.attempts == 2
        assert len(result.repair_history) == 2
        assert result.repair_history[0].status == "failed"
        assert result.repair_history[1].status == "validated"
        mock_gen.assert_called_once()


@pytest.mark.asyncio
async def test_validate_all_retries_exhausted():
    """If all retries fail, status should be FAILED."""
    original = "print(1/0)"
    bad_patch = "print(1/0)"
    root_cause = RootCauseResult(bug_type="ZeroDivisionError", root_cause="division by zero")

    with patch("backend.validator.runner.generate_patch") as mock_gen:
        from backend.models import PatchResult
        # every retry also returns broken code
        mock_gen.return_value = PatchResult(
            patched_code="print(2/0)",
            explanation="Still broken",
        )

        result = await validate_patch(
            original, bad_patch, root_cause, max_retries=3
        )

        assert result.status == ValidationStatus.FAILED
        assert result.attempts == 3
        assert all(r.status == "failed" for r in result.repair_history)
        assert result.confidence < 0.5


@pytest.mark.asyncio
async def test_validate_syntax_error_patch():
    """Patch with syntax error should fail and retry."""
    original = "x = 1"
    bad_patch = "x = (("  # syntax error
    root_cause = RootCauseResult(bug_type="Test", root_cause="test")

    with patch("backend.validator.runner.generate_patch") as mock_gen:
        from backend.models import PatchResult
        mock_gen.return_value = PatchResult(patched_code="x = 1\nprint('ok')")

        result = await validate_patch(original, bad_patch, root_cause, max_retries=2)

        assert result.status == ValidationStatus.VALIDATED
        assert result.attempts == 2
