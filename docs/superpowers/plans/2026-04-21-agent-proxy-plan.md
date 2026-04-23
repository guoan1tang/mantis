# Agent Proxy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an AI-driven HTTP/HTTPS interception proxy (Charles-like) with terminal TUI, natural language rule/mock/security commands, and Hermes-inspired four-layer memory system.

**Architecture:** Single-process Python application. mitmproxy runs via `DumpMaster` inside Textual's asyncio event loop. A central `Store` coordinates data between the proxy addon, TUI, agents, and memory system. Four LLM-powered agents (Rule, Mock, Security, Analysis) translate natural language into proxy actions.

**Tech Stack:** Python 3.12+, mitmproxy, Textual, OpenAI SDK, pyyaml, qrcode, rich, pytest

---

## File Structure Map

| File | Action | Responsibility |
|------|--------|----------------|
| `pyproject.toml` | Create | Project config, dependencies, CLI entry point |
| `src/agent_proxy/__init__.py` | Create | Package init |
| `src/agent_proxy/__main__.py` | Create | `python -m agent_proxy` entry |
| `src/agent_proxy/core/models.py` | Create | FlowRecord, ProxyRule dataclasses |
| `src/agent_proxy/core/store.py` | Create | In-memory data hub with async queues |
| `src/agent_proxy/core/config.py` | Create | Config loading from YAML + CLI override |
| `src/agent_proxy/proxy/addon.py` | Create | mitmproxy addon for capture/intercept/rewrite |
| `src/agent_proxy/proxy/engine.py` | Create | mitmproxy lifecycle (start/stop via DumpMaster) |
| `src/agent_proxy/proxy/cert.py` | Create | CA cert check, install, QR code generation |
| `src/agent_proxy/agents/base.py` | Create | Agent ABC + intent router |
| `src/agent_proxy/agents/llm.py` | Create | OpenAI SDK wrapper with async support + retry |
| `src/agent_proxy/agents/rule_agent.py` | Create | Natural language → ProxyRule |
| `src/agent_proxy/agents/mock_agent.py` | Create | Traffic pattern → mock data |
| `src/agent_proxy/agents/security_agent.py` | Create | Security issue detection |
| `src/agent_proxy/agents/analysis_agent.py` | Create | Traffic analysis/summary |
| `src/agent_proxy/memory/working.py` | Create | Working memory (sliding window) |
| `src/agent_proxy/memory/episodic.py` | Create | Episodic memory (JSONL by date) |
| `src/agent_proxy/memory/semantic.py` | Create | Semantic memory (knowledge) |
| `src/agent_proxy/memory/procedural.py` | Create | Procedural memory (habits) |
| `src/agent_proxy/memory/system.py` | Create | Memory coordinator + consolidation loop |
| `src/agent_proxy/tui/app.py` | Create | Textual App bootstrap |
| `src/agent_proxy/tui/screens/main.py` | Create | Three-panel main screen |
| `src/agent_proxy/tui/screens/cert.py` | Create | Certificate installation guide screen |
| `src/agent_proxy/tui/widgets/flow_list.py` | Create | Flow list widget |
| `src/agent_proxy/tui/widgets/flow_detail.py` | Create | Request detail widget |
| `src/agent_proxy/tui/widgets/ai_panel.py` | Create | AI input/output panel |
| `src/agent_proxy/tui/widgets/status_bar.py` | Create | Top status bar |
| `src/agent_proxy/tui/styles.py` | Create | TUI theme constants |
| `src/agent_proxy/utils/proxy_config.py` | Create | macOS system proxy auto-config |
| `src/agent_proxy/utils/qr.py` | Create | QR code generation helper |
| `src/agent_proxy/cli.py` | Create | CLI argument parsing + orchestration |
| `tests/test_models.py` | Create | Model tests |
| `tests/test_store.py` | Create | Store tests |
| `tests/test_config.py` | Create | Config tests |
| `tests/test_addon.py` | Create | Addon tests |
| `tests/test_agents.py` | Create | Agent tests (mocked LLM) |
| `tests/test_memory.py` | Create | Memory system tests |

---

### Task 1: Project Setup & Data Models

**Files:**
- Create: `pyproject.toml`
- Create: `src/agent_proxy/__init__.py`
- Create: `src/agent_proxy/__main__.py`
- Create: `src/agent_proxy/core/models.py`
- Test: `tests/test_models.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "agent-proxy"
version = "0.1.0"
description = "AI-driven HTTP/HTTPS interception proxy with natural language control"
requires-python = ">=3.12"
dependencies = [
    "mitmproxy>=10.0",
    "textual>=0.50",
    "openai>=1.0",
    "pyyaml>=6.0",
    "qrcode[pil]>=7.4",
    "rich>=13.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "ruff>=0.3",
]

[project.scripts]
agent-proxy = "agent_proxy.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.ruff]
target-version = "py312"
```

- [ ] **Step 2: Create `src/agent_proxy/__init__.py`** (empty file)

- [ ] **Step 3: Create `src/agent_proxy/__main__.py`**

```python
"""Allow running as: python -m agent_proxy"""
from agent_proxy.cli import main

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Create `src/agent_proxy/core/models.py`**

```python
"""Core data models for flow records and proxy rules."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal


@dataclass
class FlowRecord:
    """Represents one HTTP(S) request-response pair."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    method: str = ""
    url: str = ""
    status_code: int | None = None
    request_headers: dict[str, str] = field(default_factory=dict)
    response_headers: dict[str, str] = field(default_factory=dict)
    request_body: bytes | None = None
    response_body: bytes | None = None
    content_type: str = ""
    size: int = 0
    duration_ms: float = 0.0
    intercepted: bool = False
    modified: bool = False
    tags: list[str] = field(default_factory=list)
    security_issues: list[str] = field(default_factory=list)

    @property
    def host(self) -> str:
        """Extract host from URL."""
        from urllib.parse import urlparse
        return urlparse(self.url).hostname or ""

    @property
    def path(self) -> str:
        """Extract path from URL."""
        from urllib.parse import urlparse
        return urlparse(self.url).path or "/"


@dataclass
class RuleCondition:
    """Matching conditions for a proxy rule."""
    url_pattern: str | None = None      # glob/regex pattern
    methods: list[str] | None = None     # e.g. ["GET", "POST"]
    header_match: dict[str, str] | None = None

    def matches(self, flow: FlowRecord) -> bool:
        """Check if a flow matches this condition."""
        import fnmatch

        if self.url_pattern and not fnmatch.fnmatch(flow.url, f"*{self.url_pattern}*"):
            return False
        if self.methods and flow.method not in self.methods:
            return False
        if self.header_match:
            for key, value in self.header_match.items():
                if flow.request_headers.get(key) != value:
                    return False
        return True


@dataclass
class RuleAction:
    """Action to take when a rule matches."""
    type: Literal["intercept", "modify", "mock", "block", "pass"] = "pass"
    status_code: int | None = None
    headers: dict[str, str] | None = None
    body: bytes | None = None


@dataclass
class ProxyRule:
    """An executable interception/rewrite/mock rule."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    description: str = ""
    condition: RuleCondition = field(default_factory=RuleCondition)
    action: RuleAction = field(default_factory=RuleAction)
    enabled: bool = True
    source: Literal["manual", "ai"] = "manual"
```

- [ ] **Step 5: Create `tests/test_models.py`**

```python
"""Tests for core data models."""
from agent_proxy.core.models import FlowRecord, ProxyRule, RuleAction, RuleCondition


def test_flow_record_defaults():
    flow = FlowRecord()
    assert flow.id
    assert flow.method == ""
    assert flow.status_code is None
    assert flow.intercepted is False


def test_flow_record_url_parsing():
    flow = FlowRecord(url="https://api.example.com/v1/users?limit=10")
    assert flow.host == "api.example.com"
    assert flow.path == "/v1/users"


def test_rule_condition_matches_url():
    cond = RuleCondition(url_pattern="/api/users")
    flow = FlowRecord(url="https://api.example.com/api/users/123", method="GET")
    assert cond.matches(flow) is True


def test_rule_condition_no_match_method():
    cond = RuleCondition(url_pattern="/api", methods=["POST"])
    flow = FlowRecord(url="https://api.example.com/api/data", method="GET")
    assert cond.matches(flow) is False


def test_proxy_rule_defaults():
    rule = ProxyRule()
    assert rule.enabled is True
    assert rule.source == "manual"
```

- [ ] **Step 6: Run tests**

```bash
pip install -e ".[dev]"
pytest tests/test_models.py -v
```
Expected: All 5 tests PASS

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml src/agent_proxy/__init__.py src/agent_proxy/__main__.py src/agent_proxy/core/models.py tests/test_models.py
git commit -m "feat: project setup with core data models (FlowRecord, ProxyRule)"
```

---

### Task 2: Store (In-Memory Data Hub)

**Files:**
- Create: `src/agent_proxy/core/store.py`
- Test: `tests/test_store.py`

- [ ] **Step 1: Create `src/agent_proxy/core/store.py`**

```python
"""In-memory data hub coordinating all components."""
from __future__ import annotations

import asyncio
from collections import OrderedDict
from datetime import datetime, timezone

from agent_proxy.core.config import AppConfig
from agent_proxy.core.models import FlowRecord, ProxyRule


class Store:
    """Central data hub with async event queues for component communication."""

    def __init__(self, config: AppConfig | None = None):
        self.config = config or AppConfig()
        self._flows: OrderedDict[str, FlowRecord] = OrderedDict()
        self._rules: list[ProxyRule] = []
        self.flow_events: asyncio.Queue[FlowRecord] = asyncio.Queue()
        self.rule_events: asyncio.Queue[ProxyRule] = asyncio.Queue()

    @property
    def flows(self) -> dict[str, FlowRecord]:
        return dict(self._flows)

    @property
    def rules(self) -> list[ProxyRule]:
        return list(self._rules)

    def add_flow(self, flow: FlowRecord) -> None:
        """Add a captured flow record."""
        max_flows = self.config.capture.max_flows
        while len(self._flows) >= max_flows:
            self._flows.popitem(last=False)
        self._flows[flow.id] = flow
        self.flow_events.put_nowait(flow)

    def update_flow(self, flow_id: str, **kwargs) -> FlowRecord | None:
        """Update an existing flow record."""
        flow = self._flows.get(flow_id)
        if not flow:
            return None
        for key, value in kwargs.items():
            setattr(flow, key, value)
        return flow

    def add_rule(self, rule: ProxyRule) -> None:
        """Add a proxy rule."""
        self._rules.append(rule)
        self.rule_events.put_nowait(rule)

    def remove_rule(self, rule_id: str) -> bool:
        """Remove a rule by ID."""
        before = len(self._rules)
        self._rules = [r for r in self._rules if r.id != rule_id]
        return len(self._rules) < before

    def get_matching_rules(self, flow: FlowRecord) -> list[ProxyRule]:
        """Find all enabled rules matching a flow."""
        return [r for r in self._rules if r.enabled and r.condition.matches(flow)]

    def clear(self) -> None:
        """Clear all data."""
        self._flows.clear()
        self._rules.clear()
        while not self.flow_events.empty():
            self.flow_events.get_nowait()
        while not self.rule_events.empty():
            self.rule_events.get_nowait()
```

- [ ] **Step 2: Create `src/agent_proxy/core/config.py`** (Store needs it)

```python
"""Configuration management."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CaptureConfig:
    max_flows: int = 10000
    max_body_size: int = 1048576
    default_domains: list[str] = field(default_factory=list)


