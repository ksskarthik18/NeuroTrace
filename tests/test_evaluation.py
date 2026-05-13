"""
Tests for Phase 7: benchmark dataset, evaluation metrics, and new API endpoints.
"""

import json
import pytest
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.database import init_db
from evaluation.metrics import EvaluationMetrics


# --- Dataset tests ---

def test_dataset_loads():
    """Bug dataset should load as valid JSON."""
    path = Path(__file__).parent.parent / "datasets" / "bugs.json"
    with open(path, "r", encoding="utf-8") as f:
        bugs = json.load(f)
    assert isinstance(bugs, list)
    assert len(bugs) >= 30


def test_dataset_structure():
    """Each bug should have required fields."""
    path = Path(__file__).parent.parent / "datasets" / "bugs.json"
    with open(path) as f:
        bugs = json.load(f)

    required = {"id", "category", "description", "source_code", "expected_exception"}
    for bug in bugs:
        missing = required - set(bug.keys())
        assert not missing, f"Bug {bug.get('id', '?')} missing: {missing}"


def test_dataset_unique_ids():
    """All bug IDs should be unique."""
    path = Path(__file__).parent.parent / "datasets" / "bugs.json"
    with open(path) as f:
        bugs = json.load(f)
    ids = [b["id"] for b in bugs]
    assert len(ids) == len(set(ids)), "Duplicate IDs found"


def test_dataset_categories():
    """Dataset should cover multiple bug categories."""
    path = Path(__file__).parent.parent / "datasets" / "bugs.json"
    with open(path) as f:
        bugs = json.load(f)
    categories = set(b["category"] for b in bugs)
    assert len(categories) >= 5, f"Only {len(categories)} categories"


# --- Metrics tests ---

def test_metrics_defaults():
    """Default metrics should be zero."""
    m = EvaluationMetrics()
    assert m.total_sessions == 0
    assert m.patch_success_rate == 0.0
    assert m.avg_confidence == 0.0


def test_metrics_to_dict():
    """Metrics should serialize to dict."""
    m = EvaluationMetrics(total_sessions=10, patch_success_rate=0.8)
    d = m.to_dict()
    assert d["total_sessions"] == 10
    assert d["patch_success_rate"] == 0.8
    assert "validation_breakdown" in d


# --- API endpoint tests ---

@pytest.fixture
async def client():
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_sessions_endpoint(client):
    """GET /sessions should return a list."""
    resp = await client.get("/api/v1/sessions")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_session_not_found(client):
    """GET /sessions/{id} should return error for nonexistent session."""
    resp = await client.get("/api/v1/sessions/nonexistent-id")
    assert resp.status_code == 200
    data = resp.json()
    assert "error" in data


@pytest.mark.asyncio
async def test_metrics_endpoint(client):
    """GET /metrics should return metric fields."""
    resp = await client.get("/api/v1/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_sessions" in data
    assert "patch_success_rate" in data
    assert "avg_confidence" in data
    assert "validation_breakdown" in data
