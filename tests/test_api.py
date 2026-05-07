"""
Tests for the NeuroTrace API — Phase 0 (health check & basic endpoints).
"""

import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app


@pytest.fixture
async def client():
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_root(client):
    """Root endpoint returns app info."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "NeuroTrace"
    assert "version" in data


@pytest.mark.asyncio
async def test_health(client):
    """Health endpoint returns ok status."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_debug_stub(client):
    """Debug endpoint accepts code and returns a session ID."""
    response = await client.post(
        "/api/v1/debug",
        json={"source_code": "print('hello')"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["source_code"] == "print('hello')"


@pytest.mark.asyncio
async def test_execute_stub(client):
    """Execute endpoint returns not-implemented message."""
    response = await client.post(
        "/api/v1/execute",
        json={"source_code": "x = 1"}
    )
    assert response.status_code == 200
    assert "Phase 1" in response.json()["message"]
