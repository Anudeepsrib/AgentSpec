"""Anthropic adapter for tool call interception."""

from __future__ import annotations

import time
from typing import Any

from agentcontract.adapters.base import BaseAdapter


class AnthropicAdapter(BaseAdapter):
    """Adapter for Anthropic API agents."""

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

    def _run_with_client(
        self,
        client: Any,
        input: str | dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> Any:
        """Run with Anthropic client patching."""
        original_create = client.messages.create

        def patched_create(*args: Any, **kwargs: Any) -> Any:
            """Patched create method."""
            start = time.time()
            response = original_create(*args, **kwargs)
            duration = (time.time() - start) * 1000

            # Extract tool_use blocks from response
            if hasattr(response, "content") and response.content:
                for block in response.content:
                    if hasattr(block, "type") and block.type == "tool_use":
                        name = getattr(block, "name", "unknown")
                        try:
                            input_data = getattr(block, "input", {})
                        except AttributeError:
                            input_data = {}
                        self._interceptor.record(name, input_data, response, duration)

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
