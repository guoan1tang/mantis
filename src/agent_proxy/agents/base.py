"""Agent base class and intent router."""
from __future__ import annotations

import re
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
        "domain": [
            "监控域名", "监控域名列表", "域名管理", "添加域名", "移除域名", "删除域名",
        ],
        "rule": [
            "intercept", "change", "modify", "block", "rewrite", "redirect",
            "拦截", "修改", "阻止", "重定向", "改", "规则",
        ],
        "mock": [
            "mock", "generate", "fake data", "fake",
            "模拟", "生成", "假数据", "mock",
        ],
        "security": [
            "security", "vulnerability", "sensitive", "leak", "xss", "injection",
            "安全", "漏洞", "敏感", "泄露", "注入", "xss",
        ],
        "analysis": [
            "analyze", "summary", "pattern", "report", "stats",
            "分析", "总结", "报告", "统计", "什么", "流量", "接口",
        ],
    }

    @classmethod
    def route(cls, user_input: str) -> str:
        """Return the agent name to handle this input."""
        lower = user_input.lower()
        for agent, keywords in cls.AGENT_KEYWORDS.items():
            if agent != "domain":
                if any(kw in lower for kw in keywords):
                    return agent
        # Domain: check explicit domain keywords, or add/remove + domain pattern
        if any(kw in lower for kw in cls.AGENT_KEYWORDS["domain"]):
            return "domain"
        if any(kw in lower for kw in ["添加", "加", "remove", "删除", "取消"]):
            if re.search(r'[\w.-]+\.\w{2,}', user_input):
                return "domain"
        return "analysis"  # default fallback
