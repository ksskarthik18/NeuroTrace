"""
NeuroTrace Data Models
Pydantic schemas for requests, responses, and internal data structures.
"""

from __future__ import annotations
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class BugSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ValidationStatus(str, Enum):
    VALIDATED = "validated"
    FAILED = "failed"
    PARTIAL = "partial"


class DebugRequest(BaseModel):
    """Request to debug a piece of code."""
    source_code: str = Field(..., description="The buggy source code to debug")
    test_code: str | None = Field(None, description="Optional test code for validation")
    language: str = Field("python", description="Programming language (currently only python)")


class ExecutionResult(BaseModel):
    """Result from executing code in the sandbox."""
    stdout: str = ""
    stderr: str = ""
    return_code: int = 0
    execution_time_ms: int = 0
    traceback: str | None = None


class CodeIssue(BaseModel):
    """A single issue found by static analysis."""
    line: int
    column: int = 0
    code: str = ""
    message: str
    severity: str = "warning"
    source: str = "ast"


class CodeMetrics(BaseModel):
    """Metrics about the code structure."""
    num_lines: int = 0
    num_functions: int = 0
    num_classes: int = 0
    num_imports: int = 0


class StaticAnalysisResult(BaseModel):
    """Combined result from all static analyzers."""
    ast_issues: list[CodeIssue] = []
    pylint_issues: list[CodeIssue] = []
    mypy_issues: list[CodeIssue] = []
    metrics: CodeMetrics = CodeMetrics()


class ExceptionInfo(BaseModel):
    """Information about a caught exception."""
    type: str
    message: str


class TraceResult(BaseModel):
    """Result from runtime trace collection."""
    exception: ExceptionInfo | None = None
    traceback_str: str = ""
    crash_line: int | None = None
    variables_at_crash: dict[str, str] = {}
    call_stack: list[str] = []


class RootCauseResult(BaseModel):
    """LLM-generated root cause analysis."""
    bug_type: str = ""
    faulty_line: int | None = None
    root_cause: str = ""
    reasoning_steps: list[str] = []
    severity: BugSeverity = BugSeverity.MEDIUM
    confidence: float = 0.0


class PatchChange(BaseModel):
    """A single change in a patch."""
    line: int
    action: str = "replace"
    old: str = ""
    new: str = ""


class PatchResult(BaseModel):
    """LLM-generated patch."""
    patched_code: str = ""
    diff: str = ""
    explanation: str = ""
    changes: list[PatchChange] = []


class TestResults(BaseModel):
    """Results from running tests on patched code."""
    passed: int = 0
    failed: int = 0
    errors: int = 0
    output: str = ""


class RepairAttempt(BaseModel):
    """A single repair attempt in the validation loop."""
    attempt: int
    status: str
    error: str | None = None


class ValidationResult(BaseModel):
    """Result from the automated patch validation loop."""
    status: ValidationStatus = ValidationStatus.FAILED
    patched_code: str = ""
    confidence: float = 0.0
    attempts: int = 0
    repair_history: list[RepairAttempt] = []
    test_results: TestResults | None = None
    execution_result: ExecutionResult | None = None


class DebugResponse(BaseModel):
    """Complete response from the debug pipeline."""
    session_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    source_code: str
    execution: ExecutionResult | None = None
    static_analysis: StaticAnalysisResult | None = None
    trace: TraceResult | None = None
    root_cause: RootCauseResult | None = None
    patch: PatchResult | None = None
    validation: ValidationResult | None = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    version: str = ""
    environment: str = ""
