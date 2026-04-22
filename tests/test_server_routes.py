"""Tests for server routes."""
import pytest
from aiohttp.test_utils import TestClient, TestServer
from agent_proxy.core.store import Store
from agent_proxy.core.models import FlowRecord
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


# --- Flow endpoints ---


async def test_get_flows(client, store):
    store.add_flow(FlowRecord(method="GET", url="http://api.test.com/v1"))
    store.add_flow(FlowRecord(method="POST", url="http://api.test.com/v2"))
    resp = await client.get("/api/flows")
    assert resp.status == 200
    data = await resp.json()
    assert len(data) == 2


async def test_get_flows_pagination(client, store):
    for i in range(5):
        store.add_flow(FlowRecord(method="GET", url=f"http://test.com/api/{i}"))
    resp = await client.get("/api/flows?limit=2&offset=2")
    assert resp.status == 200
    data = await resp.json()
    assert len(data) == 2


async def test_get_flow_by_id(client, store):
    flow = FlowRecord(method="GET", url="http://test.com/api")
    store.add_flow(flow)
    resp = await client.get(f"/api/flows/{flow.id}")
    assert resp.status == 200
    data = await resp.json()
    assert data["method"] == "GET"


async def test_get_flow_not_found(client):
    resp = await client.get("/api/flows/nonexistent")
    assert resp.status == 404


async def test_get_flow_body(client, store):
    flow = FlowRecord(
        method="POST",
        url="http://test.com/api",
        request_body=b'{"name":"test"}',
        response_body=b'{"id":1}',
    )
    store.add_flow(flow)
    resp = await client.get(f"/api/flows/{flow.id}/body?part=request")
    assert resp.status == 200
    text = await resp.text()
    assert "name" in text
    resp2 = await client.get(f"/api/flows/{flow.id}/body?part=response")
    assert resp2.status == 200
    text2 = await resp2.text()
    assert "id" in text2
    # Invalid part
    resp3 = await client.get(f"/api/flows/{flow.id}/body?part=invalid")
    assert resp3.status == 400


# --- Domain endpoints ---

async def test_get_domains(client, store):
    store.add_domain("api.test.com")
    resp = await client.get("/api/domains")
    assert resp.status == 200
    data = await resp.json()
    assert "api.test.com" in data


async def test_add_domain(client, store):
    resp = await client.post("/api/domains", json={"domain": "new.test.com"})
    assert resp.status == 200
    assert "new.test.com" in store.domains


async def test_add_duplicate_domain(client, store):
    resp1 = await client.post("/api/domains", json={"domain": "dup.test.com"})
    assert resp1.status == 200
    resp2 = await client.post("/api/domains", json={"domain": "dup.test.com"})
    assert resp2.status == 409


async def test_delete_domain(client, store):
    store.add_domain("del.test.com")
    resp = await client.delete("/api/domains/del.test.com")
    assert resp.status == 200
    assert "del.test.com" not in store.domains


# --- Rule endpoints ---

async def test_get_rules(client, store):
    resp = await client.get("/api/rules")
    assert resp.status == 200
    data = await resp.json()
    assert isinstance(data, list)


async def test_create_rule(client, store):
    resp = await client.post("/api/rules", json={
        "description": "Test rule",
        "condition": {"url_pattern": "/api/test"},
        "action": {"type": "mock", "status_code": 200, "body": "ok"},
    })
    assert resp.status == 201
    data = await resp.json()
    assert data["description"] == "Test rule"
    assert len(store.rules) == 1
