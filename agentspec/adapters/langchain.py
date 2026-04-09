"""LangChain adapter for tool call interception.

Uses LangChain's callback system to intercept tool calls. Works with
both legacy ``AgentExecutor`` and modern LangGraph agents.

The adapter provides an ``AgentSpecCallbackHandler`` that can also be used
standalone without the adapter class.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from agentspec.adapters.base import BaseAdapter

if TYPE_CHECKING:
    from agentspec.interceptor import TraceInterceptor


class AgentSpecCallbackHandler:
    """LangChain callback handler that records tool calls to AgentSpec traces.

    Can be used standalone::

        from agentspec.adapters.langchain import AgentSpecCallbackHandler

        handler = AgentSpecCallbackHandler(interceptor)
        agent.invoke({"input": "query"}, config={"callbacks": [handler]})

    Or via the adapter::

        runner = ContractRunner(adapter="langchain")
        result = runner.run(agent=my_agent, input="query")
    """

    def __init__(self, interceptor: TraceInterceptor) -> None:
        self._interceptor = interceptor
        self._tool_starts: dict[str, float] = {}

    def on_tool_start(
        self,
        serialized: dict[str, Any] | None = None,
        input_str: str = "",
        *,
        run_id: Any = None,
        **kwargs: Any,
    ) -> None:
        """Called when a tool starts execution."""
        tool_name = "unknown"
        if serialized:
            tool_name = serialized.get(
                "name", serialized.get("id", ["unknown"])[-1] if "id" in serialized else "unknown"
            )

        key = f"{tool_name}_{id(run_id) if run_id else time.time()}"
        self._tool_starts[key] = time.time()
        # Store the tool name mapping for lookup in on_tool_end
        self._tool_starts[f"_name_{key}"] = tool_name

    def on_tool_end(
        self,
        output: Any,
        *,
        run_id: Any = None,
        **kwargs: Any,
    ) -> None:
        """Called when a tool finishes execution."""
        # Find matching start entry
        key = None
        tool_name = "unknown"
        for k in list(self._tool_starts.keys()):
            if k.startswith("_name_"):
                continue
            if run_id and str(id(run_id)) in k:
                key = k
                tool_name = self._tool_starts.pop(f"_name_{k}", "unknown")
                break

        start_time = self._tool_starts.pop(key, None) if key else None
        duration = (time.time() - start_time) * 1000 if start_time else 0.0

        # Extract args from kwargs if available
        args = kwargs.get("tool_input", {})
        if isinstance(args, str):
            args = {"input": args}

        self._interceptor.record(tool_name, args, output, duration)

    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: Any = None,
        **kwargs: Any,
    ) -> None:
        """Called when a tool raises an error."""
        # Clean up start entry
        for k in list(self._tool_starts.keys()):
            if not k.startswith("_name_") and run_id and str(id(run_id)) in k:
                tool_name = self._tool_starts.pop(f"_name_{k}", "unknown")
                start_time = self._tool_starts.pop(k, None)
                duration = (time.time() - start_time) * 1000 if start_time else 0.0
                self._interceptor.record(tool_name, {}, error, duration)
                break


class LangChainAdapter(BaseAdapter):
    """Adapter for LangChain / LangGraph agents.

    Supports:
    - ``AgentExecutor`` (legacy ``.run()`` / ``.invoke()``)
    - LangGraph compiled graphs (``.invoke()`` / ``.ainvoke()``)
    - Any callable that accepts a ``callbacks`` kwarg
    """

    def run(
        self,
        agent: Any,
        input: str | dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> Any:
        """Run a LangChain agent with interception."""
        callback = AgentSpecCallbackHandler(self._interceptor)
        config = self._build_config(callback, context)

        # Modern invoke() API (LangGraph / LCEL)
        if hasattr(agent, "invoke"):
            input_val = input if isinstance(input, dict) else {"input": input}
            return agent.invoke(input_val, config=config)

        # Legacy run() API
        if hasattr(agent, "run"):
            if isinstance(input, dict):
                return agent.run(**input, callbacks=config.get("callbacks", [callback]))
            return agent.run(input, callbacks=config.get("callbacks", [callback]))

        # Callable agent
        if callable(agent):
            if isinstance(input, dict):
                return agent(interceptor=self._interceptor, **input, **(context or {}))
            return agent(input, interceptor=self._interceptor, **(context or {}))

        raise ValueError(f"Unsupported agent type for LangChain adapter: {type(agent)}")

    async def arun(
        self,
        agent: Any,
        input: str | dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> Any:
        """Run an async LangChain agent with interception."""
        callback = AgentSpecCallbackHandler(self._interceptor)
        config = self._build_config(callback, context)

        # Modern ainvoke() API
        if hasattr(agent, "ainvoke"):
            input_val = input if isinstance(input, dict) else {"input": input}
            return await agent.ainvoke(input_val, config=config)

        # Fallback to sync invoke in async context
        if hasattr(agent, "invoke"):
            input_val = input if isinstance(input, dict) else {"input": input}
            return agent.invoke(input_val, config=config)

        # Callable agent
        if callable(agent):
            if isinstance(input, dict):
                return await agent(interceptor=self._interceptor, **input, **(context or {}))
            return await agent(input, interceptor=self._interceptor, **(context or {}))

        raise ValueError(f"Unsupported agent type for LangChain adapter: {type(agent)}")

    @staticmethod
    def _build_config(
        callback: AgentSpecCallbackHandler, context: dict[str, Any] | None
    ) -> dict[str, Any]:
        """Build LangChain config dict with callback handler merged in."""
        config: dict[str, Any] = {"callbacks": [callback]}

        if context:
            if "callbacks" in context:
                existing = context["callbacks"]
                if isinstance(existing, list):
                    config["callbacks"].extend(existing)
                else:
                    config["callbacks"].append(existing)
            # Merge non-callback context into config
            config.update({k: v for k, v in context.items() if k != "callbacks"})

        return config