@dataclass
class ProxyConfig:
    listen_host: str = "0.0.0.0"
    listen_port: int = 8080
    auto_system_proxy: bool = True


@dataclass
class LLMConfig:
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o"


@dataclass
class MemoryConfig:
    working_window_size: int = 20
    consolidation_interval: int = 15
    semantic_confidence_threshold: float = 0.7
    stale_memory_days: int = 7


@dataclass
class AppConfig:
    proxy: ProxyConfig = field(default_factory=ProxyConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    capture: CaptureConfig = field(default_factory=CaptureConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)

    @classmethod
    def from_yaml(cls, path: str | Path | None = None) -> AppConfig:
        """Load config from YAML file."""
        import yaml

        config_path = Path(path) if path else _default_config_path()
        if config_path.exists():
            with open(config_path) as f:
                data = yaml.safe_load(f)
            return _dict_to_config(data)
        return cls()

    def save(self, path: str | Path | None = None) -> None:
        """Save config to YAML."""
        import yaml

        config_path = Path(path) if path else _default_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            yaml.dump(_config_to_dict(self), f, default_flow_style=False)


def _default_config_path() -> Path:
    return Path.home() / ".agent-proxy" / "config.yaml"


def _dict_to_config(data: dict) -> AppConfig:
    config = AppConfig()
    if "proxy" in data:
        config.proxy = ProxyConfig(**{k: v for k, v in data["proxy"].items() if hasattr(config.proxy, k)})
    if "llm" in data:
        config.llm = LLMConfig(**{k: v for k, v in data["llm"].items() if hasattr(config.llm, k)})
    if "capture" in data:
        config.capture = CaptureConfig(**{k: v for k, v in data["capture"].items() if hasattr(config.capture, k)})
    if "memory" in data:
        config.memory = MemoryConfig(**{k: v for k, v in data["memory"].items() if hasattr(config.memory, k)})
    return config


def _config_to_dict(config: AppConfig) -> dict:
    return {
        "proxy": {
            "listen_host": config.proxy.listen_host,
            "listen_port": config.proxy.listen_port,
            "auto_system_proxy": config.proxy.auto_system_proxy,
        },
        "llm": {
            "api_key": config.llm.api_key,
            "base_url": config.llm.base_url,
            "model": config.llm.model,
        },
        "capture": {
            "max_flows": config.capture.max_flows,
            "max_body_size": config.capture.max_body_size,
            "default_domains": config.capture.default_domains,
        },
        "memory": {
            "working_window_size": config.memory.working_window_size,
            "consolidation_interval": config.memory.consolidation_interval,
            "semantic_confidence_threshold": config.memory.semantic_confidence_threshold,
            "stale_memory_days": config.memory.stale_memory_days,
        },
    }
```

- [ ] **Step 3: Create `tests/test_store.py`**

```python
"""Tests for Store."""
import pytest
from agent_proxy.core.models import FlowRecord, ProxyRule, RuleAction, RuleCondition
from agent_proxy.core.store import Store


@pytest.fixture
def store():
    return Store()


def test_add_flow(store):
    flow = FlowRecord(method="GET", url="https://api.example.com/users")
    store.add_flow(flow)
    assert flow.id in store.flows


def test_flow_eviction_on_max(store):
    store.config.capture.max_flows = 3
    for i in range(5):
        store.add_flow(FlowRecord(url=f"https://api.example.com/{i}"))
    assert len(store.flows) == 3
    # Oldest flows evicted
    assert "https://api.example.com/0" not in store.flows.values()


def test_add_and_get_rules(store):
    rule = ProxyRule(description="test rule")
    store.add_rule(rule)
    assert rule in store.rules


def test_get_matching_rules(store):
    rule = ProxyRule(
        condition=RuleCondition(url_pattern="/api/users"),
        action=RuleAction(type="modify"),
    )
    store.add_rule(rule)
    flow = FlowRecord(url="https://api.example.com/api/users/1", method="GET")
    matches = store.get_matching_rules(flow)
    assert len(matches) == 1
    assert matches[0].id == rule.id


def test_remove_rule(store):
    rule = ProxyRule()
    store.add_rule(rule)
    store.remove_rule(rule.id)
    assert rule.id not in [r.id for r in store.rules]


def test_disabled_rules_ignored(store):
    rule = ProxyRule(
        enabled=False,
        condition=RuleCondition(url_pattern="/api"),
    )
    store.add_rule(rule)
    flow = FlowRecord(url="https://api.example.com/api/test")
    matches = store.get_matching_rules(flow)
    assert len(matches) == 0
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_store.py tests/test_models.py -v
```
Expected: All tests PASS

- [ ] **Step 5: Create `tests/test_config.py`**

```python
"""Tests for config management."""
import tempfile
from pathlib import Path

from agent_proxy.core.config import AppConfig


def test_default_config():
    config = AppConfig()
    assert config.proxy.listen_port == 8080
    assert config.capture.max_flows == 10000


def test_config_round_trip():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "config.yaml"
        config = AppConfig()
        config.proxy.listen_port = 9090
        config.save(path)

        loaded = AppConfig.from_yaml(path)
        assert loaded.proxy.listen_port == 9090


def test_config_from_yaml():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "config.yaml"
        path.write_text("proxy:\n  listen_port: 3000\n")
        config = AppConfig.from_yaml(path)
        assert config.proxy.listen_port == 3000
```

- [ ] **Step 6: Run all tests**

```bash
pytest tests/ -v
```
Expected: All tests PASS

- [ ] **Step 7: Commit**

```bash
git add src/agent_proxy/core/store.py src/agent_proxy/core/config.py tests/test_store.py
git commit -m "feat: Store data hub with async queues and config management"
```

---

### Task 3: mitmproxy Addon

**Files:**
- Create: `src/agent_proxy/proxy/addon.py`
- Test: `tests/test_addon.py`

- [ ] **Step 1: Create `src/agent_proxy/proxy/addon.py`**

```python
"""mitmproxy addon for traffic capture, interception, and rewrite."""
from __future__ import annotations

import time
from urllib.parse import urlparse

import mitmproxy.http
from mitmproxy.addonmanager import Loader

from agent_proxy.core.models import FlowRecord, RuleAction
from agent_proxy.core.store import Store


class AgentProxyAddon:
    """mitmproxy addon that captures and intercepts traffic."""

    def __init__(self, store: Store, domains: list[str] | None = None):
        self.store = store
        self.domains = domains or []
        self._start_times: dict[str, float] = {}

    def add_arguments(self, loader: Loader) -> None:
        """No custom arguments needed."""
        pass

    def _should_capture(self, flow: mitmproxy.http.HTTPFlow) -> bool:
        """Check if flow matches configured domains."""
        if not self.domains:
            return True
        host = flow.request.host
        return any(self._domain_match(host, d) for d in self.domains)

    @staticmethod
    def _domain_match(host: str, pattern: str) -> bool:
        """Match host against domain pattern (supports wildcard *)."""
        import fnmatch
        return fnmatch.fnmatch(host, pattern)

    def request(self, flow: mitmproxy.http.HTTPFlow) -> None:
        """Handle incoming request."""
        if not self._should_capture(flow):
            return

        # Track timing
        self._start_times[flow.id] = time.time()

        # Check for intercept/block/mock rules
        temp_flow = self._to_flow_record(flow, include_response=False)
        matching_rules = self.store.get_matching_rules(temp_flow)

        for rule in matching_rules:
            action = rule.action
            if action.type == "block":
                flow.response = mitmproxy.http.HTTPResponse.make(
                    status_code=action.status_code or 403,
                    content=b"Blocked by Agent Proxy",
                )
                temp_flow.intercepted = True
                temp_flow.status_code = action.status_code or 403
                self.store.add_flow(temp_flow)
                return

            if action.type == "mock":
                flow.response = mitmproxy.http.HTTPResponse.make(
                    status_code=action.status_code or 200,
                    content=action.body or b"",
                    headers=action.headers,
                )
                temp_flow.intercepted = True
                temp_flow.modified = True
                temp_flow.status_code = action.status_code or 200
                temp_flow.response_body = action.body or b""
                self.store.add_flow(temp_flow)
                return

            if action.type == "modify":
                # Headers modification
                if action.headers:
                    for key, value in action.headers.items():
                        flow.request.headers[key] = value

    def response(self, flow: mitmproxy.http.HTTPFlow) -> None:
        """Handle response."""
        if not self._should_capture(flow):
            return

        record = self._to_flow_record(flow)

        # Calculate duration
        start = self._start_times.pop(flow.id, None)
        if start:
            record.duration_ms = (time.time() - start) * 1000

        # Apply modify rules to response
        matching_rules = self.store.get_matching_rules(record)
        for rule in matching_rules:
            if rule.action.type == "modify":
                action = rule.action
                if action.body is not None:
                    flow.response.content = action.body
                    record.response_body = action.body
                    record.modified = True
                if action.status_code:
                    flow.response.status_code = action.status_code
                    record.status_code = action.status_code
                    record.modified = True
                if action.headers:
                    for key, value in action.headers.items():
                        flow.response.headers[key] = value

        self.store.add_flow(record)

    def error(self, flow: mitmproxy.http.HTTPFlow) -> None:
        """Handle connection error."""
        if not self._should_capture(flow):
            return
        record = self._to_flow_record(flow)
        record.status_code = 0
        self.store.add_flow(record)

    def _to_flow_record(self, flow: mitmproxy.http.HTTPFlow, include_response: bool = True) -> FlowRecord:
        """Convert mitmproxy flow to FlowRecord."""
        url = flow.request.pretty_url
        max_body = self.store.config.capture.max_body_size

        record = FlowRecord(
            method=flow.request.method,
            url=url,
            request_headers=dict(flow.request.headers),
            request_body=flow.request.content[:max_body] if flow.request.content else None,
            content_type=flow.request.headers.get("Content-Type", ""),
        )

        if include_response and flow.response:
            record.status_code = flow.response.status_code
            record.response_headers = dict(flow.response.headers)
            record.response_body = flow.response.content[:max_body] if flow.response.content else None
            record.size = len(flow.response.content) if flow.response.content else 0

        return record
```

- [ ] **Step 2: Create `tests/test_addon.py`**

```python
"""Tests for mitmproxy addon."""
import pytest
from unittest.mock import MagicMock

from agent_proxy.core.models import FlowRecord, ProxyRule, RuleAction, RuleCondition
from agent_proxy.core.store import Store
from agent_proxy.proxy.addon import AgentProxyAddon


@pytest.fixture
def store():
    return Store()


@pytest.fixture
def addon(store):
    return AgentProxyAddon(store)


def test_domain_filter_no_filter(addon, store):
    """When no domains set, capture everything."""
    assert addon._should_capture(MagicMock(host="anything.com")) is True


def test_domain_filter_exact_match(addon, store):
    addon.domains = ["api.example.com"]
    flow = MagicMock(host="api.example.com")
    assert addon._should_capture(flow) is True


def test_domain_filter_no_match(addon, store):
    addon.domains = ["api.example.com"]
    flow = MagicMock(host="other.com")
    assert addon._should_capture(flow) is False


def test_domain_filter_wildcard(addon, store):
    addon.domains = ["*.example.com"]
    flow = MagicMock(host="api.example.com")
    assert addon._should_capture(flow) is True


def test_mock_rule_blocks_request(addon, store):
    rule = ProxyRule(
        condition=RuleCondition(url_pattern="/blocked"),
        action=RuleAction(type="block", status_code=403),
    )
    store.add_rule(rule)

    flow = MagicMock()
    flow.id = "test1"
    flow.request = MagicMock()
    flow.request.method = "GET"
    flow.request.pretty_url = "https://api.example.com/blocked"
    flow.request.headers = {}
    flow.request.content = None
    flow.response = None

    addon.request(flow)
    # Verify response was set by the block rule
    assert flow.response is not None
    assert flow.response.status_code == 403
```

- [ ] **Step 3: Run tests**

```bash
pytest tests/test_addon.py -v
```
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add src/agent_proxy/proxy/addon.py tests/test_addon.py
git commit -m "feat: mitmproxy addon for traffic capture, interception, and rewrite"
```

---

### Task 4: Proxy Engine & Certificate Management

**Files:**
- Create: `src/agent_proxy/proxy/engine.py`
- Create: `src/agent_proxy/proxy/cert.py`

- [ ] **Step 1: Create `src/agent_proxy/proxy/engine.py`**

```python
"""mitmproxy lifecycle management via DumpMaster."""
from __future__ import annotations

import asyncio
import socket

from mitmproxy.master import DumpMaster
from mitmproxy.options import Options

from agent_proxy.core.config import AppConfig
from agent_proxy.core.store import Store
from agent_proxy.proxy.addon import AgentProxyAddon


class ProxyEngine:
    """Manages mitmproxy lifecycle as an asyncio task."""

    def __init__(self, store: Store, config: AppConfig, domains: list[str] | None = None):
        self.store = store
        self.config = config
        self.domains = domains or config.capture.default_domains
        self.addon = AgentProxyAddon(store, self.domains)
        self.master: DumpMaster | None = None
        self._task: asyncio.Task | None = None
        self._healthy = True

    async def start(self) -> None:
        """Start mitmproxy as a background asyncio task."""
        opts = Options(
            listen_host=self.config.proxy.listen_host,
            listen_port=self.config.proxy.listen_port,
        )

        self.master = DumpMaster(opts)
        self.master.addons.add(self.addon)

        async def run_master():
            try:
                await self.master.run()
            except Exception as e:
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
```

- [ ] **Step 2: Create `src/agent_proxy/proxy/cert.py`**

```python
"""CA certificate management."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def get_mitmproxy_cert_path() -> Path:
    """Get the default mitmproxy CA certificate path."""
    return Path.home() / ".mitmproxy" / "mitmproxy-ca-cert.pem"


def is_cert_installed_macos() -> bool:
    """Check if mitmproxy CA cert is trusted on macOS."""
    try:
        result = subprocess.run(
            ["security", "find-certificate", "-c", "mitmproxy", "-p"],
            capture_output=True, text=True, timeout=5,
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def install_cert_macos(cert_path: Path) -> bool:
    """Install mitmproxy CA cert into macOS keychain."""
    try:
        result = subprocess.run(
            ["sudo", "security", "add-trusted-cert", "-d", "-r", "trustRoot",
             "-k", "/Library/Keychains/System.keychain", str(cert_path)],
            capture_output=True, text=True, timeout=30,
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def generate_cert_qr_code(host: str, port: int) -> str:
    """Generate QR code text for mitm.it certificate download."""
    return f"http://{host}:{port}"


def get_local_ip() -> str:
    """Get the machine's local IP address."""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()
```

- [ ] **Step 3: Commit**

```bash
git add src/agent_proxy/proxy/engine.py src/agent_proxy/proxy/cert.py
git commit -m "feat: proxy engine lifecycle and certificate management"
```

---

### Task 5: LLM Client & Agent Base

**Files:**
- Create: `src/agent_proxy/agents/llm.py`
- Create: `src/agent_proxy/agents/base.py`
- Test: `tests/test_agents.py` (partial - base + llm tests)

- [ ] **Step 1: Create `src/agent_proxy/agents/llm.py`**

```python
"""LLM client using OpenAI SDK with async support and retry."""
from __future__ import annotations

import json

from openai import AsyncOpenAI

from agent_proxy.core.config import LLMConfig


class LLMClient:
    """Async OpenAI SDK wrapper with retry logic."""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url if config.base_url else None,
        )

    async def call(
        self,
        system_prompt: str,
        user_prompt: str,
        response_format: type | None = None,
        max_retries: int = 3,
    ) -> str:
        """Call LLM with retry. Returns raw response text."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        kwargs = {
            "model": self.config.model,
            "messages": messages,
            "temperature": 0.1,
        }

        for attempt in range(max_retries):
            try:
                response = await self.client.chat.completions.create(**kwargs)
                return response.choices[0].message.content or ""
            except Exception:
                if attempt == max_retries - 1:
                    raise
                import asyncio
                await asyncio.sleep(2 ** attempt)

    async def call_json(
        self,
        system_prompt: str,
        user_prompt: str,
        max_retries: int = 3,
    ) -> dict | list:
        """Call LLM and parse response as JSON."""
        text = await self.call(system_prompt, user_prompt, max_retries=max_retries)
        # Extract JSON from markdown code blocks if present
        if "```" in text:
            start = text.find("```")
            line_end = text.index("\n", start) if "\n" in text[start:] else start + 3
            block_start = line_end + 1
            end = text.find("```", block_start)
            if end > 0:
                text = text[block_start:end].strip()
        # Fallback: find first { or [ for plain JSON responses
        if text.strip().startswith("{") or text.strip().startswith("["):
            return json.loads(text.strip())
        for ch in ["{", "["]:
            idx = text.find(ch)
            if idx >= 0:
                try:
                    return json.loads(text[idx:])
                except json.JSONDecodeError:
                    continue
        return json.loads(text.strip())
```

- [ ] **Step 2: Create `src/agent_proxy/agents/base.py`**

```python
"""Agent base class and intent router."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from agent_proxy.core.store import Store
from agent_proxy.agents.llm import LLMClient


@dataclass
class AgentResult:
    """Result from an agent execution."""
    success: bool
    message: str
    data: dict | list | None = None


class BaseAgent(ABC):
    """Base class for all agents."""

    def __init__(self, llm_client: LLMClient, store: Store):
        self.llm = llm_client
        self.store = store

    @abstractmethod
    async def execute(self, user_input: str) -> AgentResult:
        """Execute the agent with user input."""
        ...

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        ...


class IntentRouter:
    """Routes user input to the correct agent based on keywords."""

    AGENT_KEYWORDS = {
        "rule": ["intercept", "change", "modify", "block", "rewrite", "redirect"],
        "mock": ["mock", "generate", "fake data", "fake"],
        "security": ["security", "vulnerability", "sensitive", "leak", "xss", "injection"],
        "analysis": ["analyze", "summary", "pattern", "report", "stats"],
    }

    @classmethod
    def route(cls, user_input: str) -> str:
        """Return the agent name to handle this input."""
        lower = user_input.lower()
        for agent, keywords in cls.AGENT_KEYWORDS.items():
            if any(kw in lower for kw in keywords):
                return agent
        return "analysis"  # default fallback
```

- [ ] **Step 3: Create `tests/test_agents.py`** (base + llm tests)

```python
"""Tests for agent base classes and intent routing."""
from agent_proxy.agents.base import IntentRouter


def test_route_rule_agent():
    assert IntentRouter.route("change /api/users response") == "rule"


def test_route_mock_agent():
    assert IntentRouter.route("generate mock data for /api/login") == "mock"


def test_route_security_agent():
    assert IntentRouter.route("check for security vulnerabilities") == "security"


def test_route_analysis_agent():
    assert IntentRouter.route("analyze current traffic") == "analysis"


def test_route_default_fallback():
    assert IntentRouter.route("tell me about requests") == "analysis"
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_agents.py -v
```
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/agent_proxy/agents/llm.py src/agent_proxy/agents/base.py tests/test_agents.py
git commit -m "feat: LLM client with retry and agent base with intent router"
```

---

### Task 6: Agent Implementations (Rule, Mock, Security, Analysis)

**Files:**
- Create: `src/agent_proxy/agents/rule_agent.py`
- Create: `src/agent_proxy/agents/mock_agent.py`
- Create: `src/agent_proxy/agents/security_agent.py`
- Create: `src/agent_proxy/agents/analysis_agent.py`
- Test: `tests/test_agents.py` (add agent tests)

- [ ] **Step 1: Create `src/agent_proxy/agents/rule_agent.py`**

```python
"""RuleAgent: translates natural language to ProxyRule."""
from __future__ import annotations

import json

from agent_proxy.agents.base import BaseAgent, AgentResult
from agent_proxy.core.models import ProxyRule, RuleCondition, RuleAction


class RuleAgent(BaseAgent):
    """Converts natural language commands into executable proxy rules."""

    def get_system_prompt(self) -> str:
        return """You are a proxy rule generator. Convert user instructions into a JSON object representing a proxy rule.

The JSON must have this exact structure:
{
  "description": "natural language description",
  "condition": {
    "url_pattern": "URL pattern to match (use path fragments, e.g. '/api/users')",
    "methods": ["GET", "POST"] or null,
    "header_match": {} or null
  },
  "action": {
    "type": "one of: intercept, modify, mock, block, pass",
    "status_code": number or null,
    "headers": {} or null,
    "body": "response body string or null"
  }
}

Examples:
- "Block all requests to /api/admin" → {"type": "block", "url_pattern": "/api/admin"}
- "Change /api/orders 500 errors to 200 with empty JSON" → {"type": "modify", "url_pattern": "/api/orders", "status_code": 200, "body": "{}"}
- "Mock /api/users to return a list with one user" → {"type": "mock", "url_pattern": "/api/users", "status_code": 200, "body": "[{\\"id\\": 1, \\"name\\": \\"test_user\\"}]"}"""

    async def execute(self, user_input: str) -> AgentResult:
        try:
            rule_json = await self.llm.call_json(
                self.get_system_prompt(),
                user_input,
            )

            condition = RuleCondition(
                url_pattern=rule_json.get("condition", {}).get("url_pattern"),
                methods=rule_json.get("condition", {}).get("methods"),
                header_match=rule_json.get("condition", {}).get("header_match"),
            )
            action = RuleAction(
                type=rule_json.get("action", {}).get("type", "pass"),
                status_code=rule_json.get("action", {}).get("status_code"),
                headers=rule_json.get("action", {}).get("headers"),
                body=rule_json.get("action", {}).get("body", "").encode() if rule_json.get("action", {}).get("body") else None,
            )
            rule = ProxyRule(
                description=rule_json.get("description", user_input),
                condition=condition,
                action=action,
                source="ai",
            )
            self.store.add_rule(rule)
            return AgentResult(success=True, message=f"Rule created: {rule.description}", data={"rule_id": rule.id})

        except Exception as e:
            return AgentResult(success=False, message=f"Failed to create rule: {e}")
```

- [ ] **Step 2: Create `src/agent_proxy/agents/mock_agent.py`**

```python
"""MockAgent: generates mock response data from traffic patterns."""
from __future__ import annotations

from agent_proxy.agents.base import BaseAgent, AgentResult
from agent_proxy.core.models import ProxyRule, RuleCondition, RuleAction


class MockAgent(BaseAgent):
    """Generates mock response data based on captured traffic patterns."""

    def get_system_prompt(self) -> str:
        return """You are a mock data generator. Analyze the provided HTTP traffic and generate realistic mock response data.

Return a JSON object:
{
  "url_pattern": "the URL pattern to mock",
  "status_code": 200,
  "mock_body": "JSON string of the mock response body"
}

The mock data should match the structure of the actual response but use placeholder values."""

    async def execute(self, user_input: str) -> AgentResult:
        # Find flows mentioned in the input
        flows = list(self.store.flows.values())
        # Extract URL pattern from input
        import re
        url_match = re.search(r'[/\w]+', user_input)
        url_pattern = url_match.group(0) if url_match else user_input

        # Find matching flows
        matching = [f for f in flows if url_pattern in f.url]

        if not matching:
            return AgentResult(success=False, message=f"No captured traffic matching '{url_pattern}'")

        # Use the most recent matching flow
        flow = matching[-1]
        context = f"Request: {flow.method} {flow.url}\nResponse status: {flow.status_code}\nResponse body: {flow.response_body.decode() if flow.response_body else 'empty'}"

        try:
            result = await self.llm.call_json(
                self.get_system_prompt(),
                f"Generate mock data based on this traffic:\n{context}",
            )

            body = result.get("mock_body", "{}").encode()
            rule = ProxyRule(
                description=f"Mock {url_pattern}",
                condition=RuleCondition(url_pattern=url_pattern),
                action=RuleAction(type="mock", status_code=result.get("status_code", 200), body=body),
                source="ai",
            )
            self.store.add_rule(rule)
            return AgentResult(success=True, message=f"Mock created for {url_pattern}", data={"rule_id": rule.id})

        except Exception as e:
            return AgentResult(success=False, message=f"Failed to generate mock: {e}")
```

- [ ] **Step 3: Create `src/agent_proxy/agents/security_agent.py`**

```python
"""SecurityAgent: detects security issues in captured traffic."""
from __future__ import annotations

from agent_proxy.agents.base import BaseAgent, AgentResult


class SecurityAgent(BaseAgent):
    """Analyzes captured traffic for security issues."""

    def get_system_prompt(self) -> str:
        return """You are a security analyst. Review the provided HTTP traffic for security issues.

Check for:
1. Sensitive data exposure (API keys, passwords, tokens in responses)
2. Missing security headers (Content-Security-Policy, X-Frame-Options, HSTS)
3. XSS patterns (unescaped user input in responses)
4. SQL injection indicators (error messages with SQL syntax)
5. Unencrypted credentials (passwords sent in query params or without TLS)

Return a JSON array of issues:
[
  {"flow_id": "abc123", "issue": "description", "severity": "high|medium|low", "detail": "explanation"}
]

If no issues found, return an empty array []."""

    async def execute(self, user_input: str) -> AgentResult:
        flows = list(self.store.flows.values())
        if not flows:
            return AgentResult(success=False, message="No traffic captured yet")

        # Build context from recent flows (limit to 20)
        recent = flows[-20:]
        context = "\n---\n".join(
            f"Flow {f.id}: {f.method} {f.url} → {f.status_code}\n"
            f"  Response headers: {f.response_headers}\n"
            f"  Response body: {f.response_body.decode()[:500] if f.response_body else 'empty'}"
            for f in recent
        )

        try:
            issues = await self.llm.call_json(
                self.get_system_prompt(),
                f"Analyze these flows for security issues:\n{context}",
            )

            if isinstance(issues, list):
                # Tag flows with issues
                for issue in issues:
                    flow_id = issue.get("flow_id")
                    if flow_id and flow_id in self.store.flows:
                        record = self.store.flows[flow_id]
                        record.security_issues.append(issue.get("issue", ""))

                count = len(issues)
                severity_summary = ", ".join(
                    f"{i['severity']}: {i['issue']}" for i in issues if isinstance(i, dict)
                )
                msg = f"Found {count} security issues: {severity_summary}" if issues else "No security issues found"
                return AgentResult(success=True, message=msg, data=issues)

            return AgentResult(success=False, message="Unexpected LLM response format")

        except Exception as e:
            return AgentResult(success=False, message=f"Security analysis failed: {e}")
```

- [ ] **Step 4: Create `src/agent_proxy/agents/analysis_agent.py`**

```python
"""AnalysisAgent: general traffic analysis and summarization."""
from __future__ import annotations

from collections import Counter

from agent_proxy.agents.base import BaseAgent, AgentResult


class AnalysisAgent(BaseAgent):
    """Provides traffic analysis and summaries."""

    def get_system_prompt(self) -> str:
        return """You are a traffic analyst. Review the provided HTTP traffic summary and provide insights.

Return a JSON object:
{
  "total_requests": number,
  "endpoints": ["list of unique endpoint paths"],
  "method_distribution": {"GET": N, "POST": N},
  "average_response_size": number,
  "insights": ["list of observations or patterns found"],
  "recommendations": ["list of suggestions for optimization or debugging"]
}"""

    async def execute(self, user_input: str) -> AgentResult:
        flows = list(self.store.flows.values())
        if not flows:
            return AgentResult(success=False, message="No traffic captured yet")

        # Build basic stats
        methods = Counter(f.method for f in flows)
        endpoints = list(set(f.path for f in flows))
        avg_size = sum(f.size for f in flows) / len(flows)

        context = (
            f"Total requests: {len(flows)}\n"
            f"Methods: {dict(methods)}\n"
            f"Endpoints: {endpoints[:20]}\n"
            f"Average response size: {avg_size:.0f} bytes\n"
        )

        try:
            result = await self.llm.call_json(
                self.get_system_prompt(),
                f"Analyze this traffic:\n{context}",
            )

            insights = result.get("insights", [])
            recommendations = result.get("recommendations", [])
            message = "Analysis complete"
            if insights:
                message += "\nInsights:\n" + "\n".join(f"  - {i}" for i in insights)
            if recommendations:
                message += "\nRecommendations:\n" + "\n".join(f"  - {r}" for r in recommendations)

            return AgentResult(success=True, message=message, data=result)

        except Exception as e:
            return AgentResult(success=False, message=f"Analysis failed: {e}")
```

- [ ] **Step 5: Append agent integration tests to `tests/test_agents.py`**

```python
"""Integration tests for agents with mocked LLM."""
import pytest
from unittest.mock import AsyncMock, patch

from agent_proxy.core.store import Store
from agent_proxy.core.config import AppConfig
from agent_proxy.agents.llm import LLMClient
from agent_proxy.agents.rule_agent import RuleAgent
from agent_proxy.agents.mock_agent import MockAgent
from agent_proxy.agents.security_agent import SecurityAgent
from agent_proxy.agents.analysis_agent import AnalysisAgent


@pytest.fixture
def store():
    return Store(AppConfig())


@pytest.fixture
def llm_client():
    config = AppConfig().llm
    return LLMClient(config)


@pytest.fixture
def rule_agent(store, llm_client):
    return RuleAgent(llm_client, store)


@pytest.fixture
def mock_agent(store, llm_client):
    return MockAgent(llm_client, store)


@pytest.fixture
def security_agent(store, llm_client):
    return SecurityAgent(llm_client, store)


@pytest.fixture
def analysis_agent(store, llm_client):
    return AnalysisAgent(llm_client, store)


@pytest.mark.asyncio
async def test_rule_agent_creates_rule(rule_agent, store):
    with patch.object(rule_agent.llm, "call_json", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = {
            "description": "Block admin endpoint",
            "condition": {"url_pattern": "/api/admin", "methods": None, "header_match": None},
            "action": {"type": "block", "status_code": 403, "headers": None, "body": None},
        }
        result = await rule_agent.execute("Block all /api/admin requests")
        assert result.success is True
        assert len(store.rules) == 1


@pytest.mark.asyncio
async def test_security_agent_no_flows(security_agent):
    result = await security_agent.execute("check security")
    assert result.success is False
    assert "No traffic" in result.message


@pytest.mark.asyncio
async def test_analysis_agent_no_flows(analysis_agent):
    result = await analysis_agent.execute("analyze traffic")
    assert result.success is False
    assert "No traffic" in result.message
```

- [ ] **Step 6: Run tests**

```bash
pytest tests/test_agents.py -v
```
Expected: All tests PASS (including previous intent routing tests)

- [ ] **Step 7: Commit**

```bash
git add src/agent_proxy/agents/rule_agent.py src/agent_proxy/agents/mock_agent.py src/agent_proxy/agents/security_agent.py src/agent_proxy/agents/analysis_agent.py tests/test_agents.py
git commit -m "feat: implement RuleAgent, MockAgent, SecurityAgent, AnalysisAgent"
```

---

### Task 7: Memory System

**Files:**
- Create: `src/agent_proxy/memory/working.py`
- Create: `src/agent_proxy/memory/episodic.py`
- Create: `src/agent_proxy/memory/semantic.py`
- Create: `src/agent_proxy/memory/procedural.py`
- Create: `src/agent_proxy/memory/system.py`
- Test: `tests/test_memory.py`

- [ ] **Step 1: Create `src/agent_proxy/memory/working.py`**

```python
"""Working memory: sliding window of recent context."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass


@dataclass
class MemoryEntry:
    role: str  # "user" or "agent"
    content: str


class WorkingMemory:
    """Sliding window of recent conversation."""

    def __init__(self, max_size: int = 20):
        self._entries: deque[MemoryEntry] = deque(maxlen=max_size)

    def add(self, role: str, content: str) -> None:
        self._entries.append(MemoryEntry(role=role, content=content))

    def get_context(self) -> str:
        """Return formatted recent conversation context."""
        return "\n".join(f"{e.role}: {e.content}" for e in self._entries)

    def clear(self) -> None:
        self._entries.clear()

    @property
    def size(self) -> int:
        return len(self._entries)
```

- [ ] **Step 2: Create `src/agent_proxy/memory/episodic.py`**

```python
"""Episodic memory: persistent event log by date."""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class EpisodicEvent:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str = ""
    data: dict = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)


