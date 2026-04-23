"""mitmproxy lifecycle management via Master."""
from __future__ import annotations

import asyncio
import socket

from mitmproxy.master import Master
from mitmproxy.options import Options
from mitmproxy import addons
from mitmproxy.addons import errorcheck
from mitmproxy.addons import termlog

from agent_proxy.core.config import AppConfig
from agent_proxy.core.store import Store
from agent_proxy.proxy.addon import AgentProxyAddon


class ProxyEngine:
    """Manages mitmproxy lifecycle as an asyncio task."""

    def __init__(self, store: Store, config: AppConfig):
        self.store = store
        self.config = config
        self.addon = AgentProxyAddon(store)
        self.master: Master | None = None
        self._task: asyncio.Task | None = None
        self._healthy = True

    async def start(self) -> None:
        """Start mitmproxy as a background asyncio task."""
        opts = Options(
            listen_host=self.config.proxy.listen_host,
            listen_port=self.config.proxy.listen_port,
        )

        self.master = Master(opts)
        # Register default addons (tlsconfig for HTTPS interception, etc.)
        self.master.addons.add(*addons.default_addons())
        self.master.addons.add(termlog.TermLog())
        self.master.addons.add(errorcheck.ErrorCheck())
        # Register our custom traffic capture addon
        self.master.addons.add(self.addon)

        async def run_master():
            try:
                await self.master.run()
            except Exception:
                self._healthy = False
                raise

        self._task = asyncio.create_task(run_master())

    async def stop(self) -> None:
        """Gracefully stop mitmproxy."""
        if self.master:
            self.master.shutdown()
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=5.0)
            except (asyncio.TimeoutError, Exception):
                pass

    @property
    def is_healthy(self) -> bool:
        return self._healthy and self._task and not self._task.done()

    @staticmethod
    def find_available_port(start: int = 8080, max_try: int = 10) -> int:
        """Find an available port starting from `start`."""
        for port in range(start, start + max_try):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(("0.0.0.0", port))
                    return port
                except OSError:
                    continue
        raise OSError(f"No available port in range {start}-{start + max_try}")
