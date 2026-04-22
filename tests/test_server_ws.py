"""Tests for WebSocket real-time event forwarding."""
import asyncio
import json
import pytest
from aiohttp.test_utils import TestClient, TestServer
from aiohttp import WSMsgType
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


async def test_flow_added_event(client, store):
    async with client.ws_connect("/ws/events") as ws:
        flow = FlowRecord(method="GET", url="http://test.com/api")
        store.add_flow(flow)
        msg = await asyncio.wait_for(ws.receive(), timeout=2.0)
        assert msg.type == WSMsgType.TEXT
        data = json.loads(msg.data)
        assert data["type"] == "flow_added"
        assert data["flow"]["method"] == "GET"
