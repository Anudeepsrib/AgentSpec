"""OpenAI adapter for tool call interception."""

from __future__ import annotations

import time
from typing import Any

from agentspec.adapters.base import BaseAdapter


class OpenAIAdapter(BaseAdapter):
    """Adapter for OpenAI API agents."""

    def run(
        self,
        agent: Any,
        input: str | dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> Any:
        """Run an OpenAI-compatible agent with interception.

        This adapter patches the OpenAI client to intercept tool calls.
        """
        # Check if this is an OpenAI client or agent
        if hasattr(agent, "chat") or hasattr(agent, "completions"):
            return self._run_with_client(agent, input, context)
        elif callable(agent):
            # Assume it's an agent function that we should wrap
            return self._run_with_function(agent, input, context)

        raise ValueError(f"Unsupported agent type for OpenAI adapter: {type(agent)}")

    def _run_with_client(
        self,
        client: Any,
        input: str | dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> Any:
        """Run with direct OpenAI client patching."""
        # Store original method
        original_create = None
        if hasattr(client, "chat") and hasattr(client.chat, "completions"):
            original_create = client.chat.completions.create
        elif hasattr(client, "completions"):
            original_create = client.completions.create

        if original_create is None:
            raise ValueError("Could not find completions.create method on client")

        def patched_create(*args: Any, **kwargs: Any) -> Any:
            """Patched create method that intercepts tool calls."""
            # Patch tools if present
            tools = kwargs.get("tools", [])

            for tool in tools:
                if isinstance(tool, dict) and "function" in tool:
                    func_name = tool["function"].get("name")
                    if func_name:
                        # We'll record when this tool is called via the response
                        pass

            # Call original
            start = time.time()
            response = original_create(*args, **kwargs)
            duration = (time.time() - start) * 1000

            # Extract tool calls from response
            if hasattr(response, "choices") and response.choices:
                choice = response.choices[0]
                if hasattr(choice, "message") and choice.message:
                    message = choice.message
                    if hasattr(message, "tool_calls") and message.tool_calls:
                        for tc in message.tool_calls:
                            if hasattr(tc, "function"):
                                func = tc.function
                                name = getattr(func, "name", "unknown")
                                try:
                                    import json
                                    args = json.loads(getattr(func, "arguments", "{}"))
                                except json.JSONDecodeError:
                                    args = {}
                                self._interceptor.record(name, args, response, duration)

            return response

        # Apply patch
        if hasattr(client, "chat") and hasattr(client.chat, "completions"):
            client.chat.completions.create = patched_create
        elif hasattr(client, "completions"):
            client.completions.create = patched_create

        try:
            # Run the agent
            if isinstance(input, dict):
                result = client.chat.completions.create(**input)
            else:
                result = client.chat.completions.create(
                    messages=[{"role": "user", "content": input}],
                    **(context or {}),
                )
            return result
        finally:
            # Restore original
            if hasattr(client, "chat") and hasattr(client.chat, "completions"):
                client.chat.completions.create = original_create
            elif hasattr(client, "completions"):
                client.completions.create = original_create

    def _run_with_function(
        self,
        agent: Any,
        input: str | dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> Any:
        """Run with a callable agent function."""
        # Pass interceptor to agent so it can record tool calls
        if isinstance(input, dict):
            result = agent(interceptor=self._interceptor, **input, **(context or {}))
        else:
            result = agent(input, interceptor=self._interceptor, **(context or {}))
        return result

    async def arun(
        self,
        agent: Any,
        input: str | dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> Any:
        """Run an async OpenAI-compatible agent with interception."""
        # Check if this is an OpenAI client or agent
        if hasattr(agent, "chat") or hasattr(agent, "completions"):
            return await self._arun_with_client(agent, input, context)
        elif callable(agent):
            # Assume it's an agent function that we should wrap
            return await self._arun_with_function(agent, input, context)

        raise ValueError(f"Unsupported agent type for OpenAI adapter: {type(agent)}")

    async def _arun_with_client(
        self,
        client: Any,
        input: str | dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> Any:
        """Run with direct AsyncOpenAI client patching."""
        original_create = None
        if hasattr(client, "chat") and hasattr(client.chat, "completions"):
            original_create = client.chat.completions.create
        elif hasattr(client, "completions"):
            original_create = client.completions.create

        if original_create is None:
            raise ValueError("Could not find completions.create method on client")

        async def patched_create(*args: Any, **kwargs: Any) -> Any:
            """Patched async create method that intercepts tool calls."""
            start = time.time()
            response = await original_create(*args, **kwargs)
            duration = (time.time() - start) * 1000

            if hasattr(response, "choices") and response.choices:
                choice = response.choices[0]
                if hasattr(choice, "message") and choice.message:
                    message = choice.message
                    if hasattr(message, "tool_calls") and message.tool_calls:
                        for tc in message.tool_calls:
                            if hasattr(tc, "function"):
                                func = tc.function
                                name = getattr(func, "name", "unknown")
                                try:
                                    import json
                                    args_dict = json.loads(getattr(func, "arguments", "{}"))
                                except json.JSONDecodeError:
                                    args_dict = {}
                                self._interceptor.record(name, args_dict, response, duration)

            return response

        # Apply patch
        if hasattr(client, "chat") and hasattr(client.chat, "completions"):
            client.chat.completions.create = patched_create
        elif hasattr(client, "completions"):
            client.completions.create = patched_create

        try:
            # Run the agent
            if isinstance(input, dict):
                result = await client.chat.completions.create(**input)
            else:
                result = await client.chat.completions.create(
                    messages=[{"role": "user", "content": input}],
                    **(context or {}),
                )
            return result
        finally:
            # Restore original
            if hasattr(client, "chat") and hasattr(client.chat, "completions"):
                client.chat.completions.create = original_create
            elif hasattr(client, "completions"):
                client.completions.create = original_create

    async def _arun_with_function(
        self,
        agent: Any,
        input: str | dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> Any:
        """Run with an async callable agent function."""
        # Pass interceptor to agent so it can record tool calls
        if isinstance(input, dict):
            result = await agent(interceptor=self._interceptor, **input, **(context or {}))
        else:
            result = await agent(input, interceptor=self._interceptor, **(context or {}))
        return result
