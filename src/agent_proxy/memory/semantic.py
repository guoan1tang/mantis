"""Semantic memory: abstracted knowledge."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
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
        cutoff = datetime.now(timezone.utc) - timedelta(days=stale_days)
        before = len(self._entries)
        self._entries = [e for e in self._entries if e.last_verified >= cutoff]
        pruned = before - len(self._entries)
        if pruned:
            self._save()
        return pruned
