"""
NeuroTrace - Evaluation Metrics
Calculates and tracks debugging pipeline performance from stored sessions.
"""

from dataclasses import dataclass, asdict
from sqlalchemy import select, func
from backend.database import async_session, DebugSession


@dataclass
class EvaluationMetrics:
    """Aggregated evaluation metrics across debug sessions."""
    total_sessions: int = 0
    patch_success_rate: float = 0.0
    execution_success: float = 0.0
    avg_confidence: float = 0.0
    avg_attempts: float = 0.0
    avg_latency_ms: float = 0.0
    validation_breakdown: dict = None

    def __post_init__(self):
        if self.validation_breakdown is None:
            self.validation_breakdown = {}

    def to_dict(self) -> dict:
        return asdict(self)


async def compute_metrics() -> EvaluationMetrics:
    """Compute aggregate metrics from all stored debug sessions."""
    async with async_session() as session:
        total = await session.scalar(select(func.count(DebugSession.id)))
        if not total or total == 0:
            return EvaluationMetrics()

        validated = await session.scalar(
            select(func.count(DebugSession.id)).where(
                DebugSession.validation_status == "validated"
            )
        )
        failed = await session.scalar(
            select(func.count(DebugSession.id)).where(
                DebugSession.validation_status == "failed"
            )
        )

        avg_confidence = await session.scalar(
            select(func.avg(DebugSession.confidence))
        ) or 0.0

        avg_attempts = await session.scalar(
            select(func.avg(DebugSession.attempts))
        ) or 0.0

        avg_latency = await session.scalar(
            select(func.avg(DebugSession.latency_ms))
        ) or 0.0

        # count sessions where the patched code ran without error
        exec_success = validated  # validated implies execution succeeded

        return EvaluationMetrics(
            total_sessions=total,
            patch_success_rate=round(validated / total, 3) if total else 0.0,
            execution_success=round(exec_success / total, 3) if total else 0.0,
            avg_confidence=round(avg_confidence, 3),
            avg_attempts=round(avg_attempts, 2),
            avg_latency_ms=round(avg_latency, 1),
            validation_breakdown={
                "validated": validated,
                "failed": failed,
                "other": total - validated - failed,
            },
        )
