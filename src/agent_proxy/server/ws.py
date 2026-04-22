"""WebSocket handler for real-time flow events."""
import asyncio
import base64
import json
from aiohttp import web

from agent_proxy.core.store import Store


async def websocket_handler(request: web.Request) -> web.WebSocketResponse:
    """Handle WebSocket connections for real-time event forwarding."""
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    store: Store = request.app["store"]
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


def _rule_to_dict(rule) -> dict:
    """Serialize ProxyRule to dict. Avoids circular import from routes.py."""
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
                base64.b64encode(rule.action.body).decode()
                if rule.action.body else None
            ),
        },
    }
