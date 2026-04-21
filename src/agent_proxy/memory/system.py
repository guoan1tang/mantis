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
        base = Path(config.memory_dir)
        base.mkdir(parents=True, exist_ok=True)
        self.working = WorkingMemory(max_size=config.working_window_size)
        self.episodic = EpisodicMemory(base / "episodic")
        self.semantic = SemanticMemory(base / "semantic.json")
        self.procedural = ProceduralMemory(base / "procedural.json")
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
        except Exception as exc:
            print(f"[MemorySystem] Consolidation error: {exc}")

        self.semantic.prune(self.config.stale_memory_days)

    def get_context_for_agent(self) -> str:
        """Build context string from all memory layers for agent prompts."""
        parts = []

        working_ctx = self.working.get_context()
        if working_ctx:
            parts.append(f"Recent conversation:\n{working_ctx}")

        semantic = self.semantic.get_all()
        if semantic:
            parts.append("Known facts:\n" + "\n".join(f"- {e.fact}" for e in semantic))

        procedural = self.procedural.get_all()
        if procedural:
            parts.append("User habits:\n" + "\n".join(f"- {e.pattern}" for e in procedural))

        return "\n---\n".join(parts)
