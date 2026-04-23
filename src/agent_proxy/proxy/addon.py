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

    def __init__(self, store: Store):
        self.store = store
        self._start_times: dict[str, float] = {}
        self._already_added: set[str] = set()  # Track flows already added in request()

    def add_arguments(self, loader: Loader) -> None:
        """No custom arguments needed."""
        pass

    def _should_capture(self, flow: mitmproxy.http.HTTPFlow) -> bool:
        """Check if flow should be captured."""
        if self.store.paused:
            return False
        domains = self.store.domains
        if not domains:
            return True
        host = flow.request.host
        return any(self._domain_match(host, d) for d in domains)

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
                flow.response = mitmproxy.http.Response.make(
                    status_code=action.status_code or 403,
                    content=b"Blocked by Agent Proxy",
                )
                temp_flow.intercepted = True
                temp_flow.status_code = action.status_code or 403
                self._already_added.add(flow.id)
                self.store.add_flow(temp_flow)
                return

            if action.type == "mock":
                flow.response = mitmproxy.http.Response.make(
                    status_code=action.status_code or 200,
                    content=action.body or b"",
                    headers=action.headers,
                )
                temp_flow.intercepted = True
                temp_flow.modified = True
                temp_flow.status_code = action.status_code or 200
                temp_flow.response_body = action.body or b""
                self._already_added.add(flow.id)
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
        if flow.id in self._already_added:
            return  # Already added in request() (block/mock)
        self._already_added.discard(flow.id)

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
            id=flow.id,
            mitmproxy_id=flow.id,
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
