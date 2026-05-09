"""
NeuroTrace - Root Cause Analyzer
Uses LLM chain-of-thought reasoning to identify the root cause of bugs.
"""

import json
import difflib

from backend.models import (
    RootCauseResult, BugSeverity,
    TraceResult, StaticAnalysisResult,
)
from backend.llm.client import get_llm_client
from backend.llm.prompts import ROOT_CAUSE_SYSTEM, ROOT_CAUSE_USER


def _format_variables(variables: dict[str, str]) -> str:
    """Format variable dict into readable string."""
    if not variables:
        return "No variables captured"
    lines = [f"  {k} = {v}" for k, v in variables.items()]
    return "\n".join(lines)


def _format_static_warnings(analysis: StaticAnalysisResult | None) -> str:
    """Format static analysis issues into readable string."""
    if not analysis:
        return "No static analysis available"
    all_issues = analysis.ast_issues + analysis.pylint_issues + analysis.mypy_issues
    if not all_issues:
        return "No issues found"
    lines = [f"  Line {i.line}: [{i.source}] {i.message}" for i in all_issues[:10]]
    return "\n".join(lines)


async def analyze_root_cause(
    source_code: str,
    trace: TraceResult,
    static_analysis: StaticAnalysisResult | None = None,
) -> RootCauseResult:
    """
    Use LLM to perform chain-of-thought root cause analysis.
    Combines code, runtime trace, and static analysis into a structured prompt.
    """
    if trace.exception is None:
        return RootCauseResult(
            bug_type="No error detected",
            root_cause="Code executed without raising an exception.",
            confidence=1.0,
        )

    prompt = ROOT_CAUSE_USER.format(
        source_code=source_code,
        exception_type=trace.exception.type,
        exception_message=trace.exception.message,
        traceback_str=trace.traceback_str or "Not available",
        variables=_format_variables(trace.variables_at_crash),
        static_warnings=_format_static_warnings(static_analysis),
    )

    messages = [
        {"role": "system", "content": ROOT_CAUSE_SYSTEM},
        {"role": "user", "content": prompt},
    ]

    try:
        client = get_llm_client()
        data = await client.achat_json(messages)

        severity_str = data.get("severity", "medium").lower()
        try:
            severity = BugSeverity(severity_str)
        except ValueError:
            severity = BugSeverity.MEDIUM

        return RootCauseResult(
            bug_type=data.get("bug_type", trace.exception.type),
            faulty_line=data.get("faulty_line"),
            root_cause=data.get("root_cause", ""),
            reasoning_steps=data.get("reasoning_steps", []),
            severity=severity,
            confidence=float(data.get("confidence", 0.5)),
        )

    except Exception as e:
        # fallback: return basic info from trace if LLM fails
        return RootCauseResult(
            bug_type=trace.exception.type,
            faulty_line=trace.crash_line,
            root_cause=f"LLM analysis failed ({type(e).__name__}). "
                       f"Error: {trace.exception.type}: {trace.exception.message}",
            reasoning_steps=[f"LLM error: {str(e)}"],
            severity=BugSeverity.MEDIUM,
            confidence=0.2,
        )
