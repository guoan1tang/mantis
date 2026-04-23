"""RuleAgent: translates natural language to ProxyRule."""
from __future__ import annotations

from agent_proxy.agents.base import BaseAgent, AgentResult
from agent_proxy.core.models import ProxyRule, RuleCondition, RuleAction


class RuleAgent(BaseAgent):
    """Converts natural language commands into executable proxy rules."""

    def get_system_prompt(self) -> str:
        return """你是一个代理规则生成器。请将用户的自然语言指令转换为代理规则的 JSON 对象。

JSON 结构如下：
{
  "description": "自然语言描述",
  "condition": {
    "url_pattern": "URL 匹配模式（使用路径片段，如 '/api/users'）",
    "methods": ["GET", "POST"] 或 null,
    "header_match": {} 或 null
  },
  "action": {
    "type": "以下之一: intercept, modify, mock, block, pass",
    "status_code": 数字 或 null,
    "headers": {} 或 null,
    "body": "响应体字符串 或 null"
  }
}

示例：
- "拦截所有对 /api/admin 的请求" → {"type": "block", "url_pattern": "/api/admin"}
- "将 /api/orders 的 500 错误改为 200，返回空 JSON" → {"type": "modify", "url_pattern": "/api/orders", "status_code": 200, "body": "{}"}
- "模拟 /api/users 返回一个包含一个用户的列表" → {"type": "mock", "url_pattern": "/api/users", "status_code": 200, "body": "[{\\"id\\": 1, \\"name\\": \\"test_user\\"}]"}"""

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
            return AgentResult(success=True, message=f"规则已创建: {rule.description}", data={"rule_id": rule.id})

        except Exception as e:
            return AgentResult(success=False, message=f"规则创建失败: {e}")
