"""LLM client using OpenAI SDK with async support and retry."""
from __future__ import annotations

import asyncio
import json

from openai import AsyncOpenAI

from agent_proxy.core.config import LLMConfig


class LLMClient:
    """Async OpenAI SDK wrapper with retry logic."""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url if config.base_url else None,
        )

    async def call(
        self,
        system_prompt: str,
        user_prompt: str,
        response_format: type | None = None,
        max_retries: int = 3,
    ) -> str:
        """Call LLM with retry. Returns raw response text."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        kwargs = {
            "model": self.config.model,
            "messages": messages,
            "temperature": 0.1,
        }

        for attempt in range(max_retries):
            try:
                response = await self.client.chat.completions.create(**kwargs)
                return response.choices[0].message.content or ""
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)

    async def call_json(
        self,
        system_prompt: str,
        user_prompt: str,
        max_retries: int = 3,
    ) -> dict | list:
        """Call LLM and parse response as JSON."""
        text = await self.call(system_prompt, user_prompt, max_retries=max_retries)
        # Extract JSON from markdown code blocks if present
        if "```" in text:
            start = text.find("```")
            line_end = text.index("\n", start) if "\n" in text[start:] else start + 3
            block_start = line_end + 1
            end = text.find("```", block_start)
            if end > 0:
                text = text[block_start:end].strip()
        # Fallback: find first { or [ for plain JSON responses
        if text.strip().startswith("{") or text.strip().startswith("["):
            return json.loads(text.strip())
        for ch in ["{", "["]:
            idx = text.find(ch)
            if idx >= 0:
                try:
                    return json.loads(text[idx:])
                except json.JSONDecodeError:
                    continue
        raise json.JSONDecodeError("LLM response is not valid JSON", text, 0)
