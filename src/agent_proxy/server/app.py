"""aiohttp application factory and route registration."""
from aiohttp import web

from agent_proxy.core.store import Store
from agent_proxy.server.routes import register_routes


def create_app(store: Store) -> web.Application:
    """Create and configure the aiohttp application."""
    app = web.Application()
    app["store"] = store
    app.router.add_get("/api/health", health_handler)
    register_routes(app)
    return app


async def health_handler(request: web.Request) -> web.Response:
    """Return health status with flow and domain counts."""
    store: Store = request.app["store"]
    return web.json_response({
        "status": "ok",
        "flows": len(store.flows),
        "domains": store.domains,
        "rules": len(store.rules),
    })