class EpisodicMemory:
    """JSONL-based persistent event log."""

    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or Path.home() / ".agent-proxy" / "memory" / "episodic"
        self.base_dir.mkdir(parents=True, exist_ok=True)

    @property
    def _today_file(self) -> Path:
        return self.base_dir / f"{datetime.now(timezone.utc):%Y-%m-%d}.jsonl"

    def record(self, event_type: str, data: dict, tags: list[str] | None = None) -> EpisodicEvent:
        event = EpisodicEvent(event_type=event_type, data=data, tags=tags or [])
        with open(self._today_file, "a") as f:
            f.write(json.dumps({
                "id": event.id,
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type,
                "data": event.data,
                "tags": event.tags,
            }) + "\n")
        return event

    def get_recent(self, limit: int = 50) -> list[EpisodicEvent]:
        """Get most recent events across all date files."""
        events = []
        for filepath in sorted(self.base_dir.glob("*.jsonl")):
            with open(filepath) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        raw = json.loads(line)
                        events.append(EpisodicEvent(
                            id=raw["id"],
                            timestamp=datetime.fromisoformat(raw["timestamp"]),
                            event_type=raw["event_type"],
                            data=raw["data"],
                            tags=raw.get("tags", []),
                        ))
        return events[-limit:]
```

- [ ] **Step 3: Create `src/agent_proxy/memory/semantic.py`**

```python
"""Semantic memory: abstracted knowledge."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class SemanticEntry:
    fact: str
    confidence: float
    source_episodes: list[str]
    last_verified: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class SemanticMemory:
    """Persistent knowledge store."""

    def __init__(self, path: Path | None = None):
        self.path = path or Path.home() / ".agent-proxy" / "memory" / "semantic.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._entries: list[SemanticEntry] = self._load()

    def _load(self) -> list[SemanticEntry]:
        if self.path.exists():
            with open(self.path) as f:
                raw = json.load(f)
            return [
                SemanticEntry(
                    fact=e["fact"],
                    confidence=e["confidence"],
                    source_episodes=e["source_episodes"],
                    last_verified=datetime.fromisoformat(e["last_verified"]),
                )
                for e in raw
            ]
        return []

    def _save(self) -> None:
        with open(self.path, "w") as f:
            json.dump([
                {
                    "fact": e.fact,
                    "confidence": e.confidence,
                    "source_episodes": e.source_episodes,
                    "last_verified": e.last_verified.isoformat(),
                }
                for e in self._entries
            ], f, indent=2)

    def add(self, entry: SemanticEntry) -> None:
        self._entries.append(entry)
        self._save()

    def get_all(self) -> list[SemanticEntry]:
        return list(self._entries)

    def prune(self, stale_days: int = 7) -> int:
        """Remove entries not verified for stale_days. Returns count pruned."""
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(days=stale_days)
        before = len(self._entries)
        self._entries = [e for e in self._entries if e.last_verified >= cutoff]
        pruned = before - len(self._entries)
        if pruned:
            self._save()
        return pruned
```

- [ ] **Step 4: Create `src/agent_proxy/memory/procedural.py`**

```python
"""Procedural memory: user habits and workflow patterns."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ProceduralEntry:
    pattern: str
    trigger: str
    action_template: str
    usage_count: int = 0


