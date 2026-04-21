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
