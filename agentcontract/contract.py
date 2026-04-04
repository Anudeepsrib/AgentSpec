"""Core Contract decorator and ContractRunner."""

from __future__ import annotations

import functools
import inspect
from typing import Any, Callable

from agentcontract.interceptor import AgentTrace, TraceInterceptor
from agentcontract.result import AgentResult
from agentcontract.snapshot import SnapshotManager
from agentcontract.adapters.base import BaseAdapter


class ContractRunner:
    """Runs agent tests with interception and assertion support."""

    def __init__(
        self,
        adapter: str | BaseAdapter | None = None,
        snapshot_dir: str | None = None,
    ) -> None:
        self._interceptor = TraceInterceptor()
        self._snapshot_manager = SnapshotManager(snapshot_dir)
        self._adapter = self._resolve_adapter(adapter)

    def _resolve_adapter(self, adapter: str | BaseAdapter | None) -> BaseAdapter | None:
        """Resolve adapter string or instance to adapter object."""
        if adapter is None:
            return None

        if isinstance(adapter, BaseAdapter):
            return adapter

        # Import adapters lazily
        if adapter == "openai":
            from agentcontract.adapters.openai import OpenAIAdapter
            return OpenAIAdapter(self._interceptor)
        elif adapter == "anthropic":
            from agentcontract.adapters.anthropic import AnthropicAdapter
            return AnthropicAdapter(self._interceptor)
        elif adapter == "langchain":
            from agentcontract.adapters.langchain import LangChainAdapter
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
            return AgentResult(self._interceptor.trace, self._snapshot_manager)

        finally:
            self._interceptor.stop()

    def _wrap_with_chaos(
        self,
        agent: Callable[..., Any],
        chaos: Any,
    ) -> Callable[..., Any]:
        """Wrap agent execution with chaos injection."""
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Chaos injector modifies behavior during execution
            return agent(*args, **kwargs)
        return wrapper

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
            snapshot_mgr = SnapshotManager()

            # Run the test function
            try:
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


class ContractViolation(Exception):
    """Base exception for contract failures."""
    pass
