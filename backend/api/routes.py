"""
NeuroTrace API Routes
Defines all REST endpoints for the debugging pipeline.
"""

import uuid
from fastapi import APIRouter
from backend.config import get_settings
from backend.models import DebugRequest, DebugResponse, HealthResponse, ExecutionResult
from backend.debugger.sandbox import execute_code

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
    Currently runs Phase 1 (execution) only.
    Remaining phases will be wired in later.
    """
    execution = await execute_code(request.source_code)

    return DebugResponse(
        session_id=str(uuid.uuid4()),
        source_code=request.source_code,
        execution=execution,
    )


@router.post("/execute", response_model=ExecutionResult)
async def execute_code_endpoint(request: DebugRequest):
    """Execute code in the sandbox and return the result."""
    return await execute_code(request.source_code)


@router.post("/analyze")
async def analyze_code(request: DebugRequest):
    """Run static analysis. (Phase 2)"""
    return {"message": "Not implemented yet - coming in Phase 2"}


@router.post("/trace")
async def collect_trace(request: DebugRequest):
    """Collect runtime trace. (Phase 3)"""
    return {"message": "Not implemented yet - coming in Phase 3"}


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
