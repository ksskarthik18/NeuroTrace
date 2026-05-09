"""
NeuroTrace - LLM Prompt Templates
Structured prompts for root cause analysis and patch generation.
"""

ROOT_CAUSE_SYSTEM = """You are an expert Python debugger. Your job is to analyze buggy Python code and determine the root cause of the error. Think step by step.

You must respond with ONLY valid JSON in this exact format:
{
  "bug_type": "the exception or error type (e.g. IndexError, TypeError, LogicError)",
  "faulty_line": <line number as integer or null>,
  "root_cause": "a detailed explanation of WHY the bug occurs, not just what the error is",
  "reasoning_steps": ["step 1 of your analysis", "step 2", ...],
  "severity": "critical|high|medium|low",
  "confidence": <float between 0.0 and 1.0>
}"""

ROOT_CAUSE_USER = """Analyze the following buggy Python code and determine the root cause of the error.

## Source Code
```python
{source_code}
```

## Runtime Error
{exception_type}: {exception_message}

## Traceback
{traceback_str}

## Variables at Crash Point
{variables}

## Static Analysis Warnings
{static_warnings}

Respond with ONLY the JSON object, no other text."""


PATCH_SYSTEM = """You are an expert Python developer. Your job is to fix buggy Python code with a minimal, safe patch. Do NOT rewrite the entire file. Make the smallest change that fixes the bug.

You must respond with ONLY valid JSON in this exact format:
{
  "patched_code": "the complete corrected source code",
  "explanation": "brief explanation of what was changed and why",
  "diff_summary": "one line summary of the change"
}"""

PATCH_USER = """Fix the following buggy Python code.

## Original Code
```python
{source_code}
```

## Bug Analysis
- Bug Type: {bug_type}
- Root Cause: {root_cause}
- Faulty Line: {faulty_line}

Generate a minimal fix. Respond with ONLY the JSON object, no other text."""

PATCH_RETRY_USER = """Your previous fix attempt failed. Fix the code again, avoiding the same mistake.

## Original Code
```python
{source_code}
```

## Bug Analysis
- Bug Type: {bug_type}
- Root Cause: {root_cause}

## Previous Patch (FAILED)
```python
{previous_patch}
```

## Failure Reason
{failure_reason}

Generate a corrected fix. Respond with ONLY the JSON object, no other text."""
