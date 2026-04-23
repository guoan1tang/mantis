"""SecurityAgent: detects security issues in captured traffic."""
from __future__ import annotations

from agent_proxy.agents.base import BaseAgent, AgentResult


class SecurityAgent(BaseAgent):
    """Analyzes captured traffic for security issues."""

    def get_system_prompt(self) -> str:
        return """你是一个安全分析师。检查提供的 HTTP 流量中的安全问题。

检查项：
1. 敏感数据泄露（API 密钥、密码、令牌暴露在响应中）
2. 缺少安全头部（Content-Security-Policy、X-Frame-Options、HSTS）
3. XSS 模式（未转义的用户输入出现在响应中）
4. SQL 注入迹象（响应中包含 SQL 语法的错误信息）
5. 未加密的凭据（密码在查询参数中或未使用 TLS 传输）

返回一个 JSON 数组：
[
  {"flow_id": "abc123", "issue": "问题描述", "severity": "high|medium|low", "detail": "详细说明"}
]

如果没有发现问题，返回空数组 []。

要求：所有文本（issue 和 detail）使用中文。"""

    async def execute(self, user_input: str) -> AgentResult:
        flows = list(self.store.flows.values())
        if not flows:
            return AgentResult(success=False, message="还没有捕获到任何流量")

        recent = flows[-20:]
        context = "\n---\n".join(
            f"Flow {f.id}: {f.method} {f.url} → {f.status_code}\n"
            f"  Response headers: {f.response_headers}\n"
            f"  Response body: {f.response_body.decode(errors='replace')[:500] if f.response_body else 'empty'}"
            for f in recent
        )

        try:
            issues = await self.llm.call_json(
                self.get_system_prompt(),
                f"Analyze these flows for security issues:\n{context}",
            )

            if isinstance(issues, list):
                for issue in issues:
                    flow_id = issue.get("flow_id")
                    if flow_id and flow_id in self.store.flows:
                        record = self.store.flows[flow_id]
                        record.security_issues.append(issue.get("issue", ""))

                count = len(issues)
                severity_summary = ", ".join(
                    f"{i.get('severity', 'unknown')}: {i.get('issue', 'unknown')}" for i in issues if isinstance(i, dict)
                )
                msg = f"发现 {count} 个安全问题: {severity_summary}" if issues else "未发现安全问题"
                return AgentResult(success=True, message=msg, data=issues)

            return AgentResult(success=False, message="LLM 返回格式异常")

        except Exception as e:
            return AgentResult(success=False, message=f"安全分析失败: {e}")
