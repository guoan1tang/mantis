"""MockAgent: generates mock response data from traffic patterns."""
from __future__ import annotations

import re

from agent_proxy.agents.base import BaseAgent, AgentResult
from agent_proxy.core.models import ProxyRule, RuleCondition, RuleAction


class MockAgent(BaseAgent):
    """Generates mock response data based on captured traffic patterns."""

    def get_system_prompt(self) -> str:
        return """You are a mock data generator. Analyze the provided HTTP traffic and generate realistic mock response data.

Return a JSON object:
{
  "url_pattern": "the URL pattern to mock",
  "status_code": 200,
  "mock_body": "JSON string of the mock response body"
}

The mock data should match the structure of the actual response but use placeholder values."""

    async def execute(self, user_input: str) -> AgentResult:
        flows = list(self.store.flows.values())
        url_match = re.search(r'/[\w/]+', user_input)
        url_pattern = url_match.group(0) if url_match else user_input

        matching = [f for f in flows if url_pattern in f.url]

        if not matching:
            return AgentResult(success=False, message=f"No captured traffic matching '{url_pattern}'")

        flow = matching[-1]
        context = f"Request: {flow.method} {flow.url}\nResponse status: {flow.status_code}\nResponse body: {flow.response_body.decode(errors='replace') if flow.response_body else 'empty'}"

        try:
            result = await self.llm.call_json(
                self.get_system_prompt(),
                f"Generate mock data based on this traffic:\n{context}",
            )

            body = result.get("mock_body", "{}").encode()
            rule = ProxyRule(
                description=f"Mock {url_pattern}",
                condition=RuleCondition(url_pattern=url_pattern),
                action=RuleAction(type="mock", status_code=result.get("status_code", 200), body=body),
                source="ai",
            )
            self.store.add_rule(rule)
            return AgentResult(success=True, message=f"Mock created for {url_pattern}", data={"rule_id": rule.id})

        except Exception as e:
            return AgentResult(success=False, message=f"Failed to generate mock: {e}")