class ProceduralMemory:
    """Persistent behavior pattern store."""

    def __init__(self, path: Path | None = None):
        self.path = path or Path.home() / ".agent-proxy" / "memory" / "procedural.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._entries: list[ProceduralEntry] = self._load()

    def _load(self) -> list[ProceduralEntry]:
        if self.path.exists():
            with open(self.path) as f:
                raw = json.load(f)
            return [ProceduralEntry(**e) for e in raw]
        return []

    def _save(self) -> None:
        with open(self.path, "w") as f:
            json.dump([
                {"pattern": e.pattern, "trigger": e.trigger, "action_template": e.action_template, "usage_count": e.usage_count}
                for e in self._entries
            ], f, indent=2)

    def add(self, entry: ProceduralEntry) -> None:
        self._entries.append(entry)
        self._save()

    def get_all(self) -> list[ProceduralEntry]:
        return list(self._entries)

    def increment_usage(self, pattern: str) -> None:
        for e in self._entries:
            if e.pattern == pattern:
                e.usage_count += 1
                self._save()
                return
```

- [ ] **Step 5: Create `src/agent_proxy/memory/system.py`**

```python
"""Memory system coordinator and self-improvement loop."""
from __future__ import annotations

from pathlib import Path

from agent_proxy.core.config import MemoryConfig
from agent_proxy.agents.llm import LLMClient
from agent_proxy.memory.working import WorkingMemory
from agent_proxy.memory.episodic import EpisodicMemory
from agent_proxy.memory.semantic import SemanticMemory, SemanticEntry
from agent_proxy.memory.procedural import ProceduralMemory, ProceduralEntry


