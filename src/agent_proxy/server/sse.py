"""SSE handlers for AI endpoints."""
import asyncio
import json
from collections import Counter
from aiohttp import web

from agent_proxy.core.store import Store
from agent_proxy.agents.base import IntentRouter


def register_sse_routes(app: web.Application) -> None:
    """Register SSE (Server-Sent Events) routes for AI endpoints."""
    app.router.add_post("/api/ai/analyze", ai_analyze)
    app.router.add_post("/api/ai/security", ai_security)
    app.router.add_post("/api/ai/mock", ai_mock)
    app.router.add_post("/api/ai/query", ai_query)


async def _sse_response(request: web.Request, event_gen):
    """Helper: stream events from async generator to SSE."""
    resp = web.StreamResponse(
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
    await resp.prepare(request)

    try:
        async for event in event_gen:
            await resp.write(f"data: {json.dumps(event)}\n\n".encode())
    except asyncio.CancelledError:
        pass  # Client disconnected
    except Exception as e:
        await resp.write(f'data: {json.dumps({"type": "error", "message": str(e)})}\n\n'.encode())

    await resp.write(b'data: {"type": "done"}\n\n')
    return resp


async def _compute_stats(store: Store, flow_ids: list[str] | None = None) -> dict:
    """Compute local statistics immediately (milliseconds)."""
    flows = [store.flows[fid] for fid in flow_ids if fid in store.flows] if flow_ids else list(store.flows.values())
    methods = Counter(f.method for f in flows)
    endpoints = list(set(f.path for f in flows))
    avg_size = sum(f.size for f in flows) / len(flows) if flows else 0
    return {
        "type": "stats",
        "total": len(flows),
        "methods": dict(methods),
        "endpoints": endpoints[:20],
        "avg_size": round(avg_size),
    }


def _build_analysis_prompt(query: str, flows: list) -> str:
    """Build the prompt for the analysis agent (matches AnalysisAgent.execute logic)."""
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


async def _stream_llm_chunks(llm, system_prompt: str, user_prompt: str):
    """Stream LLM response chunks directly via SSE for real-time output."""
    try:
        async for chunk in llm.stream_response(system_prompt, user_prompt):
            yield {"type": "analysis", "chunk": chunk}
    except Exception as e:
        yield {"type": "error", "message": str(e)}


async def ai_analyze(request: web.Request) -> web.StreamResponse:
    """AI analysis — stats immediately, LLM streaming after."""
    store: Store = request.app["store"]
    agents: dict | None = request.app.get("agents")
    data = await request.json()
    query = data.get("query", "")
    flow_ids = data.get("flow_ids", [])

    async def event_gen():
        yield await _compute_stats(store, flow_ids or None)

        analysis_agent = (agents or {}).get("analysis")
        if analysis_agent and getattr(analysis_agent, "llm", None):
            flows = [store.flows[fid] for fid in flow_ids if fid in store.flows] if flow_ids else list(store.flows.values())
            prompt = _build_analysis_prompt(query, flows)
            async for event in _stream_llm_chunks(
                analysis_agent.llm,
                analysis_agent.get_system_prompt(),
                prompt,
            ):
                yield event

    return await _sse_response(request, event_gen())


async def ai_security(request: web.Request) -> web.StreamResponse:
    """AI security analysis — stats immediately, LLM streaming after."""
    store: Store = request.app["store"]
    agents: dict | None = request.app.get("agents")
    data = await request.json()
    flow_ids = data.get("flow_ids", [])

    async def event_gen():
        yield await _compute_stats(store, flow_ids or None)

        security_agent = (agents or {}).get("security")
        if security_agent and getattr(security_agent, "llm", None):
            flows = [store.flows[fid] for fid in flow_ids if fid in store.flows] if flow_ids else list(store.flows.values())
            prompt = f"用户请求: 安全分析\n\n流量数据:\n" + "\n".join(f"{f.method} {f.url}" for f in flows[:50])
            async for event in _stream_llm_chunks(
                security_agent.llm,
                security_agent.get_system_prompt(),
                prompt,
            ):
                yield event

    return await _sse_response(request, event_gen())


async def ai_mock(request: web.Request) -> web.StreamResponse:
    """AI mock data generation — stats optionally, LLM streaming after."""
    store: Store = request.app["store"]
    agents: dict | None = request.app.get("agents")
    data = await request.json()
    flow_ids = data.get("flow_ids", [])

    async def event_gen():
        if flow_ids:
            flows = [store.flows[fid] for fid in flow_ids if fid in store.flows]
            if flows:
                yield {"type": "stats", "total": len(flows)}

        mock_agent = (agents or {}).get("mock")
        if mock_agent and getattr(mock_agent, "llm", None):
            flows = [store.flows[fid] for fid in flow_ids if fid in store.flows] if flow_ids else []
            last_flow = flows[-1] if flows else None
            prompt = f"为以下接口生成 Mock 数据:\n{last_flow.method} {last_flow.url}" if last_flow else "生成 Mock 数据"
            async for event in _stream_llm_chunks(
                mock_agent.llm,
                mock_agent.get_system_prompt(),
                prompt,
            ):
                yield event

    return await _sse_response(request, event_gen())


async def ai_query(request: web.Request) -> web.StreamResponse:
    """General AI query with IntentRouter."""
    store: Store = request.app["store"]
    agents: dict | None = request.app.get("agents")
    data = await request.json()
    query = data.get("query", "")

    async def event_gen():
        agent_name = IntentRouter.route(query)
        agent = (agents or {}).get(agent_name)
        if not agent:
            yield {"type": "error", "message": "LLM not configured"}
            return
        if not getattr(agent, "llm", None):
            result = await agent.execute(query)
            yield {"type": "result", "content": result.message}
            return
        system_prompt = agent.get_system_prompt()
        user_prompt = query
        if agent_name == "analysis":
            user_prompt = _build_analysis_prompt(query, list(store.flows.values()))
        async for event in _stream_llm_chunks(agent.llm, system_prompt, user_prompt):
            yield event

    return await _sse_response(request, event_gen())
