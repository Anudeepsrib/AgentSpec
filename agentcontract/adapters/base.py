"""Base adapter interface."""

from abc import ABC, abstractmethod
from typing import Any

from agentcontract.interceptor import TraceInterceptor


class BaseAdapter(ABC):
    """Base class for framework-specific adapters."""

    def __init__(self, interceptor: TraceInterceptor) -> None:
        self._interceptor = interceptor

    @abstractmethod
    def run(
        self,
        agent: Any,
        input: str | dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> Any:
        """Run an agent with interception.

        Args:
            agent: The agent to run (type varies by framework)
            input: Input to the agent
            context: Additional context

        Returns:
            Agent result (type varies by framework)
        """
        pass

    @abstractmethod
    async def arun(
        self,
        agent: Any,
        input: str | dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> Any:
        """Run an async agent with interception.

        Args:
            agent: The async agent to run
            input: Input to the agent
            context: Additional context

        Returns:
            Agent result
        """
        pass

    def record_tool_call(
        self,
        name: str,
        args: dict[str, Any],
        response: Any = None,
        duration_ms: float = 0.0,
    ) -> Any:
        """Record a tool call through the interceptor."""
        return self._interceptor.record(name, args, response, duration_ms)
