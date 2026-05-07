"""
Tests for the NeuroTrace API endpoints.
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
async def test_debug_runs_code(client):
    """Debug endpoint executes code and returns execution result."""
    response = await client.post(
        "/api/v1/debug",
        json={"source_code": "print('hello')"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["source_code"] == "print('hello')"
    assert data["execution"] is not None
    assert data["execution"]["return_code"] == 0
    assert "hello" in data["execution"]["stdout"]


@pytest.mark.asyncio
async def test_execute_endpoint(client):
    """Execute endpoint runs code and returns structured result."""
    response = await client.post(
        "/api/v1/execute",
        json={"source_code": "print(2 + 2)"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["return_code"] == 0
    assert "4" in data["stdout"]


@pytest.mark.asyncio
async def test_execute_with_error(client):
    """Execute endpoint captures errors properly."""
    response = await client.post(
        "/api/v1/execute",
        json={"source_code": "1/0"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["return_code"] != 0
    assert "ZeroDivisionError" in data["stderr"]
