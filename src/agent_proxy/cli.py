"""CLI entry point."""
from __future__ import annotations

import argparse
import asyncio

import rich

from agent_proxy.core.config import AppConfig
from agent_proxy.core.store import Store
from agent_proxy.memory.system import MemorySystem
from agent_proxy.agents.llm import LLMClient
from agent_proxy.agents.rule_agent import RuleAgent
from agent_proxy.agents.mock_agent import MockAgent
from agent_proxy.agents.security_agent import SecurityAgent
from agent_proxy.agents.analysis_agent import AnalysisAgent
from agent_proxy.proxy.engine import ProxyEngine
from agent_proxy.proxy.cert import get_mitmproxy_cert_path, get_local_ip
from agent_proxy.tui.app import AgentProxyApp
from agent_proxy.utils.proxy_config import set_system_proxy, clear_system_proxy


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AI-driven HTTP/HTTPS interception proxy")
    parser.add_argument("--domain", action="append", help="Domain(s) to capture (can be specified multiple times)")
    parser.add_argument("--port", type=int, default=None, help="Proxy listen port (default: 8080)")
    parser.add_argument("--api-key", type=str, default=None, help="OpenAI API key")
    parser.add_argument("--model", type=str, default=None, help="LLM model name")
    parser.add_argument("--no-cert-check", action="store_true", help="Skip CA certificate check")
    parser.add_argument("--no-system-proxy", action="store_true", help="Don't auto-configure system proxy")
    return parser.parse_args()


def main():
    args = parse_args()

    config = AppConfig.from_yaml()

    domains = args.domain or config.capture.default_domains
    if args.port:
        config.proxy.listen_port = args.port
    if args.api_key:
        config.llm.api_key = args.api_key
    if args.model:
        config.llm.model = args.model
    if args.no_system_proxy:
        config.proxy.auto_system_proxy = False

    if not args.no_cert_check:
        cert_path = get_mitmproxy_cert_path()
        if not cert_path.exists():
            rich.print("[yellow]Warning: mitmproxy CA certificate not found.[/yellow]")
            rich.print("HTTPS interception will not work without it.")
            rich.print(f"Install the cert from: {cert_path}")

    store = Store(config)

    llm_client = LLMClient(config.llm) if config.llm.api_key else None
    memory = MemorySystem(config.memory, llm_client)

    agents = {
        "rule": RuleAgent(llm_client, store) if llm_client else None,
        "mock": MockAgent(llm_client, store) if llm_client else None,
        "security": SecurityAgent(llm_client, store) if llm_client else None,
        "analysis": AnalysisAgent(llm_client, store) if llm_client else None,
    }

    rich.print(f"[bold green]Agent Proxy[/bold green] starting...")
    rich.print(f"  Domains: {', '.join(domains) if domains else 'all'}")
    rich.print(f"  Port: {config.proxy.listen_port}")
    rich.print(f"  Local IP: {get_local_ip()}")

    if config.proxy.auto_system_proxy:
        set_system_proxy("127.0.0.1", config.proxy.listen_port)

    engine = ProxyEngine(store, config, domains)

    async def run():
        await engine.start()

        app = AgentProxyApp(store, agents, memory)

        try:
            await app.run_async()
        finally:
            if config.proxy.auto_system_proxy:
                clear_system_proxy()
            await engine.stop()
            memory.working.clear()

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
