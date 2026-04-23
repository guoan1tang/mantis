"""DomainAgent: add/remove monitored domains via natural language."""
from __future__ import annotations

import re

from agent_proxy.agents.base import BaseAgent, AgentResult


class DomainAgent(BaseAgent):
    """Manage monitored domain list."""

    async def execute(self, user_input: str) -> AgentResult:
        lower = user_input.lower()

        # Parse action: add/remove/list
        if any(kw in lower for kw in ["添加", "加", "add"]):
            domain = self._extract_domain(user_input)
            if not domain:
                return AgentResult(success=False, message="未找到域名，例如: add baidu.com")
            if self.store.add_domain(domain):
                return AgentResult(success=True, message=f"已添加监控域名: {domain}")
            return AgentResult(success=False, message=f"域名已存在: {domain}")

        elif any(kw in lower for kw in ["移除", "删除", "remove", "取消"]):
            domain = self._extract_domain(user_input)
            if not domain:
                return AgentResult(success=False, message="未找到域名，例如: remove baidu.com")
            if self.store.remove_domain(domain):
                return AgentResult(success=True, message=f"已移除监控域名: {domain}")
            return AgentResult(success=False, message=f"域名不存在: {domain}")

        else:
            # List current domains
            domains = self.store.domains
            if domains:
                msg = "当前监控域名:\n" + "\n".join(f"  - {d}" for d in domains)
            else:
                msg = "当前未设置监控域名（捕获所有流量）"
            return AgentResult(success=True, message=msg)

    def _extract_domain(self, text: str) -> str:
        """Extract domain from user input."""
        match = re.search(r'[\w.-]+\.\w{2,}', text)
        return match.group(0) if match else ""

    def get_system_prompt(self) -> str:
        return ""  # Not using LLM, keyword-based
