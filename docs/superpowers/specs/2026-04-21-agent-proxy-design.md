# Agent Proxy - Design Document

**Date:** 2026-04-21
**Status:** Draft

## Overview

Agent Proxy is an AI-driven HTTP/HTTPS interception proxy, conceptually equivalent to Charles but with natural language interaction powered by LLM agents. Users specify a target domain via CLI, view real-time traffic in a terminal TUI, and control interception/rewrite/mock/security-analysis through natural language commands.

## Architecture

```
Agent Proxy CLI (TUI)
  ├── Textual TUI (left panel: flow list | right panel: request detail | bottom bar: AI input)
  ├── Store (in-memory data hub with async event queues)
  ├── mitmproxy Addon (traffic capture, interception, rewrite, mock)
  ├── Agent Layer (RuleAgent, MockAgent, SecurityAgent, AnalysisAgent)
  ├── Memory System (4-layer: Working → Episodic → Semantic → Procedural)
  └── LLM Client (OpenAI SDK, configurable base_url/model/api_key)
```

All components run in a single process. mitmproxy is started programmatically via its `Master` API and integrated into the same asyncio event loop that Textual uses. This is a known pattern -- mitmproxy's `DumpMaster` accepts an `asyncio` event loop, and `mitmproxy.tools.main` demonstrates running it outside the standard CLI. The addon communicates with the Store via shared in-memory data structures and `asyncio.Queue`.

### Data Flow: Addon ↔ Store ↔ Agent ↔ LLM

```
Traffic → mitmproxy addon → writes FlowRecord to Store.flows
                                    ↓
                          emits to Store.flow_events (asyncio.Queue)
                                    ↓
                              TUI subscribes, updates display

TUI user input → intent routing → selects Agent
                                    ↓
                    Agent builds prompt (with memory context)
                                    ↓
                         LLM Client → OpenAI API call
                                    ↓
                    Agent parses response → ProxyRule / analysis
                                    ↓
                          result → Store.rules / Store.flows
                                    ↓
                    emits to Store.rule_events (asyncio.Queue)
                                    ↓
                    mitmproxy addon subscribes, applies rules
```

**Agent Routing**: User input is first classified by a lightweight intent router (keyword + pattern matching, no LLM call needed) to select the appropriate agent:
- Rule keywords: "intercept", "change", "modify", "block", "rewrite" → RuleAgent
- Mock keywords: "mock", "generate", "fake data" → MockAgent
- Security keywords: "security", "vulnerability", "sensitive", "leak" → SecurityAgent
- Analysis keywords: "analyze", "summary", "pattern" → AnalysisAgent

## Core Data Models

### FlowRecord

Represents one HTTP(S) request-response pair captured by the proxy.

- `id`, `timestamp`, `method`, `url`, `status_code`
- `request_headers`, `response_headers`, `request_body`, `response_body`
- `content_type`, `size`, `duration_ms`
- `intercepted`, `modified`, `tags`, `security_issues`

### ProxyRule

An executable interception/rewrite/mock rule.

- `id`, `description` (natural language)
- `condition`: url_pattern, methods, header_match
- `action`: type (intercept/modify/mock/block/pass), status_code, headers, body
- `enabled`, `source` (manual/ai)

### Memory Model

Four-layer memory inspired by Hermes Agent (Nous Research, 2026):

1. **Working Memory**: Sliding window of recent conversation context and viewed flows. Default size: 20 entries. Cleared on exit.
2. **Episodic Memory**: Persistent record of historical events (rules created, mocks generated, security findings, user commands). Stored as JSONL files, one file per date under `~/.agent-proxy/memory/episodic/`. Each entry has: `id`, `timestamp`, `event_type`, `data` (dict), `tags`.
3. **Semantic Memory**: Knowledge abstracted from episodic events via LLM analysis (e.g., "/api/users is a frequently mocked endpoint"). Stored as JSON array under `~/.agent-proxy/memory/semantic.json`. Each entry has: `fact` (str), `confidence` (float, 0-1, determined by LLM self-assessment during consolidation), `source_episodes` (list of episode IDs), `last_verified` (datetime).
4. **Procedural Memory**: User workflow habits and preferences extracted from repeated patterns (e.g., "user prefers to change 500 to 200 + empty object"). Stored as JSON array under `~/.agent-proxy/memory/procedural.json`. Each entry has: `pattern` (str), `trigger` (str), `action_template` (str), `usage_count` (int).

**Self-Improvement Loop**: Triggers every 15 interactions (configurable via `memory.consolidation_interval`). The MemorySystem collects recent episodic events, calls LLM to identify patterns, and promotes high-confidence findings (confidence >= 0.7, configurable) to semantic/procedural memory. Entries not verified for 7+ days are pruned.

## Project Structure

