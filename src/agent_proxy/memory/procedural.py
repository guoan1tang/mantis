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
