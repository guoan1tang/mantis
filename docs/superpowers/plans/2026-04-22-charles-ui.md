# Charles-like Desktop UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Charles-style desktop app with AI features, replacing the current TUI

**Architecture:** Python aiohttp HTTP server (REST + WebSocket + SSE) serves as backend; Vite + React + TypeScript frontend runs inside Electron shell

**Tech Stack:** Python 3.12+, aiohttp, Vite, React, TypeScript, Electron

**Phases:**
- **Phase 1 (Tasks 1-6):** Python HTTP server — fully testable independently, existing TUI unchanged
- **Phase 2 (Tasks 7-10):** React + Electron frontend — depends on Phase 1 API

Each phase produces working, testable software.

---

## File Map

### New Files (Phase 1 - Python Server)
| File | Responsibility |
|------|---------------|
| `src/agent_proxy/server/__init__.py` | Package init |
| `src/agent_proxy/server/app.py` | aiohttp Application factory, routes registration |
| `src/agent_proxy/server/routes.py` | REST API route handlers (flows, domains, rules) |
| `src/agent_proxy/server/sse.py` | SSE handlers for AI endpoints |
| `src/agent_proxy/server/ws.py` | WebSocket handler for real-time flow events |
| `src/agent_proxy/server/serializers.py` | FlowRecord → JSON serialization, Base64 encoding |
| `tests/test_server_routes.py` | Tests for REST API routes |
| `tests/test_server_sse.py` | Tests for SSE handlers |
| `tests/test_server_ws.py` | Tests for WebSocket handler |
| `tests/test_server_serializers.py` | Tests for serialization |

### New Files (Phase 2 - Frontend)
| File | Responsibility |
|------|---------------|
| `src/web/package.json` | Node.js dependencies |
| `src/web/vite.config.ts` | Vite configuration |
| `src/web/tsconfig.json` | TypeScript config |
| `src/web/index.html` | Entry HTML |
| `src/web/src/main.tsx` | React entry point |
| `src/web/src/App.tsx` | Main app layout (3-column + AI panel) |
| `src/web/src/types/flow.ts` | TypeScript types for FlowRecord |
| `src/web/src/types/api.ts` | TypeScript types for API responses |
| `src/web/src/services/api.ts` | HTTP API service (fetch) |
| `src/web/src/services/ws.ts` | WebSocket service for real-time events |
| `src/web/src/services/sse.ts` | SSE service for AI streaming |
| `src/web/src/components/FlowList.tsx` | Flow table with filtering/sorting |
| `src/web/src/components/FlowDetail.tsx` | Request/Response detail panels |
| `src/web/src/components/DomainTree.tsx` | Domain sidebar tree |
| `src/web/src/components/AIPanel.tsx` | AI chat panel with SSE streaming |
| `src/web/src/components/QuickActions.tsx` | AI quick command buttons |
| `src/web/src/components/StatusBar.tsx` | Connection status bar |
| `src/web/electron/main.js` | Electron main process |
| `src/web/electron/preload.js` | Electron preload script |

### Modified Files (Phase 1)
| File | Change |
|------|--------|
| `pyproject.toml` | Add `aiohttp>=3.9` dependency |
| `src/agent_proxy/core/models.py` | Add `to_dict()` method to FlowRecord |
| `src/agent_proxy/agents/llm.py` | Add `stream_response()` async generator method |
| `src/agent_proxy/cli.py` | Add `--server` flag to launch server mode (no TUI) |

---

## Phase 1: Python HTTP Server

### Task 1: Add aiohttp dependency + FlowRecord serialization

**Files:**
- Modify: `pyproject.toml`
- Modify: `src/agent_proxy/core/models.py`
- Test: `tests/test_models.py`

- [ ] **Step 1: Add aiohttp dependency**

Add `"aiohttp>=3.9"` to `pyproject.toml` dependencies:

```toml
dependencies = [
    "mitmproxy>=10.0",
    "textual>=0.50",
    "openai>=1.0",
    "pyyaml>=6.0",
    "qrcode[pil]>=7.4",
    "rich>=13.0",
    "aiohttp>=3.9",
]
```

Run: `pip install -e .`

- [ ] **Step 2: Add `to_dict()` method to FlowRecord**

Add a `to_dict()` method to `FlowRecord` in `src/agent_proxy/core/models.py`:

```python
    def to_dict(self, include_body: bool = True) -> dict:
        """Convert to JSON-serializable dict."""
        result: dict = {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "method": self.method,
            "url": self.url,
            "host": self.host,
            "path": self.path,
            "status_code": self.status_code,
            "request_headers": self.request_headers,
            "response_headers": self.response_headers,
            "content_type": self.content_type,
            "size": self.size,
            "duration_ms": self.duration_ms,
            "intercepted": self.intercepted,
            "modified": self.modified,
            "tags": self.tags,
            "security_issues": self.security_issues,
        }
        if include_body:
            import base64
            result["request_body_base64"] = (
                base64.b64encode(self.request_body).decode() if self.request_body else None
            )
            result["response_body_base64"] = (
                base64.b64encode(self.response_body).decode() if self.response_body else None
            )
        return result
```

- [ ] **Step 3: Write test for `to_dict()`**

In `tests/test_models.py`, add:

```python
from agent_proxy.core.models import FlowRecord
import base64


def test_flow_to_dict():
    flow = FlowRecord(
        method="POST",
        url="http://api.example.com/v1/users",
        status_code=200,
        request_headers={"Content-Type": "application/json"},
        request_body=b'{"name": "test"}',
        response_body=b'{"id": 1}',
        size=100,
        duration_ms=45.0,
    )
    d = flow.to_dict()
    assert d["id"] == flow.id
    assert d["method"] == "POST"
    assert d["host"] == "api.example.com"
    assert d["path"] == "/v1/users"
    assert d["status_code"] == 200
    assert d["request_body_base64"] == base64.b64encode(b'{"name": "test"}').decode()
    assert d["response_body_base64"] == base64.b64encode(b'{"id": 1}').decode()


def test_flow_to_dict_no_body():
    flow = FlowRecord(method="GET", url="http://example.com/")
    d = flow.to_dict(include_body=False)
    assert "request_body_base64" not in d
    assert "response_body_base64" not in d
```

- [ ] **Step 4: Run tests**

