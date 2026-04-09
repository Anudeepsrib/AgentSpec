"""Anthropic adapter for tool call interception.

Supports both direct Anthropic client usage and callable agent functions.
Intercepts ``tool_use`` content blocks from Anthropic API responses and
records them in the trace.
"""

from __future__ import annotations

import time
from typing import Any

from agentspec.adapters.base import BaseAdapter


class AnthropicAdapter(BaseAdapter):
    """Adapter for Anthropic API agents.

    Usage with direct client::

        runner = ContractRunner(adapter="anthropic")
        result = runner.run(agent=anthropic_client, input="Search for flights")

    Usage with callable agent::

        runner = ContractRunner(adapter="anthropic")
        result = runner.run(agent=my_agent_fn, input="Search for flights")
    """

    def run(
        self,
        agent: Any,
        input: str | dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> Any:
        """Run an Anthropic-compatible agent with interception."""
        if hasattr(agent, "messages"):
            return self._run_with_client(agent, input, context)
        elif callable(agent):
            return self._run_with_function(agent, input, context)

        raise ValueError(f"Unsupported agent type for Anthropic adapter: {type(agent)}")

    async def arun(
        self,
        agent: Any,
        input: str | dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> Any:
        """Run an async Anthropic-compatible agent with interception."""
        if hasattr(agent, "messages"):
            return await self._arun_with_client(agent, input, context)
        elif callable(agent):
            return await self._arun_with_function(agent, input, context)

        raise ValueError(f"Unsupported agent type for Anthropic adapter: {type(agent)}")

    # ── Sync helpers ────────────────────────────────────────────────────

    def _run_with_client(
        self,
        client: Any,
        input: str | dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> Any:
        """Run with Anthropic client patching."""
        original_create = client.messages.create

        def patched_create(*args: Any, **kwargs: Any) -> Any:
            start = time.time()
            response = original_create(*args, **kwargs)
            duration = (time.time() - start) * 1000
            self._extract_tool_calls(response, duration)
            return response

        client.messages.create = patched_create

        try:
            if isinstance(input, dict):
                result = client.messages.create(**input)
            else:
                result = client.messages.create(
                    messages=[{"role": "user", "content": input}],
                    **(context or {}),
                )
            return result
        finally:
            client.messages.create = original_create

    def _run_with_function(
        self,
        agent: Any,
        input: str | dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> Any:
        """Run with a callable agent function."""
        if isinstance(input, dict):
            result = agent(interceptor=self._interceptor, **input, **(context or {}))
        else:
            result = agent(input, interceptor=self._interceptor, **(context or {}))
        return result

    # ── Async helpers ───────────────────────────────────────────────────

    async def _arun_with_client(
        self,
        client: Any,
        input: str | dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> Any:
        """Run with async Anthropic client patching."""
        original_create = client.messages.create

        async def patched_create(*args: Any, **kwargs: Any) -> Any:
            start = time.time()
            response = await original_create(*args, **kwargs)
            duration = (time.time() - start) * 1000
            self._extract_tool_calls(response, duration)
            return response

        client.messages.create = patched_create

        try:
            if isinstance(input, dict):
                result = await client.messages.create(**input)
            else:
                result = await client.messages.create(
                    messages=[{"role": "user", "content": input}],
                    **(context or {}),
                )
            return result
        finally:
            client.messages.create = original_create

    async def _arun_with_function(
        self,
        agent: Any,
        input: str | dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> Any:
        """Run with an async callable agent function."""
        if isinstance(input, dict):
            result = await agent(interceptor=self._interceptor, **input, **(context or {}))
        else:
            result = await agent(input, interceptor=self._interceptor, **(context or {}))
        return result

    # ── Extraction ──────────────────────────────────────────────────────

    def _extract_tool_calls(self, response: Any, duration: float) -> None:
        """Extract tool_use blocks from an Anthropic API response."""
        if not hasattr(response, "content") or not response.content:
            return

        for block in response.content:
            if hasattr(block, "type") and block.type == "tool_use":
                name = getattr(block, "name", "unknown")
                input_data = getattr(block, "input", {})
                if not isinstance(input_data, dict):
                    input_data = {}
                self._interceptor.record(name, input_data, response, duration)
