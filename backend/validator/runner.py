"""
NeuroTrace - Patch Validation Runner
Executes patched code, runs tests, and implements the iterative repair loop.
If a patch fails, feeds the error back to the patch generator and retries.
"""

import re

from backend.config import get_settings
from backend.models import (
    ValidationResult, ValidationStatus,
    ExecutionResult, TestResults, RepairAttempt,
    RootCauseResult, PatchResult,
)
from backend.debugger.sandbox import execute_code, execute_code_with_tests
from backend.patcher.generator import generate_patch

settings = get_settings()


def _parse_pytest_output(output: str) -> TestResults:
    """Parse pytest-style output to extract pass/fail/error counts."""
    passed = failed = errors = 0

    # match pytest summary line: "5 passed, 2 failed, 1 error"
    match = re.search(r"(\d+) passed", output)
    if match:
        passed = int(match.group(1))
    match = re.search(r"(\d+) failed", output)
    if match:
        failed = int(match.group(1))
    match = re.search(r"(\d+) error", output)
    if match:
        errors = int(match.group(1))

    return TestResults(passed=passed, failed=failed, errors=errors, output=output)


def _calculate_confidence(
    execution: ExecutionResult,
    test_results: TestResults | None,
    original_code: str,
    patched_code: str,
    attempts: int,
) -> float:
    """
    Calculate confidence score for a patch.
    Formula:
      0.35 * execution_success
    + 0.35 * test_pass_rate
    + 0.15 * patch_minimality
    + 0.15 * attempt_penalty
    """
    # execution success: 1.0 if runs without error, 0.0 otherwise
    exec_score = 1.0 if execution.return_code == 0 else 0.0

    # test pass rate
    test_score = 0.5  # default if no tests provided
    if test_results and (test_results.passed + test_results.failed + test_results.errors) > 0:
        total = test_results.passed + test_results.failed + test_results.errors
        test_score = test_results.passed / total

    # patch minimality: smaller diff = higher score
    orig_lines = original_code.strip().splitlines()
    patch_lines = patched_code.strip().splitlines()
    if len(orig_lines) > 0:
        changed = sum(1 for a, b in zip(orig_lines, patch_lines) if a != b)
        added = abs(len(patch_lines) - len(orig_lines))
        total_changes = changed + added
        minimality = max(0.0, 1.0 - (total_changes / max(len(orig_lines), 1)) * 0.5)
    else:
        minimality = 0.5

    # attempt penalty: first attempt = 1.0, degrades with retries
    attempt_score = max(0.0, 1.0 - (attempts - 1) * 0.3)

    # If the patch made no meaningful changes (ignoring blank lines and comments) and executes perfectly,
    # it means the original code was already correct. Give it 100% confidence.
    def _clean_line(line: str) -> str:
        return line.split('#')[0].strip()

    orig_clean = [_clean_line(l) for l in orig_lines if _clean_line(l)]
    patch_clean = [_clean_line(l) for l in patch_lines if _clean_line(l)]
    
    if orig_clean == patch_clean and exec_score == 1.0:
        return 1.0

    confidence = (
        0.35 * exec_score
        + 0.35 * test_score
        + 0.15 * minimality
        + 0.15 * attempt_score
    )

    return round(min(1.0, max(0.0, confidence)), 2)


async def validate_patch(
    original_code: str,
    patched_code: str,
    root_cause: RootCauseResult,
    test_code: str | None = None,
    max_retries: int | None = None,
) -> ValidationResult:
    """
    Validate a patch by executing it and optionally running tests.
    If the patch fails, retry by feeding the error back to the LLM.
    """
    max_retries = max_retries or settings.max_repair_attempts
    repair_history: list[RepairAttempt] = []
    current_patch = patched_code

    for attempt in range(1, max_retries + 1):
        # execute the patched code
        if test_code:
            execution = await execute_code_with_tests(current_patch, test_code)
        else:
            execution = await execute_code(current_patch)

        # parse test results if tests were provided
        test_results = None
        if test_code:
            test_results = _parse_pytest_output(execution.stdout + execution.stderr)
            # Fallback for plain assert statements (no pytest output)
            if test_results.passed == 0 and test_results.failed == 0 and test_results.errors == 0:
                if execution.return_code == 0:
                    test_results.passed = 1
                else:
                    test_results.failed = 1

        # check if patch succeeded
        if execution.return_code == 0:
            confidence = _calculate_confidence(
                execution, test_results, original_code, current_patch, attempt
            )
            repair_history.append(RepairAttempt(
                attempt=attempt, status="validated"
            ))
            return ValidationResult(
                status=ValidationStatus.VALIDATED,
                patched_code=current_patch,
                confidence=confidence,
                attempts=attempt,
                repair_history=repair_history,
                test_results=test_results,
                execution_result=execution,
            )

        # patch failed — record the attempt
        error_msg = execution.stderr[:500] if execution.stderr else "Unknown error"
        repair_history.append(RepairAttempt(
            attempt=attempt, status="failed", error=error_msg
        ))

        # if we have retries left, ask LLM for a new patch
        if attempt < max_retries:
            new_patch_result = await generate_patch(
                original_code,
                root_cause,
                attempt=attempt + 1,
                previous_patch=current_patch,
                failure_reason=error_msg,
            )
            current_patch = new_patch_result.patched_code

    # all attempts exhausted
    confidence = _calculate_confidence(
        execution, test_results if test_code else None,
        original_code, current_patch, max_retries
    )
    return ValidationResult(
        status=ValidationStatus.FAILED,
        patched_code=current_patch,
        confidence=confidence,
        attempts=max_retries,
        repair_history=repair_history,
        test_results=test_results if test_code else None,
        execution_result=execution,
    )