Run: `.venv/bin/python -m pytest tests/test_models.py -v`
Expected: All pass

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/agent_proxy/core/models.py tests/test_models.py
git commit -m "feat: add aiohttp dep and FlowRecord.to_dict() for API serialization"
```

---

### Task 2: Server App Factory + Health Endpoint

**Files:**
- Create: `src/agent_proxy/server/__init__.py`
- Create: `src/agent_proxy/server/app.py`
- Test: `tests/test_server_routes.py`

- [ ] **Step 1: Create server package**

`src/agent_proxy/server/__init__.py`:
```python
from agent_proxy.server.app import create_app

__all__ = ["create_app"]
```

- [ ] **Step 2: Write test for health endpoint**

In `tests/test_server_routes.py`:

```python
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
```

- [ ] **Step 3: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_server_routes.py -v`
Expected: ModuleNotFoundError (server module doesn't exist yet)

- [ ] **Step 4: Implement create_app with health endpoint**

`src/agent_proxy/server/app.py`:

```python
"""aiohttp application factory and route registration."""
from aiohttp import web

from agent_proxy.core.store import Store


def create_app(store: Store) -> web.Application:
    app = web.Application()
    app["store"] = store
    app.router.add_get("/api/health", health_handler)
    return app


async def health_handler(request: web.Request) -> web.Response:
    store: Store = request.app["store"]
    return web.json_response({
        "status": "ok",
        "flows": len(store.flows),
        "domains": store.domains,
        "rules": len(store.rules),
    })
```

- [ ] **Step 5: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_server_routes.py::test_health_endpoint -v`
Expected: PASS

- [ ] **Step 6: Add CLI --server flag**

In `src/agent_proxy/cli.py`, add a new entry point function:

```python
def server_main():
    """Launch API server without TUI."""
    import asyncio
    from aiohttp import web
    from agent_proxy.server.app import create_app

    args = parse_args()
    # ... same config setup as main() ...

    store = Store(config)
    llm_client = LLMClient(config.llm) if config.llm.api_key else None
    agents = { ... }  # same as main()

    engine = ProxyEngine(store, config)

    async def run():
        await engine.start()
        app = create_app(store)
        # Add WebSocket, SSE, agent handlers to app
        # ...
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", config.proxy.listen_port + 1000)
        await site.start()
        rich.print(f"[bold green]API Server[/bold green] running on http://127.0.0.1:{config.proxy.listen_port + 1000}")
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            pass
        finally:
            await engine.stop()
            await runner.cleanup()

    asyncio.run(run())
```

This is the skeleton — full implementation comes in Tasks 4-5.

- [ ] **Step 7: Commit**

```bash
git add src/agent_proxy/server/__init__.py src/agent_proxy/server/app.py tests/test_server_routes.py src/agent_proxy/cli.py
git commit -m "feat: add aiohttp app factory and health endpoint"
```

---

### Task 3: REST API Routes (Flows, Domains, Rules)

**Files:**
- Create: `src/agent_proxy/server/routes.py`
- Modify: `src/agent_proxy/server/app.py`
- Test: `tests/test_server_routes.py`

- [ ] **Step 1: Write tests for flow endpoints**

Append to `tests/test_server_routes.py`:

```python
from agent_proxy.core.models import FlowRecord


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
```

- [ ] **Step 2: Write tests for domain endpoints**

```python
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
```

- [ ] **Step 3: Write tests for rule endpoints**

```python
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
```

- [ ] **Step 4: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_server_routes.py -v`
Expected: FAIL (endpoints not registered)

- [ ] **Step 5: Implement route handlers**

`src/agent_proxy/server/routes.py`:

```python
"""REST API route handlers for flows, domains, rules."""
from aiohttp import web

from agent_proxy.core.store import Store
from agent_proxy.core.models import ProxyRule, RuleCondition, RuleAction


def register_routes(app: web.Application) -> None:
    app.router.add_get("/api/flows", list_flows)
    app.router.add_get("/api/flows/{flow_id}", get_flow)
    app.router.add_get("/api/flows/{flow_id}/body", get_flow_body)
    app.router.add_get("/api/domains", list_domains)
    app.router.add_post("/api/domains", add_domain)
    app.router.add_delete("/api/domains/{domain}", delete_domain)
    app.router.add_get("/api/rules", list_rules)
    app.router.add_post("/api/rules", create_rule)


async def list_flows(request: web.Request) -> web.Response:
    store: Store = request.app["store"]
    limit = int(request.query.get("limit", 100))
    offset = int(request.query.get("offset", 0))
    flows = list(store.flows.values())
    page = flows[offset:offset + limit]
    return web.json_response([f.to_dict(include_body=False) for f in page])


async def get_flow(request: web.Request) -> web.Response:
    store: Store = request.app["store"]
    flow = store.flows.get(request.match_info["flow_id"])
    if not flow:
        return web.json_response({"error": "Flow not found"}, status=404)
    return web.json_response(flow.to_dict())


async def get_flow_body(request: web.Request) -> web.Response:
    """Get raw request or response body by flow ID."""
    store: Store = request.app["store"]
    flow = store.flows.get(request.match_info["flow_id"])
    if not flow:
        return web.json_response({"error": "Flow not found"}, status=404)
    part = request.query.get("part", "request")
    body = flow.request_body if part == "request" else flow.response_body if part == "response" else None
    if body is None:
        return web.Response(status=204)  # No content
    try:
        text = body.decode("utf-8", errors="replace")
    except Exception:
        import base64
        return web.json_response({"base64": base64.b64encode(body).decode()})
    return web.Response(text=text, content_type=flow.content_type or "text/plain")


async def list_domains(request: web.Request) -> web.Response:
    store: Store = request.app["store"]
    return web.json_response(store.domains)


async def add_domain(request: web.Request) -> web.Response:
    store: Store = request.app["store"]
    data = await request.json()
    domain = data.get("domain", "")
    if not domain:
        return web.json_response({"error": "Domain required"}, status=400)
    if not store.add_domain(domain):
        return web.json_response({"error": "Domain already exists"}, status=409)
    return web.json_response({"domain": domain})


async def delete_domain(request: web.Request) -> web.Response:
    store: Store = request.app["store"]
    domain = request.match_info["domain"]
    if not store.remove_domain(domain):
        return web.json_response({"error": "Domain not found"}, status=404)
    return web.json_response({"domain": domain})


async def list_rules(request: web.Request) -> web.Response:
    store: Store = request.app["store"]
    return web.json_response([_rule_to_dict(r) for r in store.rules])


async def create_rule(request: web.Request) -> web.Response:
    store: Store = request.app["store"]
    data = await request.json()
    cond_data = data.pop("condition", {})
    action_data = data.pop("action", {})
    rule = ProxyRule(
        description=data.get("description", ""),
        condition=RuleCondition(**cond_data),
        action=RuleAction(**action_data),
        source=data.get("source", "manual"),
    )
    store.add_rule(rule)
    return web.json_response(_rule_to_dict(rule), status=201)


def _rule_to_dict(rule: ProxyRule) -> dict:
    return {
        "id": rule.id,
        "description": rule.description,
        "enabled": rule.enabled,
        "source": rule.source,
        "condition": {
            "url_pattern": rule.condition.url_pattern,
            "methods": rule.condition.methods,
            "header_match": rule.condition.header_match,
        },
        "action": {
            "type": rule.action.type,
            "status_code": rule.action.status_code,
            "headers": rule.action.headers,
            "body_base64": (
                __import__("base64").b64encode(rule.action.body).decode()
                if rule.action.body else None
            ),
        },
    }
```

Then register in `app.py`:

```python
from agent_proxy.server.routes import register_routes

def create_app(store: Store) -> web.Application:
    app = web.Application()
    app["store"] = store
    app.router.add_get("/api/health", health_handler)
    register_routes(app)
    return app
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_server_routes.py -v`
Expected: All PASS

- [ ] **Step 7: Commit**

```bash
git add src/agent_proxy/server/routes.py tests/test_server_routes.py src/agent_proxy/server/app.py
git commit -m "feat: add REST API routes for flows, domains, rules"
```

---

### Task 4: WebSocket Real-Time Events

**Files:**
- Create: `src/agent_proxy/server/ws.py`
- Modify: `src/agent_proxy/server/app.py`
- Test: `tests/test_server_ws.py`

- [ ] **Step 1: Write test for WebSocket event broadcast**

`tests/test_server_ws.py`:

```python
import asyncio
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
        import json
        data = json.loads(msg.data)
        assert data["type"] == "flow_added"
        assert data["flow"]["method"] == "GET"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_server_ws.py -v`
Expected: FAIL (WebSocket endpoint doesn't exist)

- [ ] **Step 3: Implement WebSocket handler**

`src/agent_proxy/server/ws.py`:

```python
"""WebSocket handler for real-time flow events."""
import asyncio
import json
from aiohttp import web

from agent_proxy.core.store import Store


async def websocket_handler(request: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    store: Store = request.app["store"]
    # Register a listener that pushes events to this connection
    task = asyncio.create_task(_forward_events(ws, store))

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.ERROR:
                break
    finally:
        task.cancel()

    return ws


async def _forward_events(ws: web.WebSocketResponse, store: Store) -> None:
    """Forward flow_events and rule_events to WebSocket."""
    while True:
        try:
            # Use asyncio.wait_for with timeout to allow cancellation
            done, _ = await asyncio.wait(
                [
                    asyncio.create_task(store.flow_events.get()),
                    asyncio.create_task(store.rule_events.get()),
                ],
                return_when=asyncio.FIRST_COMPLETED,
                timeout=1.0,
            )
            for task in done:
                obj = task.result()
                if hasattr(obj, "to_dict"):
                    event = {"type": "flow_added", "flow": obj.to_dict()}
                else:
                    from agent_proxy.server.routes import _rule_to_dict
                    event = {"type": "rule_added", "rule": _rule_to_dict(obj)}
                await ws.send_json(event)
        except asyncio.CancelledError:
            break
        except Exception:
            pass
```

Register in `app.py`:

```python
from agent_proxy.server.ws import websocket_handler

def create_app(store: Store) -> web.Application:
    app = web.Application()
    app["store"] = store
    app.router.add_get("/api/health", health_handler)
    register_routes(app)
    app.router.add_get("/ws/events", websocket_handler)
    return app
```

- [ ] **Step 4: Fix the test** — The `_forward_events` uses `asyncio.wait` with two competing `get()` tasks, but both blocks will block forever since only one queue has data. Let me use a simpler approach:

```python
async def _forward_events(ws: web.WebSocketResponse, store: Store) -> None:
    """Forward flow_events and rule_events to WebSocket."""
    try:
        while True:
            try:
                flow = await asyncio.wait_for(store.flow_events.get(), timeout=0.5)
                await ws.send_json({"type": "flow_added", "flow": flow.to_dict()})
            except asyncio.TimeoutError:
                pass
            try:
                rule = await asyncio.wait_for(store.rule_events.get(), timeout=0.5)
                await ws.send_json({"type": "rule_added", "rule": _rule_to_dict(rule)})
            except asyncio.TimeoutError:
                pass
    except asyncio.CancelledError:
        pass  # Connection closed, clean exit
```

- [ ] **Step 5: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_server_ws.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/agent_proxy/server/ws.py tests/test_server_ws.py src/agent_proxy/server/app.py
git commit -m "feat: add WebSocket real-time event forwarding"
```

---

### Task 5: SSE AI Endpoints

**Files:**
- Create: `src/agent_proxy/server/sse.py`
- Modify: `src/agent_proxy/server/app.py`
- Modify: `src/agent_proxy/agents/llm.py` (add streaming method)
- Test: `tests/test_server_sse.py`

- [ ] **Step 1: Add streaming method to LLMClient**

Add to `src/agent_proxy/agents/llm.py`:

```python
    async def stream_response(
        self,
        system_prompt: str,
        user_prompt: str,
        max_retries: int = 3,
    ):
        """Stream LLM response chunks using streaming API. Yields text chunks."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        for attempt in range(max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=self.config.model,
                    messages=messages,
                    temperature=0.1,
                    stream=True,
                )
                async for chunk in response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
                return
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
```

- [ ] **Step 2: Write test for SSE stats endpoint**

`tests/test_server_sse.py`:

```python
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

    class FakeLLM:
        async def stream_response(self, system_prompt, user_prompt, max_retries=3):
            for chunk in ["正在分析", f"，共发现 {len(store.flows)} 个请求", "，主要集中在 /api 路径"]:
                yield chunk

    from agent_proxy.agents.analysis import AnalysisAgent
    fake_agent = AnalysisAgent.__new__(AnalysisAgent)
    fake_agent.llm = FakeLLM()
    fake_agent.get_system_prompt = lambda: "Analyze traffic"
    fake_agent.build_prompt = lambda q, flows: q

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

    # Should have at least stats + done (no LLM = no analysis chunks)
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
    # Each analysis event should have a "chunk" field (string), not "content"
    analysis_msgs = [m for m in messages if m["type"] == "analysis"]
    assert all("chunk" in m for m in analysis_msgs)
```

- [ ] **Step 3: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_server_sse.py -v`
Expected: FAIL

- [ ] **Step 4: Implement SSE handlers**

`src/agent_proxy/server/sse.py`:

```python
"""SSE handlers for AI endpoints."""
import asyncio
import json
from collections import Counter
from aiohttp import web

from agent_proxy.core.store import Store
from agent_proxy.agents.base import IntentRouter


def register_sse_routes(app: web.Application) -> None:
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
        pass  # Client disconnected, no need to write done
    except Exception as e:
        await resp.write(f'data: {json.dumps({{"type": "error", "message": str(e)}})}\n\n'.encode())

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
        # 1. Stats returned immediately (no LLM wait)
        yield await _compute_stats(store, flow_ids or None)

        # 2. LLM analysis streamed chunk-by-chunk
        analysis_agent = (agents or {}).get("analysis")
        if analysis_agent and getattr(analysis_agent, "llm", None):
            prompt = analysis_agent.build_prompt(query, list(store.flows.values()))
            async for event in _stream_llm_chunks(
                analysis_agent.llm,
                analysis_agent.get_system_prompt(),
                prompt,
            ):
                yield event

    return await _sse_response(request, event_gen())


async def ai_security(request: web.Request) -> web.StreamResponse:
    """AI security check — stats + LLM security analysis streaming."""
    store: Store = request.app["store"]
    agents: dict | None = request.app.get("agents")
    data = await request.json()
    flow_ids = data.get("flow_ids", [])

    async def event_gen():
        yield await _compute_stats(store, flow_ids or None)

        security_agent = (agents or {}).get("security")
        if security_agent and getattr(security_agent, "llm", None):
            flows = [store.flows[fid] for fid in flow_ids if fid in store.flows] if flow_ids else list(store.flows.values())
            prompt = security_agent.build_prompt(flows)
            async for event in _stream_llm_chunks(
                security_agent.llm,
                security_agent.get_system_prompt(),
                prompt,
            ):
                yield event

    return await _sse_response(request, event_gen())


async def ai_mock(request: web.Request) -> web.StreamResponse:
    """AI generate mock data — LLM streaming."""
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
            prompt = mock_agent.build_prompt(flows[-1] if flows else None)
            async for event in _stream_llm_chunks(
                mock_agent.llm,
                mock_agent.get_system_prompt(),
                prompt,
            ):
                yield event

    return await _sse_response(request, event_gen())


async def ai_query(request: web.Request) -> web.StreamResponse:
    """General AI query with IntentRouter — routes to appropriate agent."""
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
            # Non-LLM agent (e.g., DomainAgent) — return result directly
            result = await agent.execute(query)
            yield {"type": "result", "content": result.message}
            return
        # LLM-based agent — stream chunks
        system_prompt = agent.get_system_prompt()
        user_prompt = query  # Agent-specific prompt if available
        if hasattr(agent, "build_prompt"):
            user_prompt = agent.build_prompt(query, list(store.flows.values()))
        async for event in _stream_llm_chunks(agent.llm, system_prompt, user_prompt):
            yield event

    return await _sse_response(request, event_gen())
```

Update `create_app` signature:

```python
def create_app(store: Store, agents: dict | None = None) -> web.Application:
    app = web.Application()
    app["store"] = store
    app["agents"] = agents or {}
    app.router.add_get("/api/health", health_handler)
    register_routes(app)
    register_sse_routes(app)
    app.router.add_get("/ws/events", websocket_handler)
    return app
```

- [ ] **Step 5: Add asyncio import to sse.py**

```python
import asyncio
```

- [ ] **Step 6: Run tests**

Run: `.venv/bin/python -m pytest tests/test_server_sse.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/agent_proxy/server/sse.py src/agent_proxy/agents/llm.py tests/test_server_sse.py src/agent_proxy/server/app.py
git commit -m "feat: add SSE AI endpoints with streaming"
```

---

### Task 6: CLI Server Mode Integration

**Files:**
- Modify: `src/agent_proxy/cli.py`
- Test: Manual

- [ ] **Step 1: Add `--server` flag to CLI**

Add to `parse_args()`:
```python
parser.add_argument("--server", action="store_true", help="Run API server mode (no TUI)")
```

- [ ] **Step 2: Implement server_main() in cli.py**

```python
def server_main():
    """Launch API server without TUI."""
    args = parse_args()
    config = AppConfig.from_yaml()

    if args.port:
        config.proxy.listen_port = args.port
    if args.api_key:
        config.llm.api_key = args.api_key
    if args.model:
        config.llm.model = args.model

    store = Store(config)
    llm_client = LLMClient(config.llm) if config.llm.api_key else None
    memory = MemorySystem(config.memory, llm_client)

    agents = {
        "domain": DomainAgent(llm_client, store),
        "rule": RuleAgent(llm_client, store) if llm_client else None,
        "mock": MockAgent(llm_client, store) if llm_client else None,
        "security": SecurityAgent(llm_client, store) if llm_client else None,
        "analysis": AnalysisAgent(llm_client, store) if llm_client else None,
    }

    from aiohttp import web
    from agent_proxy.server.app import create_app

    engine = ProxyEngine(store, config)

    # HTTP server port: proxy port + 1000
    http_port = config.proxy.listen_port + 1000

    async def run():
        await engine.start()

        app = create_app(store, agents)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", http_port)
        await site.start()

        rich.print(f"[bold green]Agent Proxy[/bold green] starting...")
        rich.print(f"  Proxy port: {config.proxy.listen_port}")
        rich.print(f"  API server: http://127.0.0.1:{http_port}")

        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            pass
        finally:
            await engine.stop()
            await runner.cleanup()

    asyncio.run(run())
```

- [ ] **Step 3: Update main() to handle --server**

In `main()`:
```python
def main():
    args = parse_args()
    if args.server:
        server_main()
        return
    # ... rest of existing code
```

- [ ] **Step 4: Manual test**

Run: `.venv/bin/python -m agent_proxy --server`
Verify:
- Proxy starts on configured port
- API server starts on port + 1000
- `curl http://127.0.0.1:API_PORT/api/health` returns JSON
- Make HTTP requests through proxy, check `/api/flows` returns them

- [ ] **Step 5: Commit**

```bash
git add src/agent_proxy/cli.py
git commit -m "feat: add --server flag for API server mode"
```

---

## Phase 2: React + Electron Frontend

### Task 7: Frontend Scaffolding (Vite + React + TypeScript)

**Files:**
- Create: `src/web/package.json`
- Create: `src/web/vite.config.ts`
- Create: `src/web/tsconfig.json`
- Create: `src/web/index.html`
- Create: `src/web/src/main.tsx`

- [ ] **Step 1: Create package.json**

```json
{
  "name": "agent-proxy-ui",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "@tanstack/react-table": "^8.20.5"
  },
  "devDependencies": {
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "@vitejs/plugin-react": "^4.3.4",
    "typescript": "~5.6.2",
    "vite": "^6.0.1"
  }
}
```

Run: `cd src/web && npm install`

- [ ] **Step 2: Create vite.config.ts**

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:9080',
      '/ws': 'http://127.0.0.1:9080',
    },
  },
});
```

- [ ] **Step 3: Create tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"]
}
```

- [ ] **Step 4: Create index.html**

```html
<!doctype html>
<html lang="zh">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Agent Proxy</title>
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #1a1a2e; color: #e0e0e0; }
    </style>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 5: Create main.tsx**

```tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

- [ ] **Step 6: Verify dev server**

Run: `cd src/web && npm run dev`
Expected: Vite dev server starts, no errors

- [ ] **Step 7: Commit**

```bash
git add src/web/package.json src/web/vite.config.ts src/web/tsconfig.json src/web/index.html src/web/src/main.tsx
git commit -m "feat: scaffold Vite + React + TypeScript frontend"
```

---

### Task 8: Types + API Services

**Files:**
- Create: `src/web/src/types/flow.ts`
- Create: `src/web/src/types/api.ts`
- Create: `src/web/src/services/api.ts`
- Create: `src/web/src/services/ws.ts`
- Create: `src/web/src/services/sse.ts`

- [ ] **Step 1: Create TypeScript types**

`src/web/src/types/flow.ts`:

```typescript
export interface Flow {
  id: string;
  timestamp: string;
  method: string;
  url: string;
  host: string;
  path: string;
  status_code: number | null;
  request_headers: Record<string, string>;
  response_headers: Record<string, string>;
  content_type: string;
  size: number;
  duration_ms: number;
  intercepted: boolean;
  modified: boolean;
  tags: string[];
  security_issues: string[];
  request_body_base64: string | null;
  response_body_base64: string | null;
}

export interface FlowList {
  id: string;
  method: string;
  url: string;
  host: string;
  path: string;
  status_code: number | null;
  duration_ms: number;
  size: number;
}
```

`src/web/src/types/api.ts`:

```typescript
export interface HealthResponse {
  status: string;
  flows: number;
  domains: string[];
  rules: number;
}

export interface StatsEvent {
  type: 'stats';
  total: number;
  methods: Record<string, number>;
  endpoints: string[];
  avg_size: number;
}

export interface AnalysisEvent {
  type: 'analysis';
  chunk: string;
}

export interface ResultEvent {
  type: 'result';
  content: string;
}

export interface ErrorEvent {
  type: 'error';
  message: string;
}

export interface DoneEvent {
  type: 'done';
}

export type AIEvent = StatsEvent | AnalysisEvent | ResultEvent | ErrorEvent | DoneEvent;
```

- [ ] **Step 2: Create API service**

`src/web/src/services/api.ts`:

```typescript
const BASE_URL = import.meta.env.VITE_API_URL || '';

export async function fetchFlows(limit = 100, offset = 0): Promise<FlowList[]> {
  const resp = await fetch(`${BASE_URL}/api/flows?limit=${limit}&offset=${offset}`);
  if (!resp.ok) throw new Error(`Failed to fetch flows: ${resp.statusText}`);
  return resp.json();
}

export async function fetchFlow(id: string): Promise<import('../types/flow').Flow> {
  const resp = await fetch(`${BASE_URL}/api/flows/${id}`);
  if (!resp.ok) throw new Error(`Flow not found`);
  return resp.json();
}

export async function fetchDomains(): Promise<string[]> {
  const resp = await fetch(`${BASE_URL}/api/domains`);
  return resp.json();
}

export async function addDomain(domain: string): Promise<void> {
  const resp = await fetch(`${BASE_URL}/api/domains`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ domain }),
  });
  if (!resp.ok) throw new Error(`Failed to add domain`);
}

export async function deleteDomain(domain: string): Promise<void> {
  const resp = await fetch(`${BASE_URL}/api/domains/${domain}`, { method: 'DELETE' });
  if (!resp.ok) throw new Error(`Failed to delete domain`);
}

export async function postAIQuery(query: string, flowIds?: string[]): Promise<ReadableStream<Uint8Array>> {
  const resp = await fetch(`${BASE_URL}/api/ai/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, flow_ids: flowIds }),
  });
  if (!resp.ok) throw new Error(`AI request failed: ${resp.statusText}`);
  return resp.body!;
}
```

- [ ] **Step 3: Create WebSocket service**

`src/web/src/services/ws.ts`:

```typescript
export type WSEvent =
  | { type: 'flow_added'; flow: any }
  | { type: 'flow_updated'; flow: any }
  | { type: 'domain_added'; domain: string }
  | { type: 'rule_added'; rule: any }
  | { type: 'error'; message: string };

export class WSService {
  private ws: WebSocket | null = null;
  private listeners: ((event: WSEvent) => void)[] = [];
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 3;

  connect(url?: string) {
    const backendUrl = import.meta.env.VITE_API_URL || '';
    const defaultWsUrl = url || `${backendUrl || `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.hostname}:9080`}/ws/events`;
    this.ws = new WebSocket(defaultWsUrl);
    this.ws.onmessage = (e) => {
      try {
        const event: WSEvent = JSON.parse(e.data);
        this.listeners.forEach(fn => fn(event));
      } catch {}
    };
    this.ws.onclose = () => {
      this.reconnectAttempts++;
      if (this.reconnectAttempts <= this.maxReconnectAttempts) {
        setTimeout(() => this.connect(url), 5000);
      }
    };
  }

  onEvent(fn: (event: WSEvent) => void) {
    this.listeners.push(fn);
    return () => { this.listeners = this.listeners.filter(l => l !== fn); };
  }

  disconnect() {
    this.ws?.close();
    this.ws = null;
  }
}
```

- [ ] **Step 4: Create SSE service**

`src/web/src/services/sse.ts`:

```typescript
import type { AIEvent } from '../types/api';

export class SSEService {
  private abortController: AbortController | null = null;

  async query(url: string, query: string, flowIds?: string[], onEvent: (event: AIEvent) => void): Promise<void> {
    this.abortController?.abort();
    this.abortController = new AbortController();

    const resp = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, flow_ids: flowIds }),
      signal: this.abortController.signal,
    });

    if (!resp.ok) throw new Error(`AI request failed: ${resp.statusText}`);

    const reader = resp.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const event: AIEvent = JSON.parse(line.slice(6));
              onEvent(event);
            } catch {}
          }
        }
      }
    } catch (e) {
      if (e instanceof DOMException && e.name === 'AbortError') return;
      throw e;
    }
  }

  abort() {
    this.abortController?.abort();
  }
}
```

- [ ] **Step 5: Commit**

```bash
git add src/web/src/types/flow.ts src/web/src/types/api.ts src/web/src/services/api.ts src/web/src/services/ws.ts src/web/src/services/sse.ts
git commit -m "feat: add TypeScript types and API services"
```

---

### Task 9: UI Components (Flow List, Flow Detail, Domain Tree, AI Panel)

**Files:**
- Create: `src/web/src/App.tsx`
- Create: `src/web/src/components/FlowList.tsx`
- Create: `src/web/src/components/FlowDetail.tsx`
- Create: `src/web/src/components/DomainTree.tsx`
- Create: `src/web/src/components/AIPanel.tsx`
- Create: `src/web/src/components/QuickActions.tsx`
- Create: `src/web/src/components/StatusBar.tsx`

- [ ] **Step 1: Create App.tsx (main layout)**

```tsx
import { useState, useEffect, useCallback } from 'react';
import type { FlowList } from './types/flow';
import type { WSEvent } from './services/ws';
import { fetchFlows } from './services/api';
import { WSService } from './services/ws';
import FlowListTable from './components/FlowList';
import FlowDetail from './components/FlowDetail';
import DomainTree from './components/DomainTree';
import AIPanel from './components/AIPanel';
import StatusBar from './components/StatusBar';

const ws = new WSService();

export default function App() {
  const [flows, setFlows] = useState<FlowList[]>([]);
  const [selectedFlow, setSelectedFlow] = useState<string | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    // Initial load
    fetchFlows().then(setFlows).catch(console.error);

    // WebSocket for real-time updates
    ws.connect();
    ws.onEvent((event: WSEvent) => {
      setConnected(true);
      if (event.type === 'flow_added') {
        setFlows(prev => [...prev, event.flow]);
      }
    });

    return () => ws.disconnect();
  }, []);

  const handleSelect = useCallback((id: string) => setSelectedFlow(id), []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <StatusBar connected={connected} flowCount={flows.length} />
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Left: Domain tree */}
        <div style={{ width: 200, borderRight: '1px solid #333', overflowY: 'auto' }}>
          <DomainTree />
        </div>
        {/* Center: Flow list */}
        <div style={{ width: '40%', borderRight: '1px solid #333', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          <FlowListTable flows={flows} selectedId={selectedFlow} onSelect={handleSelect} />
        </div>
        {/* Right: Flow detail */}
        <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          <FlowDetail flowId={selectedFlow} />
        </div>
      </div>
      {/* Bottom: AI Panel */}
      <div style={{ height: 200, borderTop: '1px solid #333' }}>
        <AIPanel />
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create StatusBar component**

`src/web/src/components/StatusBar.tsx`:

```tsx
export default function StatusBar({ connected, flowCount }: { connected: boolean; flowCount: number }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 16, padding: '4px 12px',
      background: '#16213e', fontSize: 13,
    }}>
      <span style={{ color: connected ? '#4caf50' : '#f44336' }}>
        {connected ? '●' : '✗'} {connected ? 'Connected' : 'Disconnected'}
      </span>
      <span>Flows: {flowCount}</span>
    </div>
  );
}
```

- [ ] **Step 3: Create FlowList component**

`src/web/src/components/FlowList.tsx`:

```tsx
import { useState } from 'react';
import type { FlowList } from '../types/flow';

interface Props {
  flows: FlowList[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export default function FlowListTable({ flows, selectedId, onSelect }: Props) {
  const [filter, setFilter] = useState('');
  const filtered = flows.filter(f =>
    !filter || f.path.toLowerCase().includes(filter) || f.host.toLowerCase().includes(filter)
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <input
        placeholder="Filter by path or host..."
        value={filter}
        onChange={e => setFilter(e.target.value)}
        style={{ padding: 8, border: 'none', borderBottom: '1px solid #333', background: '#1a1a2e', color: '#e0e0e0', outline: 'none' }}
      />
      <div style={{ flex: 1, overflowY: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ textAlign: 'left', borderBottom: '1px solid #333' }}>
              <th style={{ padding: '4px 8px' }}>Method</th>
              <th style={{ padding: '4px 8px' }}>Path</th>
              <th style={{ padding: '4px 8px' }}>Status</th>
              <th style={{ padding: '4px 8px' }}>Time</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(f => (
              <tr
                key={f.id}
                onClick={() => onSelect(f.id)}
                style={{
                  background: f.id === selectedId ? '#16213e' : 'transparent',
                  cursor: 'pointer',
                  borderBottom: '1px solid #222',
                }}
              >
                <td style={{ padding: '4px 8px' }}>
                  <span style={{ color: f.method === 'GET' ? '#4caf50' : f.method === 'POST' ? '#2196f3' : '#ff9800' }}>
                    {f.method}
                  </span>
                </td>
                <td style={{ padding: '4px 8px', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {f.path}
                </td>
                <td style={{ padding: '4px 8px', color: (f.status_code ?? 0) < 400 ? '#4caf50' : '#f44336' }}>
                  {f.status_code ?? '...'}
                </td>
                <td style={{ padding: '4px 8px', color: '#888' }}>
                  {f.duration_ms > 0 ? `${f.duration_ms.toFixed(0)}ms` : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Create FlowDetail component**

`src/web/src/components/FlowDetail.tsx`:

```tsx
import { useEffect, useState } from 'react';
import { fetchFlow } from '../services/api';
import type { Flow } from '../types/flow';

export default function FlowDetail({ flowId }: { flowId: string | null }) {
  const [flow, setFlow] = useState<Flow | null>(null);

  useEffect(() => {
    if (!flowId) { setFlow(null); return; }
    fetchFlow(flowId).then(setFlow).catch(console.error);
  }, [flowId]);

  if (!flow) return <div style={{ padding: 20, color: '#666' }}>No flow selected</div>;

  const decodeBody = (b64: string | null) => {
    if (!b64) return '(empty)';
    try {
      const text = atob(b64);
      if (text.startsWith('{') || text.startsWith('[')) {
        return JSON.stringify(JSON.parse(text), null, 2);
      }
      return text;
    } catch {
      return '(binary data)';
    }
  };

  return (
    <div style={{ padding: 12, overflowY: 'auto', flex: 1, fontSize: 13 }}>
      <div style={{ marginBottom: 12 }}>
        <strong>{flow.method}</strong> {flow.url}
      </div>

      <h4 style={{ margin: '8px 0 4px' }}>Request Headers</h4>
      <pre style={{ fontSize: 12, whiteSpace: 'pre-wrap', color: '#aaa' }}>
        {Object.entries(flow.request_headers).map(([k, v]) => `${k}: ${v}`).join('\n') || '(none)'}
      </pre>

      <h4 style={{ margin: '8px 0 4px' }}>Request Body</h4>
      <pre style={{ fontSize: 12, whiteSpace: 'pre-wrap', color: '#ccc' }}>
        {decodeBody(flow.request_body_base64)}
      </pre>

      <h4 style={{ margin: '8px 0 4px' }}>Response ({flow.status_code})</h4>
      <pre style={{ fontSize: 12, color: '#888' }}>
        Duration: {flow.duration_ms.toFixed(0)}ms | Size: {flow.size}B
      </pre>

      <h4 style={{ margin: '8px 0 4px' }}>Response Headers</h4>
      <pre style={{ fontSize: 12, whiteSpace: 'pre-wrap', color: '#aaa' }}>
        {Object.entries(flow.response_headers).map(([k, v]) => `${k}: ${v}`).join('\n') || '(none)'}
      </pre>

      <h4 style={{ margin: '8px 0 4px' }}>Response Body</h4>
      <pre style={{ fontSize: 12, whiteSpace: 'pre-wrap', color: '#ccc' }}>
        {decodeBody(flow.response_body_base64)}
      </pre>
    </div>
  );
}
```

- [ ] **Step 5: Create DomainTree component**

`src/web/src/components/DomainTree.tsx`:

```tsx
import { useEffect, useState } from 'react';
import { fetchDomains, addDomain, deleteDomain } from '../services/api';

export default function DomainTree() {
  const [domains, setDomains] = useState<string[]>([]);

  useEffect(() => {
    fetchDomains().then(setDomains).catch(console.error);
  }, []);

  const handleAdd = async () => {
    const domain = prompt('Enter domain:');
    if (!domain) return;
    try {
      await addDomain(domain);
      setDomains(prev => [...prev, domain]);
    } catch (e) {
      alert('Failed to add domain');
    }
  };

  const handleDelete = async (domain: string) => {
    if (!confirm(`Remove ${domain}?`)) return;
    try {
      await deleteDomain(domain);
      setDomains(prev => prev.filter(d => d !== domain));
    } catch (e) {
      alert('Failed to remove domain');
    }
  };

  return (
    <div>
      <div style={{ padding: 8, borderBottom: '1px solid #333', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <strong style={{ fontSize: 13 }}>Domains</strong>
        <button onClick={handleAdd} style={{ background: '#2196f3', color: '#fff', border: 'none', padding: '2px 8px', borderRadius: 4, cursor: 'pointer', fontSize: 12 }}>+</button>
      </div>
      <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
        {domains.map(d => (
          <li key={d} style={{ padding: '4px 8px', fontSize: 12, display: 'flex', justifyContent: 'space-between', cursor: 'pointer' }}
              onClick={() => handleDelete(d)}>
            <span>▼ {d}</span>
            <span style={{ color: '#666', cursor: 'pointer' }} title="Remove">×</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

- [ ] **Step 6: Create AIPanel component**

`src/web/src/components/AIPanel.tsx`:

```tsx
import { useState } from 'react';
import { SSEService } from '../services/sse';
import type { AIEvent } from '../types/api';
import QuickActions from './QuickActions';

const sse = new SSEService();

export default function AIPanel() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([]);
  const [streaming, setStreaming] = useState(false);
  const [currentResponse, setCurrentResponse] = useState('');

  const handleSubmit = async (query?: string) => {
    const text = query || input.trim();
    if (!text || streaming) return;
    if (!query) setInput('');
    setMessages(prev => [...prev, { role: 'user', content: text }]);
    setStreaming(true);
    setCurrentResponse('');

    try {
      await sse.query('/api/ai/query', text, undefined, (event: AIEvent) => {
        if (event.type === 'stats') {
          setCurrentResponse(prev => prev + `📊 总请求: ${event.total} | 方法: ${JSON.stringify(event.methods)}\n\n`);
        } else if (event.type === 'analysis') {
          setCurrentResponse(prev => prev + event.content);
        } else if (event.type === 'error') {
          setCurrentResponse(prev => prev + `\n❌ ${event.message}`);
          setStreaming(false);
        } else if (event.type === 'done') {
          setStreaming(false);
          setMessages(prev => [...prev, { role: 'assistant', content: currentResponse }]);
          setCurrentResponse('');
        }
      });
    } catch (e: any) {
      setMessages(prev => [...prev, { role: 'error', content: e.message }]);
      setStreaming(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ flex: 1, overflowY: 'auto', padding: 8, fontSize: 13 }}>
        {messages.map((m, i) => (
          <div key={i} style={{ marginBottom: 8 }}>
            <strong style={{ color: m.role === 'user' ? '#87CEEB' : m.role === 'error' ? '#FF6B6B' : '#90EE90' }}>
              {m.role === 'user' ? 'You' : m.role === 'error' ? 'Error' : 'AI'}:
            </strong>
            <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit', color: '#ccc', margin: 0 }}>
              {m.content}
            </pre>
          </div>
        ))}
        {streaming && (
          <div>
            <strong style={{ color: '#90EE90' }}>AI:</strong>
            <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit', color: '#ccc', margin: 0 }}>
              {currentResponse}
              <span style={{ animation: 'blink 1s infinite' }}>▊</span>
            </pre>
          </div>
        )}
      </div>
      <QuickActions onAction={handleSubmit} disabled={streaming} />
      <form onSubmit={e => { e.preventDefault(); handleSubmit(); }} style={{ display: 'flex', borderTop: '1px solid #333' }}>
        <input value={input} onChange={e => setInput(e.target.value)} placeholder="向 AI 提问..."
               style={{ flex: 1, padding: 8, border: 'none', background: '#1a1a2e', color: '#e0e0e0', outline: 'none' }} />
        <button type="submit" disabled={streaming}
                style={{ padding: '4px 16px', background: '#2196f3', color: '#fff', border: 'none', cursor: streaming ? 'not-allowed' : 'pointer' }}>
          {streaming ? '...' : '发送'}
        </button>
      </form>
    </div>
  );
}
```

- [ ] **Step 7: Create QuickActions component**

`src/web/src/components/QuickActions.tsx`:

```tsx
const actions = [
  { label: '📊 分析流量', query: '分析流量' },
  { label: '🔒 检查安全', query: '检查安全' },
  { label: '📋 统计接口', query: '统计接口' },
];

export default function QuickActions({ onAction, disabled }: { onAction: (q: string) => void; disabled: boolean }) {
  return (
    <div style={{ display: 'flex', gap: 8, padding: '4px 8px' }}>
      {actions.map(a => (
        <button key={a.label} disabled={disabled}
                onClick={() => onAction(a.query)}
                style={{ padding: '2px 10px', fontSize: 12, background: '#2a2a4a', color: '#e0e0e0', border: '1px solid #444', borderRadius: 4, cursor: disabled ? 'not-allowed' : 'pointer' }}>
          {a.label}
        </button>
      ))}
    </div>
  );
}
```

- [ ] **Step 8: Verify build**

Run: `cd src/web && npm run build`
Expected: Successful build

- [ ] **Step 9: Commit**

```bash
git add src/web/src/App.tsx src/web/src/components/*.tsx
git commit -m "feat: add UI components for Charles-like interface"
```

---

### Task 10: Electron Shell

**Files:**
- Create: `src/web/electron/main.js`
- Create: `src/web/electron/preload.js`
- Modify: `src/web/package.json` (add electron deps + scripts)

- [ ] **Step 1: Add Electron dependencies**

```bash
cd src/web && npm install electron electron-builder
```

- [ ] **Step 2: Create Electron main process**

`src/web/electron/main.js`:

```javascript
const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let pythonProcess = null;
let mainWindow = null;
let apiPort = 9080;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  // In dev: load Vite dev server
  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:5173');
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }
}

function startPythonServer() {
  // Find the bundled Python executable
  const isPackaged = app.isPackaged;
  const pythonPath = isPackaged
    ? path.join(process.resourcesPath, 'agent-proxy/bin/agent-proxy')
    : process.platform === 'win32' ? 'python' : 'python3';

  const args = ['-m', 'agent_proxy.cli', '--server', '--port', String(apiPort)];

  // If running from source, use the virtualenv
  const envPath = path.join(__dirname, '../../../.venv/bin/python');
  const actualPython = isPackaged ? pythonPath : envPath;

  pythonProcess = spawn(actualPython, args, {
    stdio: ['pipe', 'pipe', 'pipe'],
    cwd: path.join(__dirname, '../../../'),
  });

  pythonProcess.stdout.on('data', (data) => {
    console.log(`Python: ${data}`);
    // Look for "API server" in output to know it's ready
    if (data.toString().includes('API')) {
      setTimeout(createWindow, 1000);
    }
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error(`Python Error: ${data}`);
  });

  pythonProcess.on('error', (err) => {
    console.error('Failed to start Python process:', err);
  });
}

app.whenReady().then(() => {
  startPythonServer();
});

app.on('window-all-closed', () => {
  if (pythonProcess) {
    pythonProcess.kill('SIGTERM');
  }
  app.quit();
});

app.on('before-quit', () => {
  if (pythonProcess) {
    pythonProcess.kill('SIGTERM');
  }
});
```

- [ ] **Step 3: Create preload script**

`src/web/electron/preload.js`:

```javascript
const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  platform: process.platform,
});
```

- [ ] **Step 4: Add Electron scripts to package.json**

```json
{
  "main": "electron/main.js",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "electron:dev": "cross-env NODE_ENV=development electron .",
    "electron:build": "vite build && electron-builder",
    "preview": "vite preview"
  }
}
```

Run: `npm install --save-dev cross-env @types/node`

- [ ] **Step 5: Manual test**

```bash
# Terminal 1: Start Python server
cd /Users/duliday/Documents/workspace/mantis
.venv/bin/python -m agent_proxy --server

# Terminal 2: Start frontend dev server
cd src/web
npm run electron:dev
```

Expected: Electron window opens, showing the Charles-like interface with real-time flow data.

- [ ] **Step 6: Commit**

```bash
git add src/web/electron/main.js src/web/electron/preload.js src/web/package.json
git commit -m "feat: add Electron shell with Python process management"
```

---

## Final Verification

- [ ] Run all Python tests: `.venv/bin/python -m pytest tests/ -v`
- [ ] Run frontend build: `cd src/web && npm run build`
- [ ] Manual integration test: `--server` mode + Electron dev mode
- [ ] Verify WebSocket real-time updates by making HTTP requests through proxy
- [ ] Verify AI SSE streaming works with LLM configured