class MemorySystem:
    """Coordinates all memory layers and runs self-improvement loop."""

    def __init__(self, config: MemoryConfig, llm_client: LLMClient | None = None):
        self.config = config
        self.working = WorkingMemory(max_size=config.working_window_size)
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory()
        self.procedural = ProceduralMemory()
        self.llm = llm_client
        self._interaction_count = 0

    def record_interaction(self, user_input: str, agent_result: str) -> None:
        """Record a user-agent interaction."""
        self.working.add("user", user_input)
        self.working.add("agent", agent_result)
        self.episodic.record(
            event_type="interaction",
            data={"user_input": user_input, "agent_result": agent_result},
        )
        self._interaction_count += 1

    async def consolidate(self) -> None:
        """Run self-improvement: extract patterns from episodic memory."""
        if not self.llm:
            return
        if self._interaction_count < self.config.consolidation_interval:
            return

        self._interaction_count = 0
        recent = self.episodic.get_recent(limit=50)

        context = "\n".join(
            f"{e.event_type}: {e.data}" for e in recent
        )

        # Extract semantic memories
        try:
            findings = await self.llm.call_json(
                system_prompt="Extract facts from these interaction events. Return JSON array: [{\"fact\": \"...\", \"confidence\": 0.0-1.0}]",
                user_prompt=f"Extract knowledge from these events:\n{context}",
            )
            if isinstance(findings, list):
                for f in findings:
                    if f.get("confidence", 0) >= self.config.semantic_confidence_threshold:
                        self.semantic.add(SemanticEntry(
                            fact=f["fact"],
                            confidence=f["confidence"],
                            source_episodes=[e.id for e in recent[:5]],
                        ))
        except Exception:
            pass  # Non-critical failure

        # Prune stale memories
        self.semantic.prune(self.config.stale_memory_days)

    def get_context_for_agent(self) -> str:
        """Build context string from all memory layers for agent prompts."""
        parts = []

        # Working memory
        working_ctx = self.working.get_context()
        if working_ctx:
            parts.append(f"Recent conversation:\n{working_ctx}")

        # Semantic memory
        semantic = self.semantic.get_all()
        if semantic:
            parts.append("Known facts:\n" + "\n".join(f"- {e.fact}" for e in semantic))

        # Procedural memory
        procedural = self.procedural.get_all()
        if procedural:
            parts.append("User habits:\n" + "\n".join(f"- {e.pattern}" for e in procedural))

        return "\n---\n".join(parts)
