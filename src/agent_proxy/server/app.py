"""aiohttp application factory and route registration."""
import pathlib
from aiohttp import web

from agent_proxy.core.store import Store
from agent_proxy.server.routes import register_routes
from agent_proxy.server.ws import websocket_handler
from agent_proxy.server.sse import register_sse_routes
from agent_proxy.proxy.cert import get_local_ip, get_mitmproxy_cert_path


def create_app(store: Store, agents: dict | None = None, proxy_port: int = 8080) -> web.Application:
    """Create and configure the aiohttp application."""
    app = web.Application()
    app["store"] = store
    app["agents"] = agents or {}
    app["proxy_port"] = proxy_port
    app.router.add_get("/api/health", health_handler)
    app.router.add_get("/cert", cert_download_handler)
    app.router.add_get("/cert/setup", cert_setup_handler)
    register_routes(app)
    register_sse_routes(app)
    app.router.add_get("/ws/events", websocket_handler)
    return app


async def health_handler(request: web.Request) -> web.Response:
    """Return health status with flow and domain counts."""
    store: Store = request.app["store"]
    proxy_port = request.app.get("proxy_port", 8080)
    api_port = proxy_port + 1000
    host = get_local_ip()
    return web.json_response({
        "status": "ok",
        "flows": len(store.flows),
        "domains": store.domains,
        "rules": len(store.rules),
        "proxy_host": host,
        "proxy_port": proxy_port,
        "cert_url": f"http://{host}:5173/cert/setup",
    })


async def cert_download_handler(request: web.Request) -> web.FileResponse:
    """Serve mitmproxy CA certificate for download."""
    cert_path = get_mitmproxy_cert_path()
    if not cert_path.exists():
        return web.Response(text="Certificate not found. Please run 'mitmproxy' first to generate it.", status=500)
    return web.FileResponse(cert_path, headers={"Content-Disposition": 'attachment; filename="mitmproxy-ca-cert.pem"'})


async def cert_setup_handler(request: web.Request) -> web.Response:
    """Serve mobile proxy setup page with cert download link."""
    host = get_local_ip()
    port = request.app.get("proxy_port", 8080)
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {{ font-family: -apple-system, sans-serif; background: #0f0f23; color: #e0e0e0; padding: 20px; margin: 0; }}
h1 {{ font-size: 20px; color: #4caf50; }}
.step {{ background: #16213e; border-radius: 8px; padding: 16px; margin: 12px 0; }}
.step h2 {{ font-size: 16px; margin: 0 0 8px; color: #87CEEB; }}
.step p {{ margin: 0; font-size: 14px; color: #aaa; line-height: 1.6; }}
a.btn {{ display: inline-block; background: #4caf50; color: #fff; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-size: 16px; margin-top: 12px; }}
</style>
</head>
<body>
<h1>手机抓包设置</h1>
<div class="step">
<h2>1. 安装证书</h2>
<p>点击下方按钮下载 CA 证书，然后在手机上信任该证书。</p>
<a class="btn" href="/cert" download>下载证书</a>
</div>
<div class="step">
<h2>2. 配置代理</h2>
<p>打开 Wi-Fi 设置 → 代理 → 手动，填入：</p>
<p style="color: #fff; font-size: 18px; margin-top: 8px;">{host} : {port}</p>
</div>
<div class="step">
<h2>3. 开始抓包</h2>
<p>代理设置完成后，手机的所有 HTTP 流量将自动被抓取和记录。</p>
<p style="color: #aaa; margin-top: 8px;">HTTPS 需要在手机设置中信任下载的证书。</p>
</div>
</body>
</html>"""
    return web.Response(text=html, content_type="text/html; charset=utf-8")
