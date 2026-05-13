"""
NeuroTrace - Benchmark Runner
Batch-runs the debugging pipeline on a curated dataset of bugs
and logs results to the database for evaluation.

Usage:
    python -m evaluation.benchmark_runner
    python -m evaluation.benchmark_runner --max 5
"""

import json
import time
import asyncio
import argparse
from pathlib import Path

from backend.database import init_db, async_session, DebugSession
from backend.debugger.sandbox import execute_code
from backend.debugger.static_analyzer import analyze_code
from backend.debugger.trace_collector import collect_trace
from backend.llm.root_cause import analyze_root_cause
from backend.patcher.generator import generate_patch
from backend.validator.runner import validate_patch

DATASET_PATH = Path(__file__).parent.parent / "datasets" / "bugs.json"


def load_bugs(max_bugs: int | None = None) -> list[dict]:
    """Load bug samples from the dataset file."""
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        bugs = json.load(f)
    if max_bugs:
        bugs = bugs[:max_bugs]
    return bugs


async def run_single_bug(bug: dict) -> dict:
    """Run the full pipeline on a single bug and return results."""
    source = bug["source_code"]
    test_code = bug.get("test_code")
    start = time.perf_counter()

    try:
        execution = await execute_code(source)
        static_analysis = await analyze_code(source)
        trace = await collect_trace(source)
        root_cause = await analyze_root_cause(source, trace, static_analysis)
        patch = await generate_patch(source, root_cause)
        validation = await validate_patch(
            source, patch.patched_code, root_cause, test_code
        )

        latency_ms = int((time.perf_counter() - start) * 1000)

        return {
            "id": bug["id"],
            "category": bug["category"],
            "description": bug["description"],
            "bug_type": root_cause.bug_type,
            "root_cause": root_cause.root_cause,
            "patched_code": validation.patched_code,
            "diff": patch.diff,
            "confidence": validation.confidence,
            "validation_status": validation.status.value,
            "attempts": validation.attempts,
            "latency_ms": latency_ms,
            "error": None,
        }

    except Exception as e:
        latency_ms = int((time.perf_counter() - start) * 1000)
        return {
            "id": bug["id"],
            "category": bug["category"],
            "description": bug["description"],
            "bug_type": bug.get("expected_exception", "unknown"),
            "root_cause": "",
            "patched_code": "",
            "diff": "",
            "confidence": 0.0,
            "validation_status": "error",
            "attempts": 0,
            "latency_ms": latency_ms,
            "error": f"{type(e).__name__}: {str(e)}",
        }


async def save_result(result: dict):
    """Save a benchmark result to the database."""
    session_record = DebugSession(
        id=result["id"],
        source_code="",
        bug_type=result["bug_type"],
        root_cause=result["root_cause"],
        patched_code=result["patched_code"],
        diff=result["diff"],
        confidence=result["confidence"],
        validation_status=result["validation_status"],
        attempts=result["attempts"],
        latency_ms=result["latency_ms"],
    )
    async with async_session() as session:
        # upsert: delete existing, then insert
        existing = await session.get(DebugSession, result["id"])
        if existing:
            await session.delete(existing)
            await session.flush()
        session.add(session_record)
        await session.commit()


async def run_benchmark(max_bugs: int | None = None):
    """Run the full benchmark suite."""
    await init_db()
    bugs = load_bugs(max_bugs)
    total = len(bugs)
    results = []

    print(f"\n{'='*60}")
    print(f"  NeuroTrace Benchmark Runner")
    print(f"  Running {total} bugs")
    print(f"{'='*60}\n")

    validated = 0
    failed = 0
    errors = 0

    for i, bug in enumerate(bugs, 1):
        print(f"[{i}/{total}] {bug['id']}: {bug['description']}...", end=" ", flush=True)
        result = await run_single_bug(bug)
        await save_result(result)
        results.append(result)

        if result["validation_status"] == "validated":
            validated += 1
            print(f"PASS (confidence: {result['confidence']}, {result['latency_ms']}ms)")
        elif result["error"]:
            errors += 1
            print(f"ERROR: {result['error'][:60]}")
        else:
            failed += 1
            print(f"FAIL ({result['latency_ms']}ms)")

    print(f"\n{'='*60}")
    print(f"  Results: {validated} passed / {failed} failed / {errors} errors")
    print(f"  Success Rate: {validated/total*100:.1f}%")
    if results:
        avg_conf = sum(r["confidence"] for r in results) / len(results)
        avg_lat = sum(r["latency_ms"] for r in results) / len(results)
        print(f"  Avg Confidence: {avg_conf:.2f}")
        print(f"  Avg Latency: {avg_lat:.0f}ms")
    print(f"{'='*60}\n")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NeuroTrace Benchmark Runner")
    parser.add_argument("--max", type=int, default=None, help="Max bugs to run")
    args = parser.parse_args()
    asyncio.run(run_benchmark(args.max))
