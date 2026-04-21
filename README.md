# Agent Proxy

AI-driven HTTP/HTTPS interception proxy with natural language control.

## Features

- **Domain-filtered traffic capture** -- specify domains via CLI
- **HTTPS interception** -- mitmproxy TLS interception with CA certificate management
- **Mobile proxy support** -- proxy traffic from phones on the same network
- **Natural language commands** -- create rules, generate mocks, analyze security via AI
- **Persistent memory** -- learns your patterns across sessions (Hermes-style 4-layer memory)
- **Terminal TUI** -- real-time traffic visualization in your terminal

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Basic usage
agent-proxy --domain api.example.com

# With custom LLM
agent-proxy --domain api.example.com --api-key sk-xxx --model gpt-4o

# Custom port
agent-proxy --domain api.example.com --port 9090

# Multiple domains
agent-proxy --domain api.example.com --domain cdn.example.com

# Skip system proxy
agent-proxy --domain api.example.com --no-system-proxy
```

## Natural Language Commands

| Command | Agent | Example |
|---------|-------|---------|
| Intercept/Rewrite | RuleAgent | "change /api/orders 500 to 200" |
| Mock generation | MockAgent | "generate mock for /api/users" |
| Security analysis | SecurityAgent | "check for security issues" |
| Traffic analysis | AnalysisAgent | "analyze current traffic" |

## Architecture

- **mitmproxy** as proxy engine (HTTPS MITM)
- **Textual** for terminal UI
- **OpenAI SDK** for LLM calls
- **Hermes-inspired memory** (Working, Episodic, Semantic, Procedural)

## Configuration

Config file: `~/.agent-proxy/config.yaml`

## Project Structure

```
src/agent_proxy/
├── core/          # Data models, Store, config
├── proxy/         # mitmproxy engine, addon, cert management
├── agents/        # LLM client, RuleAgent, MockAgent, SecurityAgent, AnalysisAgent
├── memory/        # 4-layer memory system
├── tui/           # Textual TUI (screens, widgets, styles)
└── utils/         # System proxy config, QR code generation
```
