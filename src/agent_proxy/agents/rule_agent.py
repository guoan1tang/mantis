"""RuleAgent: translates natural language to ProxyRule."""
from __future__ import annotations

from agent_proxy.agents.base import BaseAgent, AgentResult
from agent_proxy.core.models import ProxyRule, RuleCondition, RuleAction


class RuleAgent(BaseAgent):
    """Converts natural language commands into executable proxy rules."""

    def get_system_prompt(self) -> str:
        return """You are a proxy rule generator. Convert user instructions into a JSON object representing a proxy rule.

The JSON must have this exact structure:
{
  "description": "natural language description",
  "condition": {
    "url_pattern": "URL pattern to match (use path fragments, e.g. '/api/users')",
    "methods": ["GET", "POST"] or null,
    "header_match": {} or null
  },
  "action": {
    "type": "one of: intercept, modify, mock, block, pass",
    "status_code": number or null,
    "headers": {} or null,
    "body": "response body string or null"
  }
}

Examples:
- "Block all requests to /api/admin" → {"type": "block", "url_pattern": "/api/admin"}
- "Change /api/orders 500 errors to 200 with empty JSON" → {"type": "modify", "url_pattern": "/api/orders", "status_code": 200, "body": "{}"}
- "Mock /api/users to return a list with one user" → {"type": "mock", "url_pattern": "/api/users", "status_code": 200, "body": "[{\\"id\\": 1, \\"name\\": \\"test_user\\"}]"}"""

    async def execute(self, user_input: str) -> AgentResult:
        try:
            rule_json = await self.llm.call_json(
                self.get_system_prompt(),
                user_input,
            )

            cond = rule_json.get("condition", {})
            act = rule_json.get("action", {})
            condition = RuleCondition(
                url_pattern=cond.get("url_pattern"),
                methods=cond.get("methods"),
                header_match=cond.get("header_match"),
            )
            action = RuleAction(
                type=act.get("type", "pass"),
                status_code=act.get("status_code"),
                headers=act.get("headers"),
                body=act.get("body", "").encode() if act.get("body") else None,
            )
            rule = ProxyRule(
                description=rule_json.get("description", user_input),
                condition=condition,
                action=action,
                source="ai",
            )
            self.store.add_rule(rule)
            return AgentResult(success=True, message=f"Rule created: {rule.description}", data={"rule_id": rule.id})

        except Exception as e:
            return AgentResult(success=False, message=f"Failed to create rule: {e}")