```

- [ ] **Step 6: Create `tests/test_memory.py`**

```python
"""Tests for memory system."""
import tempfile
from pathlib import Path
import pytest

from agent_proxy.core.config import MemoryConfig
from agent_proxy.memory.working import WorkingMemory
from agent_proxy.memory.episodic import EpisodicMemory
from agent_proxy.memory.semantic import SemanticMemory, SemanticEntry
from agent_proxy.memory.procedural import ProceduralMemory, ProceduralEntry
from agent_proxy.memory.system import MemorySystem


def test_working_memory_sliding_window():
    wm = WorkingMemory(max_size=3)
    for i in range(5):
        wm.add("user", f"msg {i}")
    assert wm.size == 3
    assert "msg 0" not in wm.get_context()


def test_working_memory_clear():
    wm = WorkingMemory()
    wm.add("user", "test")
    wm.clear()
    assert wm.size == 0


def test_episodic_memory_record_and_retrieve():
    with tempfile.TemporaryDirectory() as tmp:
        em = EpisodicMemory(Path(tmp))
        em.record("rule_created", {"rule": "test"})
        events = em.get_recent()
        assert len(events) == 1
        assert events[0].event_type == "rule_created"


def test_semantic_memory_save():
    with tempfile.TemporaryDirectory() as tmp:
        sm = SemanticMemory(Path(tmp) / "semantic.json")
        sm.add(SemanticEntry(fact="test fact", confidence=0.9, source_episodes=["ep1"]))
        assert len(sm.get_all()) == 1


def test_procedural_memory():
    with tempfile.TemporaryDirectory() as tmp:
        pm = ProceduralMemory(Path(tmp) / "procedural.json")
        pm.add(ProceduralEntry(pattern="test", trigger="test", action_template="test"))
        pm.increment_usage("test")
        entries = pm.get_all()
        assert entries[0].usage_count == 1
```

- [ ] **Step 7: Run tests**

```bash
pytest tests/test_memory.py -v
```
Expected: All tests PASS

- [ ] **Step 8: Commit**

```bash
git add src/agent_proxy/memory/ tests/test_memory.py
git commit -m "feat: Hermes-inspired four-layer memory system with consolidation"
```

---

### Task 8: TUI Widgets

**Files:**
- Create: `src/agent_proxy/tui/styles.py`
- Create: `src/agent_proxy/tui/widgets/status_bar.py`
- Create: `src/agent_proxy/tui/widgets/flow_list.py`
- Create: `src/agent_proxy/tui/widgets/flow_detail.py`
- Create: `src/agent_proxy/tui/widgets/ai_panel.py`

- [ ] **Step 1: Create `src/agent_proxy/tui/styles.py`**

```python
"""TUI theme constants."""

COLORS = {
    "bg": "#1a1a2e",
    "surface": "#16213e",
    "primary": "#0f3460",
    "accent": "#e94560",
    "text": "#eaeaea",
    "text_muted": "#888888",
    "success": "#00d26a",
    "warning": "#ffc107",
    "error": "#e94560",
}
```

- [ ] **Step 2: Create `src/agent_proxy/tui/widgets/status_bar.py`**

```python
"""Top status bar widget."""
from textual.widgets import Static


class StatusBar(Static):
    """Displays proxy status: domain, port, flow count, engine health."""

    DEFAULT_CSS = """
    StatusBar {
        dock: top;
        background: $primary;
        color: $text;
        padding: 0 1;
        height: 1;
    }
    """

    def update_status(self, domain: str, port: int, flow_count: int, healthy: bool = True) -> None:
        status_icon = "●" if healthy else "✗"
        color = "green" if healthy else "red"
        self.update(
            f"[{color}]{status_icon}[/{color}] "
            f"Proxy: {domain or 'all'} | Port: {port} | "
            f"Flows: {flow_count}"
        )
```

- [ ] **Step 3: Create `src/agent_proxy/tui/widgets/flow_list.py`**

```python
"""Flow list widget (left panel)."""
from textual.widgets import DataTable
from textual.binding import Binding

from agent_proxy.core.models import FlowRecord


