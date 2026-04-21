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


def test_semantic_memory_prune():
    with tempfile.TemporaryDirectory() as tmp:
        sm = SemanticMemory(Path(tmp) / "semantic.json")
        sm.add(SemanticEntry(fact="old fact", confidence=0.9, source_episodes=["ep1"]))
        pruned = sm.prune(stale_days=0)
        assert pruned == 1
        assert len(sm.get_all()) == 0


def test_procedural_memory():
    with tempfile.TemporaryDirectory() as tmp:
        pm = ProceduralMemory(Path(tmp) / "procedural.json")
        pm.add(ProceduralEntry(pattern="test", trigger="test", action_template="test"))
        pm.increment_usage("test")
        entries = pm.get_all()
        assert entries[0].usage_count == 1


def test_memory_system_record_interaction():
    with tempfile.TemporaryDirectory() as tmp:
        config = MemoryConfig(memory_dir=tmp)
        ms = MemorySystem(config)
        ms.record_interaction("block /api/admin", "Rule created")
        assert ms.working.size == 2
        assert ms._interaction_count == 1


def test_memory_system_context_for_agent():
    with tempfile.TemporaryDirectory() as tmp:
        config = MemoryConfig(memory_dir=tmp)
        ms = MemorySystem(config)
        ms.record_interaction("hello", "hi")
        ctx = ms.get_context_for_agent()
        assert "user: hello" in ctx
        assert "agent: hi" in ctx
