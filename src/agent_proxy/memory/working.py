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
