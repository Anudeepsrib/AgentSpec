"""Core Contract decorator and ContractRunner."""

from __future__ import annotations

import functools
import inspect
from collections.abc import Callable
from typing import Any

from agentspec.adapters.base import BaseAdapter
from agentspec.exceptions import ContractViolation
from agentspec.interceptor import AgentTrace, TraceInterceptor
from agentspec.result import AgentResult
from agentspec.snapshot import SnapshotManager
from agentspec.storage import RunLogger


class ContractRunner:
    """Runs agent tests with interception and assertion support."""

    def __init__(
        self,
        adapter: str | BaseAdapter | None = None,
        snapshot_dir: str | None = None,
        *,
        persist: bool = True,
        sanitize_keys: list[str] | None = None,
    ) -> None:
        self._interceptor = TraceInterceptor(sanitize_keys=sanitize_keys)
        self._snapshot_manager = SnapshotManager(snapshot_dir)
        self._adapter = self._resolve_adapter(adapter)
        self._run_logger = RunLogger(enabled=persist)

    def _resolve_adapter(self, adapter: str | BaseAdapter | None) -> BaseAdapter | None:
        """Resolve adapter string or instance to adapter object."""
        if adapter is None:
            return None

        if isinstance(adapter, BaseAdapter):
            return adapter

        # Import adapters lazily
        if adapter == "openai":
            from agentspec.adapters.openai import OpenAIAdapter
            return OpenAIAdapter(self._interceptor)
        elif adapter == "anthropic":
            from agentspec.adapters.anthropic import AnthropicAdapter
            return AnthropicAdapter(self._interceptor)
        elif adapter == "langchain":
            from agentspec.adapters.langchain import LangChainAdapter
            return LangChainAdapter(self._interceptor)

        raise ValueError(f"Unknown adapter: {adapter}")

    def run(
        self,
        agent: Callable[..., Any],
        input: str | dict[str, Any],
        context: dict[str, Any] | None = None,
        chaos: Any | None = None,
    ) -> AgentResult:
        """Run an agent and capture its tool calls.

        Args:
            agent: The agent function to run
            input: Input to the agent (string or dict)
            context: Additional context for the agent
            chaos: Optional chaos injector for failure testing

        Returns:
            AgentResult with full assertion capabilities
        """
        # Start interception
        self._interceptor.start()

        try:
            # Apply chaos if provided
            if chaos is not None:
                agent = self._wrap_with_chaos(agent, chaos)

            # Run the agent with adapter if available
            if self._adapter is not None:
                result = self._adapter.run(agent, input, context)
            else:
                # Direct execution - pass interceptor to agent function
                if isinstance(input, dict):
                    result = agent(interceptor=self._interceptor, **input, **(context or {}))
                else:
                    result = agent(input, interceptor=self._interceptor, **(context or {}))

            # Set final output on trace
            self._interceptor.trace.finish(result)

            # Create and return AgentResult
            agent_result = AgentResult(self._interceptor.trace, self._snapshot_manager)

            # Persist run log
            self._run_logger.log(self._interceptor.trace)

            return agent_result

        finally:
            self._interceptor.stop()

    async def arun(
        self,
        agent: Any,
        input: str | dict[str, Any],
        context: dict[str, Any] | None = None,
        chaos: Any | None = None,
    ) -> AgentResult:
        """Run an async agent and capture its tool calls.

        Args:
            agent: The async agent function to run
            input: Input to the agent
            context: Additional context
            chaos: Optional chaos injector

        Returns:
            AgentResult
        """
        self._interceptor.start()

        try:
            if chaos is not None:
                agent = self._wrap_with_chaos_async(agent, chaos)

            if self._adapter is not None:
                if not hasattr(self._adapter, "arun"):
                    raise NotImplementedError(f"Adapter {type(self._adapter).__name__} does not support arun()")
                result = await self._adapter.arun(agent, input, context)
            else:
                if isinstance(input, dict):
                    result = await agent(interceptor=self._interceptor, **input, **(context or {}))
                else:
                    result = await agent(input, interceptor=self._interceptor, **(context or {}))

            self._interceptor.trace.finish(result)
            agent_result = AgentResult(self._interceptor.trace, self._snapshot_manager)
            self._run_logger.log(self._interceptor.trace)
            return agent_result

        finally:
            self._interceptor.stop()

    def _wrap_with_chaos(
        self,
        agent: Callable[..., Any],
        chaos: Any,
    ) -> Callable[..., Any]:
        """Wrap agent execution with chaos injection.

        Injects the chaos instance so that tools wrapped via
        runner.wrap_tools() will have chaos applied.
        """

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            kwargs.setdefault("chaos", chaos)
            return agent(*args, **kwargs)
        return wrapper

    def _wrap_with_chaos_async(
        self,
        agent: Callable[..., Any],
        chaos: Any,
    ) -> Callable[..., Any]:
        """Wrap async agent execution with chaos injection."""
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            kwargs.setdefault("chaos", chaos)
            return await agent(*args, **kwargs)
        return wrapper

    def wrap_tool(
        self,
        tool: Callable[..., Any],
        name: str | None = None,
        chaos: Any | None = None,
        agent_id: str | None = None,
    ) -> Callable[..., Any]:
        """Wrap a single tool with interception and optional chaos."""
        tool_name = name or getattr(tool, "__name__", "unknown")
        wrapped = chaos.apply(tool_name, tool) if chaos is not None else tool
        return self._interceptor.wrap_tool(wrapped, tool_name=tool_name, agent_id=agent_id)

    def wrap_tool_async(
        self,
        tool: Callable[..., Any],
        name: str | None = None,
        chaos: Any | None = None,
        agent_id: str | None = None,
    ) -> Callable[..., Any]:
        """Wrap a single async tool with interception and optional chaos."""
        tool_name = name or getattr(tool, "__name__", "unknown")
        wrapped = chaos.apply_async(tool_name, tool) if chaos is not None else tool
        return self._interceptor.wrap_tool_async(wrapped, tool_name=tool_name, agent_id=agent_id)

    def wrap_tools(
        self,
        tools: list[Callable[..., Any]],
        chaos: Any | None = None,
        agent_id: str | None = None,
    ) -> list[Callable[..., Any]]:
        """Wrap multiple tools with interception and optional chaos."""
        return [
            self.wrap_tool(tool, chaos=chaos, agent_id=agent_id)
            for tool in tools
        ]

    def wrap_tools_async(
        self,
        tools: list[Callable[..., Any]],
        chaos: Any | None = None,
        agent_id: str | None = None,
    ) -> list[Callable[..., Any]]:
        """Wrap multiple async tools with interception and optional chaos."""
        return [
            self.wrap_tool_async(tool, chaos=chaos, agent_id=agent_id)
            for tool in tools
        ]

    def get_trace(self) -> AgentTrace:
        """Get the execution trace."""
        return self._interceptor.trace

    def create_result(self) -> AgentResult:
        """Create an AgentResult from the current trace."""
        return AgentResult(self._interceptor.trace, self._snapshot_manager)


