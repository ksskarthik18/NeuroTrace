"""
NeuroTrace — Evaluation Metrics
Calculates and tracks debugging pipeline performance metrics.
Implementation: Phase 7
"""

from dataclasses import dataclass


@dataclass
class EvaluationMetrics:
    """Aggregated evaluation metrics across debug sessions."""
    total_sessions: int = 0
    localization_accuracy: float = 0.0   # % correct faulty line identified
    patch_success_rate: float = 0.0      # % patches that pass tests
    execution_success: float = 0.0       # % patches that run without error
    repair_accuracy: float = 0.0         # % semantically correct fixes
    false_patch_rate: float = 0.0        # % wrong but plausible fixes
    avg_confidence: float = 0.0          # mean confidence score
    avg_attempts: float = 0.0            # mean repair attempts needed
    avg_latency_ms: float = 0.0          # mean time per debug session


# TODO: Phase 7 — Implement metric calculation from debug_sessions table
