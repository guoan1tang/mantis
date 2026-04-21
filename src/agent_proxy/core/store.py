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
