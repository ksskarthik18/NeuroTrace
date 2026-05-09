"""
NeuroTrace API Routes
Defines all REST endpoints for the debugging pipeline.
"""

import uuid
from fastapi import APIRouter
from backend.config import get_settings
from backend.models import DebugRequest, DebugResponse, HealthResponse, ExecutionResult, StaticAnalysisResult, TraceResult
from backend.debugger.sandbox import execute_code
from backend.debugger.static_analyzer import analyze_code
from backend.debugger.trace_collector import collect_trace

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
    Full debugging pipeline.
    Runs Phase 1 (execution), Phase 2 (static analysis), and Phase 3 (trace).
    Remaining phases will be wired in later.
    """
    execution = await execute_code(request.source_code)
    static_analysis = await analyze_code(request.source_code)
    trace = await collect_trace(request.source_code)

    return DebugResponse(
        session_id=str(uuid.uuid4()),
        source_code=request.source_code,
        execution=execution,
        static_analysis=static_analysis,
        trace=trace,
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


@router.post("/root-cause")
async def root_cause_analysis(request: DebugRequest):
    """Perform root cause analysis. (Phase 4)"""
    return {"message": "Not implemented yet - coming in Phase 4"}


@router.post("/patch")
async def generate_patch(request: DebugRequest):
    """Generate a patch. (Phase 4)"""
    return {"message": "Not implemented yet - coming in Phase 4"}


@router.post("/validate")
async def validate_patch(request: DebugRequest):
    """Validate a patch. (Phase 5)"""
    return {"message": "Not implemented yet - coming in Phase 5"}
