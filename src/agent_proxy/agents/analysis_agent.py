"""AnalysisAgent: general traffic analysis and summarization."""
from __future__ import annotations

from collections import Counter

from agent_proxy.agents.base import BaseAgent, AgentResult


class AnalysisAgent(BaseAgent):
    """Provides traffic analysis and summaries."""

    def get_system_prompt(self) -> str:
        return """You are a traffic analyst. Review the provided HTTP traffic summary and provide insights.

Return a JSON object:
{
  "total_requests": number,
  "endpoints": ["list of unique endpoint paths"],
  "method_distribution": {"GET": N, "POST": N},
  "average_response_size": number,
  "insights": ["list of observations or patterns found"],
  "recommendations": ["list of suggestions for optimization or debugging"]
}"""

    async def execute(self, user_input: str) -> AgentResult:
        flows = list(self.store.flows.values())
        if not flows:
            return AgentResult(success=False, message="No traffic captured yet")

        methods = Counter(f.method for f in flows)
        endpoints = list(set(f.path for f in flows))
        avg_size = sum(f.size for f in flows) / len(flows)

        context = (
            f"Total requests: {len(flows)}\n"
            f"Methods: {dict(methods)}\n"
            f"Endpoints: {endpoints[:20]}\n"
            f"Average response size: {avg_size:.0f} bytes\n"
        )

        try:
            result = await self.llm.call_json(
                self.get_system_prompt(),
                f"Analyze this traffic:\n{context}",
            )

            insights = result.get("insights", [])
            recommendations = result.get("recommendations", [])
            message = "Analysis complete"
            if insights:
                message += "\nInsights:\n" + "\n".join(f"  - {i}" for i in insights)
            if recommendations:
                message += "\nRecommendations:\n" + "\n".join(f"  - {r}" for r in recommendations)

            return AgentResult(success=True, message=message, data=result)

        except Exception as e:
            return AgentResult(success=False, message=f"Analysis failed: {e}")
