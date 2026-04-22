"""Tests for server routes."""
import pytest
from aiohttp.test_utils import TestClient, TestServer
from agent_proxy.core.store import Store
from agent_proxy.server.app import create_app


@pytest.fixture
def store():
    return Store()


@pytest.fixture
async def client(store):
    app = create_app(store)
    async with TestClient(TestServer(app)) as tc:
        yield tc


async def test_health_endpoint(client):
    resp = await client.get("/api/health")
    assert resp.status == 200
    data = await resp.json()
    assert data["status"] == "ok"
    assert "flows" in data
    assert "domains" in data