def contract(name: str | None = None) -> Callable:
    """Decorator for marking and running contract tests.

    Args:
        name: Optional contract name (defaults to function name)

    Example:
        @contract("flight_booking")
        def test_flight_booking():
            runner = ContractRunner(adapter="openai")
            result = runner.run(agent=my_agent, input="Book to NYC")
            result.must_call("search_flights")
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        contract_name = name or func.__name__

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Create a snapshot manager for this test
            SnapshotManager()

            # Run the test function
            try:
                if inspect.iscoroutinefunction(func):
                    # We can't await it here since wrapper might be running synchronously
                    # if the user hasn't properly set up pytest-asyncio, but we must
                    # return a coroutine if the function is async.
                    async def async_run():
                        result = await func(*args, **kwargs)
                        if isinstance(result, AgentResult):
                            return result
                        return result
                    return async_run()
                else:
                    result = func(*args, **kwargs)

                # If result is AgentResult, check if snapshot was called
                if isinstance(result, AgentResult):
                    return result

                return result

            except AssertionError:
                raise
            except Exception as e:
                raise ContractViolation(f"Contract '{contract_name}' failed: {e}") from e

        # Attach metadata for pytest plugin
        wrapper._is_contract = True
        wrapper._contract_name = contract_name

        return wrapper

    return decorator


class ContractSuite:
    """Group related contracts with shared configuration.

    Provides shared runner setup, setup/teardown hooks, and batch execution.

    Usage::

        suite = ContractSuite(
            name="booking_contracts",
            adapter="openai",
            sanitize_keys=["password"],
        )

        @suite.contract("search_flow")
        def test_search(runner):
            result = runner.run(agent=my_agent, input="search flights")
            result.must_call("search_flights")

        @suite.contract("booking_flow")
        def test_booking(runner):
            result = runner.run(agent=my_agent, input="book flight")
            result.must_call("book_flight")

        # Run all contracts in the suite
        report = suite.run_all()
    """

    def __init__(
        self,
        name: str,
        adapter: str | BaseAdapter | None = None,
        snapshot_dir: str | None = None,
        *,
        persist: bool = True,
        sanitize_keys: list[str] | None = None,
    ) -> None:
        self.name = name
        self._adapter = adapter
        self._snapshot_dir = snapshot_dir
        self._persist = persist
        self._sanitize_keys = sanitize_keys
        self._contracts: list[tuple[str, Callable[..., Any]]] = []

    def _make_runner(self) -> ContractRunner:
        """Create a fresh ContractRunner with suite config."""
        return ContractRunner(
            adapter=self._adapter,
            snapshot_dir=self._snapshot_dir,
            persist=self._persist,
            sanitize_keys=self._sanitize_keys,
        )

    def contract(self, name: str) -> Callable[..., Any]:
        """Register a contract test in this suite.

        The decorated function receives a fresh ``ContractRunner`` instance
        as its first argument.
        """
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            @functools.wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                runner = self._make_runner()
                return func(runner, *args, **kwargs)

            wrapper._is_contract = True  # type: ignore[attr-defined]
            wrapper._contract_name = f"{self.name}::{name}"  # type: ignore[attr-defined]
            self._contracts.append((name, wrapper))
            return wrapper

        return decorator

    def run_all(self) -> list[dict[str, Any]]:
        """Execute all registered contracts and return results.

        Returns:
            List of dicts with keys: name, passed, error.
        """
        results: list[dict[str, Any]] = []
        for name, fn in self._contracts:
            try:
                fn()
                results.append({"name": f"{self.name}::{name}", "passed": True, "error": None})
            except Exception as e:
                results.append({"name": f"{self.name}::{name}", "passed": False, "error": str(e)})
        return results

