import asyncio
import json
import pytest
from aiohttp.test_utils import TestClient, TestServer
from agent_proxy.core.store import Store
from agent_proxy.core.models import FlowRecord
from agent_proxy.server.app import create_app


@pytest.fixture
def store():
    s = Store()
    s.add_flow(FlowRecord(method="GET", url="http://test.com/api"))
    s.add_flow(FlowRecord(method="POST", url="http://test.com/users"))
    return s


@pytest.fixture
async def client(store):
    app = create_app(store, agents={})
    async with TestClient(TestServer(app)) as tc:
        yield tc


@pytest.fixture
async def client_with_llm(store):
    """Client with a mocked LLM that streams response chunks."""
    from unittest.mock import AsyncMock
    from collections import Counter

    class FakeLLM:
        async def stream_response(self, system_prompt, user_prompt, max_retries=3):
            for chunk in ["正在分析", f"，共发现 {len(store.flows)} 个请求", "，主要集中在 /api 路径"]:
                yield chunk

    from agent_proxy.agents.analysis_agent import AnalysisAgent
    fake_agent = AnalysisAgent.__new__(AnalysisAgent)
    fake_agent.llm = FakeLLM()
    fake_agent.get_system_prompt = lambda: "Analyze traffic"

    # NOTE: AnalysisAgent does not have a build_prompt() method.
    # The SSE handler constructs the prompt inline.
    def build_prompt(query, flows):
        methods = Counter(f.method for f in flows)
        endpoints = list(set(f.path for f in flows))
        avg_size = sum(f.size for f in flows) / len(flows) if flows else 0
        return (
            f"用户请求: {query}\n\n"
            f"总请求数: {len(flows)}\n"
            f"请求方法: {dict(methods)}\n"
            f"接口列表: {endpoints[:20]}\n"
            f"平均响应大小: {avg_size:.0f} 字节\n"
        )
    fake_agent.build_prompt = build_prompt

    app = create_app(store, agents={"analysis": fake_agent})
    async with TestClient(TestServer(app)) as tc:
        yield tc


async def test_analyze_stats(client):
    """Test that stats are returned immediately without LLM."""
    resp = await client.post("/api/ai/analyze", json={"query": "统计接口"})
    assert resp.status == 200
    assert resp.content_type == "text/event-stream"

    messages = []
    async for line in resp.content:
        text = line.decode().strip()
        if text.startswith("data: "):
            data = json.loads(text[6:])
            messages.append(data)
            if data.get("type") == "done":
                break

    types = [m["type"] for m in messages]
    assert "stats" in types
    assert "done" in types
    stats = next(m for m in messages if m["type"] == "stats")
    assert stats["total"] == 2


async def test_analyze_with_llm(client_with_llm):
    """Test that LLM response is streamed chunk-by-chunk."""
    resp = await client_with_llm.post("/api/ai/analyze", json={"query": "分析流量"})
    assert resp.status == 200

    messages = []
    async for line in resp.content:
        text = line.decode().strip()
        if text.startswith("data: "):
            data = json.loads(text[6:])
            messages.append(data)
            if data.get("type") == "done":
                break

    types = [m["type"] for m in messages]
    assert "stats" in types
    assert "analysis" in types
    assert "done" in types
    analysis_msgs = [m for m in messages if m["type"] == "analysis"]
    assert all("chunk" in m for m in analysis_msgs)
