"""
NeuroTrace API Routes
Defines all REST endpoints for the debugging pipeline.
"""

import uuid
from fastapi import APIRouter
from backend.config import get_settings
from backend.models import (
    DebugRequest, DebugResponse, HealthResponse,
    ExecutionResult, StaticAnalysisResult, TraceResult,
    RootCauseResult, PatchResult, ValidationResult,
)
from backend.debugger.sandbox import execute_code
from backend.debugger.static_analyzer import analyze_code
from backend.debugger.trace_collector import collect_trace
from backend.llm.root_cause import analyze_root_cause
from backend.patcher.generator import generate_patch
from backend.validator.runner import validate_patch

router = APIRouter(prefix="/api/v1", tags=["debug"])
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check if the API is running."""
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        environment=settings.app_env,
    )


@router.post("/debug", response_model=DebugResponse)
async def debug_code(request: DebugRequest):
    """
    Full debugging pipeline:
    1. Execute code in sandbox
    2. Run static analysis
    3. Collect runtime trace
    4. Perform root cause analysis (LLM)
    5. Generate patch (LLM)
    6. Validate patch with iterative repair loop
    """
    execution = await execute_code(request.source_code)
    static_analysis = await analyze_code(request.source_code)
    trace = await collect_trace(request.source_code)
    root_cause = await analyze_root_cause(request.source_code, trace, static_analysis)
    patch = await generate_patch(request.source_code, root_cause)
    validation = await validate_patch(
        request.source_code, patch.patched_code, root_cause, request.test_code
    )

    return DebugResponse(
        session_id=str(uuid.uuid4()),
        source_code=request.source_code,
        execution=execution,
        static_analysis=static_analysis,
        trace=trace,
        root_cause=root_cause,
        patch=patch,
        validation=validation,
    )


@router.post("/execute", response_model=ExecutionResult)
async def execute_code_endpoint(request: DebugRequest):
    """Execute code in the sandbox and return the result."""
    return await execute_code(request.source_code)


@router.post("/analyze", response_model=StaticAnalysisResult)
async def analyze_code_endpoint(request: DebugRequest):
    """Run static analysis on the provided code."""
    return await analyze_code(request.source_code)


@router.post("/trace", response_model=TraceResult)
async def collect_trace_endpoint(request: DebugRequest):
    """Collect runtime trace with exception details and variable state."""
    return await collect_trace(request.source_code)


@router.post("/root-cause", response_model=RootCauseResult)
async def root_cause_endpoint(request: DebugRequest):
    """Perform LLM root cause analysis on buggy code."""
    trace = await collect_trace(request.source_code)
    static_analysis = await analyze_code(request.source_code)
    return await analyze_root_cause(request.source_code, trace, static_analysis)


@router.post("/patch", response_model=PatchResult)
async def patch_endpoint(request: DebugRequest):
    """Generate a patch for buggy code."""
    trace = await collect_trace(request.source_code)
    static_analysis = await analyze_code(request.source_code)
    root_cause = await analyze_root_cause(request.source_code, trace, static_analysis)
    return await generate_patch(request.source_code, root_cause)


@router.post("/validate", response_model=ValidationResult)
async def validate_endpoint(request: DebugRequest):
    """Run the full pipeline and validate the generated patch."""
    trace = await collect_trace(request.source_code)
    static_analysis = await analyze_code(request.source_code)
    root_cause = await analyze_root_cause(request.source_code, trace, static_analysis)
    patch = await generate_patch(request.source_code, root_cause)
    return await validate_patch(
        request.source_code, patch.patched_code, root_cause, request.test_code
    )
