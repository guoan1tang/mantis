"""MockAgent: generates mock response data from traffic patterns."""
from __future__ import annotations

import re

from agent_proxy.agents.base import BaseAgent, AgentResult
from agent_proxy.core.models import ProxyRule, RuleCondition, RuleAction


class MockAgent(BaseAgent):
    """Generates mock response data based on captured traffic patterns."""

    def get_system_prompt(self) -> str:
        return """你是一个模拟数据生成器。分析提供的 HTTP 流量数据，生成合理的模拟响应数据。

返回一个 JSON 对象：
{
  "url_pattern": "要模拟的 URL 模式",
  "status_code": 200,
  "mock_body": "模拟响应体的 JSON 字符串"
}

模拟数据应与实际响应的结构匹配，但使用占位值。"""

    async def execute(self, user_input: str) -> AgentResult:
        flows = list(self.store.flows.values())
        url_match = re.search(r'/[\w/]+', user_input)
        url_pattern = url_match.group(0) if url_match else user_input

        matching = [f for f in flows if url_pattern in f.url]

        if not matching:
            return AgentResult(success=False, message=f"未找到匹配 '{url_pattern}' 的流量")

        flow = matching[-1]
        context = f"请求: {flow.method} {flow.url}\n响应状态: {flow.status_code}\n响应体: {flow.response_body.decode(errors='replace') if flow.response_body else '空'}"

        try:
            result = await self.llm.call_json(
                self.get_system_prompt(),
                f"根据以下流量生成模拟数据:\n{context}",
            )

            body = result.get("mock_body", "{}").encode()
            rule = ProxyRule(
                description=f"模拟 {url_pattern}",
                condition=RuleCondition(url_pattern=url_pattern),
                action=RuleAction(type="mock", status_code=result.get("status_code", 200), body=body),
                source="ai",
            )
            self.store.add_rule(rule)
            return AgentResult(success=True, message=f"模拟已创建: {url_pattern}", data={"rule_id": rule.id})

        except Exception as e:
            return AgentResult(success=False, message=f"模拟生成失败: {e}")
