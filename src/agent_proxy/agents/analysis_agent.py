"""AnalysisAgent: general traffic analysis and summarization."""
from __future__ import annotations

from collections import Counter

from agent_proxy.agents.base import BaseAgent, AgentResult


class AnalysisAgent(BaseAgent):
    """Provides traffic analysis and summaries."""

    def get_system_prompt(self) -> str:
        return """你是一个 HTTP 流量分析专家。请分析提供的 HTTP 流量数据，给出专业的分析结果。

请返回一个 JSON 对象（不要包含其他文本）：
{
  "total_requests": 总请求数,
  "endpoints": ["所有接口路径列表"],
  "method_distribution": {"GET": 数量, "POST": 数量},
  "average_response_size": 平均响应大小（字节）,
  "insights": ["分析发现的模式或问题"],
  "recommendations": ["优化或调试建议"]
}

要求：所有文本（insights 和 recommendations）使用中文。"""

    async def execute(self, user_input: str) -> AgentResult:
        flows = list(self.store.flows.values())
        if not flows:
            return AgentResult(success=False, message="还没有捕获到任何流量")

        methods = Counter(f.method for f in flows)
        endpoints = list(set(f.path for f in flows))
        avg_size = sum(f.size for f in flows) / len(flows)

        context = (
            f"总请求数: {len(flows)}\n"
            f"请求方法: {dict(methods)}\n"
            f"接口列表: {endpoints[:20]}\n"
            f"平均响应大小: {avg_size:.0f} 字节\n"
        )

        try:
            result = await self.llm.call_json(
                self.get_system_prompt(),
                f"用户请求: {user_input}\n\n流量数据:\n{context}",
            )

            insights = result.get("insights", [])
            recommendations = result.get("recommendations", [])
            message = "分析完成"
            if insights:
                message += "\n\n发现:\n" + "\n".join(f"  - {i}" for i in insights)
            if recommendations:
                message += "\n\n建议:\n" + "\n".join(f"  - {r}" for r in recommendations)

            return AgentResult(success=True, message=message, data=result)

        except Exception as e:
            return AgentResult(success=False, message=f"分析失败: {e}")