class FlowList(DataTable):
    """Scrollable table showing captured HTTP flows."""

    DEFAULT_CSS = """
    FlowList {
        width: 40%;
        height: 1fr;
    }
    """

    BINDINGS = [
        Binding("up", "cursor_up", "Up", show=False),
        Binding("down", "cursor_down", "Down", show=False),
        Binding("enter", "select_row", "Select", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.add_columns("Status", "Method", "Path", "Size", "Duration")
        self._flows: dict[str, FlowRecord] = {}

    def add_flow(self, flow: FlowRecord) -> None:
        """Add a flow to the table."""
        self._flows[flow.id] = flow
        status = str(flow.status_code) if flow.status_code else "..."
        size = f"{flow.size / 1024:.1f}KB" if flow.size > 1024 else f"{flow.size}B"
        duration = f"{flow.duration_ms:.0f}ms"
        self.add_row(status, flow.method, flow.path, size, duration, key=flow.id)

    def get_selected_flow(self) -> FlowRecord | None:
        """Return the currently selected flow record."""
        if self.cursor_row is not None:
            row_key = self.get_row_at(self.cursor_row).key
            return self._flows.get(row_key)
        return None
```

- [ ] **Step 4: Create `src/agent_proxy/tui/widgets/flow_detail.py`**

```python
"""Request detail widget (right panel)."""
from textual.widgets import Static

from agent_proxy.core.models import FlowRecord


class FlowDetail(Static):
    """Shows headers, body, and timing for selected flow."""

    DEFAULT_CSS = """
    FlowDetail {
        width: 60%;
        height: 1fr;
        background: $surface;
        padding: 0 1;
        overflow-y: scroll;
    }
    """

    def show_flow(self, flow: FlowRecord | None) -> None:
        """Display flow details."""
        if not flow:
            self.update("[grey]No flow selected[/grey]")
            return

        headers_text = "\n".join(
            f"  {k}: {v}" for k, v in flow.request_headers.items()
        )
        body_text = ""
        if flow.request_body:
            try:
                body_text = flow.request_body.decode()[:2000]
            except UnicodeDecodeError:
                body_text = "[binary data]"

        resp_body_text = ""
        if flow.response_body:
            try:
                resp_body_text = flow.response_body.decode()[:2000]
            except UnicodeDecodeError:
                resp_body_text = "[binary data]"

        security_text = ""
        if flow.security_issues:
            security_text = f"\n[yellow]⚠ Security Issues:[/yellow]\n" + "\n".join(
                f"  - {issue}" for issue in flow.security_issues
            )

        content = (
            f"[bold]{flow.method}[/bold] [dim]{flow.url}[/dim]\n"
            f"Status: [bold {'green' if flow.status_code and flow.status_code < 400 else 'red'}]{flow.status_code}[/bold {'green' if flow.status_code and flow.status_code < 400 else 'red'}]\n"
            f"Duration: {flow.duration_ms:.0f}ms | Size: {flow.size}B\n"
            f"\n[bold]Request Headers:[/bold]\n{headers_text}\n"
            f"\n[bold]Request Body:[/bold]\n{body_text}\n"
            f"\n[bold]Response Body:[/bold]\n{resp_body_text}\n"
            f"{security_text}"
        )
        self.update(content)
```

- [ ] **Step 5: Create `src/agent_proxy/tui/widgets/ai_panel.py`**

```python
"""AI panel: input field and result output."""
from textual.widgets import Static, Input
from textual.containers import Vertical


class AIPanel(Vertical):
    """AI command input and result display."""

    DEFAULT_CSS = """
    AIPanel {
        dock: bottom;
        height: 4;
        background: $primary;
    }
    AIPanel Input {
        width: 100%;
    }
    AIPanel Static {
        width: 100%;
        height: 2;
        color: $success;
    }
    """

    def compose(self):
        yield Input(placeholder="> Enter natural language command (e.g. 'analyze traffic', 'mock /api/users')", id="ai_input")
        yield Static("", id="ai_output")

    @property
    def input_widget(self) -> Input:
        return self.query_one("#ai_input", Input)

    @property
    def output_widget(self) -> Static:
        return self.query_one("#ai_output", Static)

    def show_result(self, message: str) -> None:
        """Display agent result."""
        # Truncate long messages
        if len(message) > 200:
            message = message[:200] + "..."
        self.output_widget.update(f"[green]✓[/green] {message}")

    def show_error(self, message: str) -> None:
        """Display error."""
        self.output_widget.update(f"[red]✗[/red] {message}")

    def clear_output(self) -> None:
        self.output_widget.update("")
```

- [ ] **Step 6: Commit**

```bash
git add src/agent_proxy/tui/styles.py src/agent_proxy/tui/widgets/
git commit -m "feat: TUI widgets for flow list, detail, AI panel, and status bar"
```

---

### Task 9: TUI Screens & App

**Files:**
- Create: `src/agent_proxy/tui/screens/main.py`
- Create: `src/agent_proxy/tui/screens/cert.py`
- Create: `src/agent_proxy/tui/app.py`

- [ ] **Step 1: Create `src/agent_proxy/tui/screens/cert.py`**

```python
"""Certificate installation guide screen."""
from textual.screen import Screen
from textual.widgets import Static, Footer
from textual.containers import Center
from textual.binding import Binding


class CertScreen(Screen):
    """Guide user through CA certificate installation."""

    BINDINGS = [Binding("escape", "app.pop_screen", "Continue")]

    def compose(self):
        yield Center(
            Static(
                "[bold yellow]CA Certificate Setup Required[/bold yellow]\n\n"
                "Agent Proxy uses a self-signed CA certificate to intercept HTTPS traffic.\n\n"
                "[bold]macOS:[/bold]\n"
                "  1. The certificate is at: ~/.mitmproxy/mitmproxy-ca-cert.pem\n"
                "  2. Open Keychain Access and import the certificate\n"
                "  3. Double-click the certificate → Trust → Always Trust\n\n"
                "[bold]iPhone/iPad:[/bold]\n"
                "  1. Open Safari and go to: http://<your-ip>:8080\n"
                "  2. Download the CA certificate\n"
                "  3. Settings → Profile Downloaded → Install\n"
                "  4. Settings → General → About → Certificate Trust Settings → Enable\n\n"
                "[bold]Android:[/bold]\n"
                "  1. Open browser: http://<your-ip>:8080\n"
                "  2. Download CA certificate\n"
                "  3. Settings → Security → Install from storage\n\n"
                "[dim]Press Escape to continue to the main screen[/dim]",
                id="cert_info",
            )
        )
        yield Footer()
```

- [ ] **Step 2: Create `src/agent_proxy/tui/screens/main.py`**

```python
"""Main screen with three-panel layout."""
from textual.screen import Screen
from textual.containers import Horizontal, Vertical
from textual.widgets import Static

from agent_proxy.core.store import Store
from agent_proxy.tui.widgets.flow_list import FlowList
from agent_proxy.tui.widgets.flow_detail import FlowDetail
from agent_proxy.tui.widgets.ai_panel import AIPanel
from agent_proxy.tui.widgets.status_bar import StatusBar


class MainScreen(Screen):
    """Main TUI screen with flow list, detail, and AI input."""

    CSS = """
    Screen {
        layout: vertical;
    }
    #main_area {
        height: 1fr;
    }
    """

    def __init__(self, store: Store):
        super().__init__()
        self.store = store

    def compose(self):
        yield StatusBar(id="status_bar")
        with Horizontal(id="main_area"):
            yield FlowList(id="flow_list")
            yield FlowDetail(id="flow_detail")
        yield AIPanel(id="ai_panel")

    def on_mount(self) -> None:
        """Subscribe to flow events."""
        self.set_interval(1.0, self.refresh_flows)

    async def refresh_flows(self) -> None:
        """Check for new flows and update the list."""
        while not self.store.flow_events.empty():
            flow = self.store.flow_events.get_nowait()
            flow_list = self.query_one("#flow_list", FlowList)
            flow_list.add_flow(flow)

        # Update status bar
        status_bar = self.query_one("#status_bar", StatusBar)
        status_bar.update_status(
            domain="",
            port=8080,
            flow_count=len(self.store.flows),
        )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Show selected flow detail."""
        flow_list = self.query_one("#flow_list", FlowList)
        flow = flow_list.get_selected_flow()
        flow_detail = self.query_one("#flow_detail", FlowDetail)
        flow_detail.show_flow(flow)
```

- [ ] **Step 3: Create `src/agent_proxy/tui/app.py`**

```python
"""Textual App bootstrap."""
from textual.app import App

from agent_proxy.core.store import Store
from agent_proxy.tui.screens.main import MainScreen


class AgentProxyApp(App):
    """Main TUI application."""

    CSS_PATH = None  # Using inline CSS in widgets

    def __init__(self, store: Store):
        super().__init__()
        self.store = store

    def on_mount(self) -> None:
        self.push_screen(MainScreen(self.store))
```

- [ ] **Step 4: Commit**

```bash
git add src/agent_proxy/tui/app.py src/agent_proxy/tui/screens/
git commit -m "feat: TUI screens (main + cert guide) and App bootstrap"
```

---

### Task 10: CLI Entry & System Proxy Config

**Files:**
- Create: `src/agent_proxy/utils/proxy_config.py`
- Create: `src/agent_proxy/utils/qr.py`
- Create: `src/agent_proxy/cli.py`

- [ ] **Step 1: Create `src/agent_proxy/utils/proxy_config.py`**

```python
"""macOS system proxy auto-configuration."""
from __future__ import annotations

import subprocess


def set_system_proxy(host: str, port: int) -> bool:
    """Set macOS system HTTP/HTTPS proxy."""
    try:
        # Get primary network service
        result = subprocess.run(
            ["networksetup", "-getdefaultnetworkservice"],
            capture_output=True, text=True, timeout=5,
        )
        # Parse service name (format: "Network Service: Wi-Fi")
        service = result.stdout.strip().replace("Network Service: ", "")
        if not service:
            service = "Wi-Fi"  # fallback

        subprocess.run(
            ["networksetup", "-setwebproxy", service, host, str(port)],
            capture_output=True, timeout=5,
        )
        subprocess.run(
            ["networksetup", "-setsecurewebproxy", service, host, str(port)],
            capture_output=True, timeout=5,
        )
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def clear_system_proxy() -> bool:
    """Clear macOS system proxy."""
    try:
        result = subprocess.run(
            ["networksetup", "-getdefaultnetworkservice"],
            capture_output=True, text=True, timeout=5,
        )
        service = result.stdout.strip().replace("Network Service: ", "")
        if not service:
            service = "Wi-Fi"

        subprocess.run(
            ["networksetup", "-setwebproxystate", service, "off"],
            capture_output=True, timeout=5,
        )
        subprocess.run(
            ["networksetup", "-setsecurewebproxystate", service, "off"],
            capture_output=True, timeout=5,
        )
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False
```

- [ ] **Step 2: Create `src/agent_proxy/utils/qr.py`**

```python
"""QR code generation."""
from __future__ import annotations

import qrcode


def generate_qr(text: str) -> str:
    """Generate ASCII QR code string for terminal display."""
    import io
    qr = qrcode.QRCode()
    qr.add_data(text)
    qr.make(fit=True)
    buf = io.StringIO()
    qr.print_ascii(tty=True, invert=False, out=buf)
    return buf.getvalue()


def generate_qr_image(text: str, path: str) -> None:
    """Generate QR code as PNG image."""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(path)
```

- [ ] **Step 3: Create `src/agent_proxy/cli.py`**

```python
"""CLI entry point."""
from __future__ import annotations

import argparse
import asyncio
import signal
import sys

import rich

from agent_proxy.core.config import AppConfig
from agent_proxy.core.store import Store
from agent_proxy.memory.system import MemorySystem
from agent_proxy.agents.llm import LLMClient
from agent_proxy.agents.base import IntentRouter
from agent_proxy.agents.rule_agent import RuleAgent
from agent_proxy.agents.mock_agent import MockAgent
from agent_proxy.agents.security_agent import SecurityAgent
from agent_proxy.agents.analysis_agent import AnalysisAgent
from agent_proxy.proxy.engine import ProxyEngine
from agent_proxy.proxy.cert import get_mitmproxy_cert_path, is_cert_installed_macos, get_local_ip
from agent_proxy.tui.screens.cert import CertScreen
from agent_proxy.utils.proxy_config import set_system_proxy, clear_system_proxy
from agent_proxy.utils.qr import generate_qr


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

    # Load config
    config = AppConfig.from_yaml()

    # Override with CLI args
    domains = args.domain or config.capture.default_domains
    if args.port:
        config.proxy.listen_port = args.port
    if args.api_key:
        config.llm.api_key = args.api_key
    if args.model:
        config.llm.model = args.model
    if args.no_system_proxy:
        config.proxy.auto_system_proxy = False

    # Check CA certificate
    if not args.no_cert_check:
        cert_path = get_mitmproxy_cert_path()
        if not cert_path.exists():
            rich.print("[yellow]Warning: mitmproxy CA certificate not found.[/yellow]")
            rich.print("HTTPS interception will not work without it.")
            rich.print(f"Install the cert from: {cert_path}")

    # Initialize Store
    store = Store(config)

    # Initialize Memory System
    llm_client = LLMClient(config.llm) if config.llm.api_key else None
    memory = MemorySystem(config.memory, llm_client)

    # Initialize Agents
    agents = {
        "rule": RuleAgent(llm_client, store) if llm_client else None,
        "mock": MockAgent(llm_client, store) if llm_client else None,
        "security": SecurityAgent(llm_client, store) if llm_client else None,
        "analysis": AnalysisAgent(llm_client, store) if llm_client else None,
    }

    # Print startup info
    rich.print(f"[bold green]Agent Proxy[/bold green] starting...")
    rich.print(f"  Domains: {', '.join(domains) if domains else 'all'}")
    rich.print(f"  Port: {config.proxy.listen_port}")
    rich.print(f"  Local IP: {get_local_ip()}")

    # Set system proxy
    if config.proxy.auto_system_proxy:
        set_system_proxy("127.0.0.1", config.proxy.listen_port)

    # Start proxy engine
    engine = ProxyEngine(store, config, domains)

    # Run the TUI
    async def run():
        await engine.start()

        app = AgentProxyApp(store)

        # Handle AI input from TUI
        # (This is wired up through the TUI's on_submit handler in MainScreen)
        # For now, the TUI captures the input and we process it via the app

        try:
            await app.run_async()
        finally:
            # Cleanup
            if config.proxy.auto_system_proxy:
                clear_system_proxy()
            await engine.stop()
            memory.working.clear()  # Working memory cleared on exit

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Commit**

```bash
git add src/agent_proxy/utils/ src/agent_proxy/cli.py
git commit -m "feat: CLI entry point with system proxy config"
```

---

### Task 11: TUI-Agent Integration & README

**Files:**
- Create: `README.md`
- Modify: `src/agent_proxy/tui/app.py` (update to accept agents + memory)
- Modify: `src/agent_proxy/tui/screens/main.py` (add AI input handler)

- [ ] **Step 1: Update `src/agent_proxy/tui/app.py` to accept agents and memory**

Replace the Task 9 version of `app.py` with:

```python
"""Textual App bootstrap."""
from textual.app import App

from agent_proxy.core.store import Store
from agent_proxy.memory.system import MemorySystem
from agent_proxy.tui.screens.main import MainScreen


class AgentProxyApp(App):
    """Main TUI application."""

    CSS_PATH = None  # Using inline CSS in widgets

    def __init__(self, store: Store, agents: dict, memory: MemorySystem):
        super().__init__()
        self.store = store
        self.agents = agents
        self.memory = memory

    def on_mount(self) -> None:
        main = MainScreen(self.store, self.agents, self.memory)
        self.push_screen(main)
```

- [ ] **Step 2: Update `src/agent_proxy/tui/screens/main.py` with AI input handler**

Replace the Task 9 version of `main.py` with:

```python
"""Main screen with three-panel layout."""
from textual.screen import Screen
from textual.containers import Horizontal
from textual.widgets import Input, DataTable

from agent_proxy.core.store import Store
from agent_proxy.memory.system import MemorySystem
from agent_proxy.agents.base import IntentRouter
from agent_proxy.tui.widgets.flow_list import FlowList
from agent_proxy.tui.widgets.flow_detail import FlowDetail
from agent_proxy.tui.widgets.ai_panel import AIPanel
from agent_proxy.tui.widgets.status_bar import StatusBar


class MainScreen(Screen):
    """Main TUI screen with flow list, detail, and AI input."""

    CSS = """
    Screen {
        layout: vertical;
    }
    #main_area {
        height: 1fr;
    }
    """

    def __init__(self, store: Store, agents: dict, memory: MemorySystem):
        super().__init__()
        self.store = store
        self.agents = agents
        self.memory = memory

    def compose(self):
        yield StatusBar(id="status_bar")
        with Horizontal(id="main_area"):
            yield FlowList(id="flow_list")
            yield FlowDetail(id="flow_detail")
        yield AIPanel(id="ai_panel")

    def on_mount(self) -> None:
        """Subscribe to flow events."""
        self.set_interval(1.0, self.refresh_flows)

    async def refresh_flows(self) -> None:
        """Check for new flows and update the list."""
        while not self.store.flow_events.empty():
            flow = self.store.flow_events.get_nowait()
            flow_list = self.query_one("#flow_list", FlowList)
            flow_list.add_flow(flow)

        status_bar = self.query_one("#status_bar", StatusBar)
        status_bar.update_status(
            domain="",
            port=8080,
            flow_count=len(self.store.flows),
        )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Show selected flow detail."""
        flow_list = self.query_one("#flow_list", FlowList)
        flow = flow_list.get_selected_flow()
        flow_detail = self.query_one("#flow_detail", FlowDetail)
        flow_detail.show_flow(flow)

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle AI command input."""
        ai_panel = self.query_one("#ai_panel", AIPanel)
        user_input = event.value
        ai_panel.input_widget.value = ""

        agent_name = IntentRouter.route(user_input)
        agent = self.agents.get(agent_name)

        if not agent:
            ai_panel.show_error("LLM not configured. Use --api-key.")
            return

        result = await agent.execute(user_input)
        self.memory.record_interaction(user_input, result.message)

        if result.success:
            ai_panel.show_result(result.message)
            await self.memory.consolidate()
        else:
            ai_panel.show_error(result.message)
```

Add `from textual.widgets import DataTable` import at the top of main.py.

- [ ] **Step 3: Update `cli.py` run() function**

Replace the `run()` function in `cli.py` (Task 10 Step 3) with the complete version:

```python
    # Run the TUI
    async def run():
        await engine.start()

        app = AgentProxyApp(store, agents, memory)

        try:
            await app.run_async()
        finally:
            if config.proxy.auto_system_proxy:
                clear_system_proxy()
            await engine.stop()
```

Also add the missing import for `get_local_ip`:

```python
from agent_proxy.proxy.cert import get_mitmproxy_cert_path, is_cert_installed_macos, get_local_ip
```

- [ ] **Step 4: Create `README.md`**

```markdown
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

See spec: `docs/superpowers/specs/2026-04-21-agent-proxy-design.md`
```

- [ ] **Step 5: Run full test suite**

```bash
pytest tests/ -v
```

- [ ] **Step 6: Commit**

```bash
git add README.md
git commit -m "docs: add README with usage and feature overview"
```
