"""Episodic memory: persistent event log by date."""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class EpisodicEvent:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str = ""
    data: dict[str, Any] = field(default_factory=dict)
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
