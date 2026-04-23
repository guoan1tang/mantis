# Mantis

AI-driven HTTP/HTTPS interception proxy with natural language control. Desktop UI for capturing, analyzing, and rewriting network traffic.

## Features

- **Desktop UI** -- Charles-like GUI with real-time traffic inspection
- **Mobile capture** -- QR code setup for phone proxy, certificate download
- **HTTPS interception** -- mitmproxy TLS interception
- **Natural language control** -- rewrite rules, mocks, security analysis via AI
- **Domain management** -- add/remove monitored domains at runtime
- **Persistent memory** -- learns your patterns across sessions
- **Terminal TUI** -- optional terminal-based interface

## Requirements

- Python >= 3.12
- Node.js

## Quick Start

```bash
git clone https://github.com/guoan1tang/mantis.git
cd mantis
make install
make start
```

## Configuration

### Configure LLM Model

The AI features (traffic analysis, rule generation, security checks) require an LLM API key.

**Option 1: Config file** (recommended)

Create `~/.agent-proxy/config.yaml`:

```yaml
llm:
  api_key: "your-api-key"
  base_url: "https://api.openai.com/v1"   # OpenAI-compatible API
  model: "gpt-4o"
```

**Option 2: CLI arguments**

```bash
# OpenAI
agent-proxy --server --api-key sk-xxx --model gpt-4o

# Compatible API (e.g. Dashscope, DeepSeek, local LLM)
agent-proxy --server --api-key xxx --model qwen-plus --base-url https://dashscope.aliyuncs.com/compatible-mode/v1
```

Without an API key, the app runs normally but AI features will be unavailable.

## Commands

| Command | Description |
|---------|-------------|
| `make install` | Install all dependencies (Python + Node.js + mitmproxy cert) |
| `make start` | Launch desktop app (auto-starts proxy server) |
| `make stop` | Stop the proxy server and clear system proxy |
| `make build` | Build distributable desktop app |
| `make clean` | Remove build artifacts and caches |

## Manual Start (advanced)

```bash
# TUI mode (terminal)
agent-proxy

# Server mode (no TUI, for desktop UI)
agent-proxy --server --port 8080
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
- **aiohttp** for REST API + WebSocket + SSE
- **Electron + React** for desktop UI
- **OpenAI SDK** for LLM calls
- **Hermes-inspired memory** (Working, Episodic, Semantic, Procedural)

```

## Project Structure

```
src/
├── agent_proxy/
│   ├── core/          # Data models, Store, config
│   ├── proxy/         # mitmproxy engine, addon, cert management
│   ├── agents/        # LLM client, agents (domain, rule, mock, security, analysis)
│   ├── memory/        # 4-layer memory system
│   ├── server/        # aiohttp REST API + WebSocket + SSE
│   ├── tui/           # Textual TUI (screens, widgets, styles)
│   └── utils/         # System proxy config, QR code generation
└── web/
    ├── electron/       # Electron main/preload process
    └── src/            # React frontend
```
