"""LangChain adapter for tool call interception."""

from __future__ import annotations

import time
from typing import Any

from agentcontract.adapters.base import BaseAdapter


class InterceptingCallbackHandler:
    """LangChain callback handler that records tool calls."""

    def __init__(self, interceptor: Any) -> None:
        self._interceptor = interceptor
        self._tool_starts: dict[str, float] = {}

    def on_tool_start(
        self,
        serialized: dict[str, Any] | None = None,
        input_str: str = "",
        **kwargs: Any,
    ) -> None:
        """Record tool start."""
        tool_name = serialized.get("name", "unknown") if serialized else "unknown"
        self._tool_starts[tool_name] = time.time()

    def on_tool_end(
        self,
        output: Any,
        serialized: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Record tool end."""
        tool_name = serialized.get("name", "unknown") if serialized else "unknown"
        start_time = self._tool_starts.pop(tool_name, None)
        duration = (time.time() - start_time) * 1000 if start_time else 0.0

        # Extract input from serialized
        args = serialized.get("args", {}) if serialized else {}

        self._interceptor.record(tool_name, args, output, duration)


class LangChainAdapter(BaseAdapter):
    """Adapter for LangChain agents."""

    def run(
        self,
        agent: Any,
        input: str | dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> Any:
        """Run a LangChain agent with interception."""
        # Try to import langchain
        try:
            from langchain.callbacks.base import BaseCallbackHandler
        except ImportError:
            raise ImportError("langchain is required for LangChainAdapter")

        # Create callback handler
        callback = InterceptingCallbackHandler(self._interceptor)

        # Build callbacks list
        callbacks = [callback]

        # Add context callbacks if present
        if context and "callbacks" in context:
            existing = context["callbacks"]
            if isinstance(existing, list):
                callbacks.extend(existing)
            else:
                callbacks.append(existing)

        # Prepare run parameters
        run_kwargs = {"callbacks": callbacks}
        if context:
            run_kwargs.update({k: v for k, v in context.items() if k != "callbacks"})

        # Run the agent
        if isinstance(input, dict):
            result = agent.run(**input, **run_kwargs)
        else:
            result = agent.run(input, **run_kwargs)

        return result
