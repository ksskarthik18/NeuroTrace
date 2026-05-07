"""
NeuroTrace API Routes
Defines all REST endpoints for the debugging pipeline.
"""

from fastapi import APIRouter
from backend.config import get_settings
from backend.models import DebugRequest, DebugResponse, HealthResponse

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
    6. Validate patch

    Currently returns a stub response — each module will be
    wired in during subsequent phases.
    """
    import uuid

    return DebugResponse(
        session_id=str(uuid.uuid4()),
        source_code=request.source_code,
    )


@router.post("/execute")
async def execute_code(request: DebugRequest):
    """Execute code in sandbox. (Phase 1)"""
    return {"message": "Not implemented yet - coming in Phase 1"}


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
