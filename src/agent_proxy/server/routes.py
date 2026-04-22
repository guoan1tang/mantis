"""REST API route handlers for flows, domains, rules."""
from aiohttp import web

from agent_proxy.core.store import Store
from agent_proxy.core.models import ProxyRule, RuleCondition, RuleAction


def register_routes(app: web.Application) -> None:
    """Register REST API routes with the application."""
    app.router.add_get("/api/flows", list_flows)
    app.router.add_get("/api/flows/{flow_id}", get_flow)
    app.router.add_get("/api/flows/{flow_id}/body", get_flow_body)
    app.router.add_get("/api/domains", list_domains)
    app.router.add_post("/api/domains", add_domain)
    app.router.add_delete("/api/domains/{domain}", delete_domain)
    app.router.add_get("/api/rules", list_rules)
    app.router.add_post("/api/rules", create_rule)


async def list_flows(request: web.Request) -> web.Response:
    """List flow records with optional pagination."""
    store: Store = request.app["store"]
    limit = int(request.query.get("limit", 100))
    offset = int(request.query.get("offset", 0))
    flows = list(store.flows.values())
    page = flows[offset:offset + limit]
    return web.json_response([f.to_dict(include_body=False) for f in page])


async def get_flow(request: web.Request) -> web.Response:
    """Get a single flow record by ID."""
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
    if part not in ("request", "response"):
        return web.json_response({"error": "Invalid part, use ?part=request or ?part=response"}, status=400)
    body = flow.request_body if part == "request" else flow.response_body
    if body is None:
        return web.Response(status=204)  # No content
    try:
        text = body.decode("utf-8", errors="replace")
    except Exception:
        import base64
        return web.json_response({"base64": base64.b64encode(body).decode()})
    return web.Response(text=text, content_type=flow.content_type or "text/plain")


async def list_domains(request: web.Request) -> web.Response:
    """List all monitored domains."""
    store: Store = request.app["store"]
    return web.json_response(store.domains)


async def add_domain(request: web.Request) -> web.Response:
    """Add a domain to the monitored list."""
    store: Store = request.app["store"]
    data = await request.json()
    domain = data.get("domain", "")
    if not domain:
        return web.json_response({"error": "Domain required"}, status=400)
    if not store.add_domain(domain):
        return web.json_response({"error": "Domain already exists"}, status=409)
    return web.json_response({"domain": domain})


async def delete_domain(request: web.Request) -> web.Response:
    """Remove a domain from the monitored list."""
    store: Store = request.app["store"]
    domain = request.match_info["domain"]
    if not store.remove_domain(domain):
        return web.json_response({"error": "Domain not found"}, status=404)
    return web.json_response({"domain": domain})


async def list_rules(request: web.Request) -> web.Response:
    """List all proxy rules."""
    store: Store = request.app["store"]
    return web.json_response([_rule_to_dict(r) for r in store.rules])


async def create_rule(request: web.Request) -> web.Response:
    """Create a new proxy rule."""
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
    """Convert a ProxyRule to a JSON-serializable dict."""
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
                __import__("base64").b64encode(
                    rule.action.body if isinstance(rule.action.body, bytes)
                    else rule.action.body.encode("utf-8")
                ).decode()
                if rule.action.body else None
            ),
        },
    }
