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
    """An executable interceptions/rewrite/mock rule."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    description: str = ""
    condition: RuleCondition = field(default_factory=RuleCondition)
    action: RuleAction = field(default_factory=RuleAction)
    enabled: bool = True
    source: Literal["manual", "ai"] = "manual"