```
agent-proxy/
├── pyproject.toml
├── src/agent_proxy/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py                         # CLI entry point
│   ├── core/
│   │   ├── store.py                   # In-memory data hub
│   │   ├── config.py                  # Global config management
│   │   └── models.py                  # Data models
│   ├── proxy/
│   │   ├── engine.py                  # mitmproxy lifecycle management
│   │   ├── addon.py                   # mitmproxy addon implementation
│   │   └── cert.py                    # CA certificate management (pre-startup check + installation)
│   ├── agents/
│   │   ├── base.py                    # Agent abstract base class
│   │   ├── rule_agent.py              # Natural language → ProxyRule
│   │   ├── mock_agent.py              # Traffic-based mock generation
│   │   ├── security_agent.py          # Security analysis
│   │   ├── analysis_agent.py          # Traffic analysis
│   │   └── llm.py                     # LLM client (OpenAI SDK)
│   ├── memory/
│   │   ├── working.py                 # Working memory (sliding window)
│   │   ├── episodic.py                # Episodic memory (event log)
│   │   ├── semantic.py                # Semantic memory (knowledge)
│   │   ├── procedural.py              # Procedural memory (habits)
│   │   └── system.py                  # Memory system coordinator + consolidation
│   ├── tui/
│   │   ├── app.py                     # Textual App main
│   │   ├── screens/
│   │   │   ├── main.py                # Three-panel main screen
│   │   │   └── cert.py                # Certificate installation guide
│   │   ├── widgets/
│   │   │   ├── flow_list.py           # Traffic list widget
│   │   │   ├── flow_detail.py         # Request detail widget
│   │   │   ├── ai_panel.py            # AI dialog/rule input panel
│   │   │   └── status_bar.py          # Top status bar
│   │   └── styles.py                  # TUI theme styles
│   └── utils/
│       ├── proxy_config.py            # System proxy auto-config (macOS)
│       └── qr.py                      # QR code generation
├── tests/
└── README.md
```

## User Flow

### CLI Startup

```bash
agent-proxy --domain api.example.com --port 8080
```

1. Parse CLI args (`--domain` can be specified multiple times for multiple domains), load `~/.agent-proxy/config.yaml` (CLI args override config `default_domains`)
2. Check CA certificate, show installation guide if missing
3. Start mitmproxy addon (background asyncio task)
4. Auto-configure system proxy (if enabled in config)
5. Launch Textual TUI
6. Domain filter active, begin capturing traffic

### TUI Interaction

Layout:

- **Left panel** (40% width): Live traffic list (scrollable, filterable, new flows highlighted)
- **Right panel** (60% width): Selected request detail (headers, body, timing)
- **Bottom bar** (full width, 2 rows): Natural language input field for AI commands

Example commands:
- "Analyze current traffic for security issues"
- "Change all /api/orders 500 errors to 200"
- "Generate mock data for /api/users"
- "Intercept the next /api/login request"

### Mobile Proxy Mode

1. Agent Proxy listens on `0.0.0.0:8080`
2. Phone browser visits `http://<machine-ip>:8080` → `mitm.it` certificate download
3. Or TUI shows QR code linking to `mitm.it`
4. Phone installs certificate, configures WiFi proxy to `<machine-ip>:8080`
5. All phone traffic flows through agent-proxy and displays in TUI

## Error Handling

| Scenario | Behavior |
|----------|----------|
| LLM API failure | Retry 3 times → degrade to manual mode with user notification |
| Port already in use | Suggest next available port or let user specify |
| CA certificate not installed | Show certificate installation guide on startup |
| Agent generates invalid rule | Validate before applying, request regeneration (max 2 retries) |
| Store memory exceeded | Evict oldest untagged flows beyond `max_flows` limit |
| System proxy setup fails | Fall back to manual instructions |
| mitmproxy engine crash at runtime | Detect via health check task, display error in TUI status bar, attempt restart once, then prompt user |

## Agent Responsibilities

| Agent | Scope |
|-------|-------|
| **RuleAgent** | Translate natural language to ProxyRule (intercept, modify, block, rewrite) |
| **MockAgent** | Generate mock response data based on captured traffic patterns |
| **SecurityAgent** | Detect security issues (sensitive data exposure, missing security headers, XSS patterns, SQL injection indicators, unencrypted credentials) |
| **AnalysisAgent** | General traffic analysis (API patterns, performance summaries, endpoint categorization, request frequency) — does **not** check for vulnerabilities |

## Configuration

```yaml
# ~/.agent-proxy/config.yaml
proxy:
  listen_host: "0.0.0.0"
  listen_port: 8080
  auto_system_proxy: true

llm:
  api_key: "sk-..."
  base_url: "https://api.openai.com/v1"
  model: "gpt-4o"

capture:
  max_flows: 10000
  max_body_size: 1048576
  default_domains: []

memory:
  working_window_size: 20
  consolidation_interval: 15
  semantic_confidence_threshold: 0.7
  stale_memory_days: 7
```

## Lifecycle

- **Startup**: Load config → check CA cert → start mitmproxy → set system proxy → launch TUI
- **Runtime**: TUI input → Agent → Rule/Memory update → Store → mitmproxy acts on rules
- **Shutdown**: Restore system proxy → save rules/memory to disk → graceful mitmproxy close

## Technology Stack

- Python 3.12+
- mitmproxy (proxy engine)
- Textual (TUI framework)
- OpenAI SDK (LLM client)
- pyyaml (config)
- qrcode (mobile certificate QR)
- rich (terminal formatting)
