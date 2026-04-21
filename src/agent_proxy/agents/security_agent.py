"""SecurityAgent: detects security issues in captured traffic."""
from __future__ import annotations

from agent_proxy.agents.base import BaseAgent, AgentResult


class SecurityAgent(BaseAgent):
    """Analyzes captured traffic for security issues."""

    def get_system_prompt(self) -> str:
        return """You are a security analyst. Review the provided HTTP traffic for security issues.

Check for:
1. Sensitive data exposure (API keys, passwords, tokens in responses)
2. Missing security headers (Content-Security-Policy, X-Frame-Options, HSTS)
3. XSS patterns (unescaped user input in responses)
4. SQL injection indicators (error messages with SQL syntax)
5. Unencrypted credentials (passwords sent in query params or without TLS)

Return a JSON array of issues:
[
  {"flow_id": "abc123", "issue": "description", "severity": "high|medium|low", "detail": "explanation"}
]

If no issues found, return an empty array []."""

    async def execute(self, user_input: str) -> AgentResult:
        flows = list(self.store.flows.values())
        if not flows:
            return AgentResult(success=False, message="No traffic captured yet")

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
                msg = f"Found {count} security issues: {severity_summary}" if issues else "No security issues found"
                return AgentResult(success=True, message=msg, data=issues)

            return AgentResult(success=False, message="Unexpected LLM response format")

        except Exception as e:
            return AgentResult(success=False, message=f"Security analysis failed: {e}")
