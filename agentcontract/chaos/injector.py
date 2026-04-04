"""Chaos injection for testing agent resilience."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class ChaosRule:
    """A single chaos rule for a tool."""

    tool_name: str
    failure_after_calls: int | None = None
    error_type: str | None = None
    error_message: str = "Injected chaos failure"
    latency_ms: int = 0
    corrupt_response: Any = None
    corrupt_after_calls: int | None = None
    call_count: int = field(default=0, repr=False)

    def should_fail_now(self) -> bool:
        """Check if this rule should trigger a failure."""
        self.call_count += 1
        if self.failure_after_calls is not None:
            return self.call_count > self.failure_after_calls
        return False

    def should_corrupt_now(self) -> bool:
        """Check if this rule should trigger corruption."""
        if self.corrupt_after_calls is not None:
            return self.call_count > self.corrupt_after_calls
        return False

    def get_error(self) -> Exception:
        """Generate the appropriate error."""
        if self.error_type == "RateLimitError":
            return RateLimitError(self.error_message)
        elif self.error_type == "TimeoutError":
            return TimeoutError(self.error_message)
        elif self.error_type == "ConnectionError":
            return ConnectionError(self.error_message)
        elif self.error_type == "ValueError":
            return ValueError(self.error_message)
        else:
            return RuntimeError(self.error_message)


class RateLimitError(Exception):
    """Simulated rate limit error."""
    pass


class ChaosInjector:
    """Inject failures and chaos into tool calls for resilience testing."""

    def __init__(self, seed: int | None = None) -> None:
        self._rules: dict[str, ChaosRule] = {}
        self._seed = seed
        if seed is not None:
            random.seed(seed)

    def fail_tool(
        self,
        tool_name: str,
        after_calls: int = 0,
        error: str = "RuntimeError",
        message: str = "Injected chaos failure",
    ) -> Self:
        """Configure a tool to fail after a certain number of calls.

        Args:
            tool_name: Name of the tool to inject failures into
            after_calls: Number of successful calls before failing
            error: Error type to raise (RateLimitError, TimeoutError, etc.)
            message: Error message

        Returns:
            Self for chaining
        """
        self._rules[tool_name] = ChaosRule(
            tool_name=tool_name,
            failure_after_calls=after_calls,
            error_type=error,
            error_message=message,
        )
        return self

    def slow_tool(self, tool_name: str, latency_ms: int) -> Self:
        """Add latency to a tool call.

        Args:
            tool_name: Name of the tool to slow down
            latency_ms: Milliseconds of latency to add

        Returns:
            Self for chaining
        """
        if tool_name in self._rules:
            self._rules[tool_name].latency_ms = latency_ms
        else:
            self._rules[tool_name] = ChaosRule(
                tool_name=tool_name,
                latency_ms=latency_ms,
            )
        return self

    def corrupt_tool_response(
        self,
        tool_name: str,
        response: Any,
        after_calls: int = 0,
    ) -> Self:
        """Corrupt the response from a tool.

        Args:
            tool_name: Name of the tool to corrupt
            response: The corrupted response to return
            after_calls: Number of successful calls before corrupting

        Returns:
            Self for chaining
        """
        if tool_name in self._rules:
            self._rules[tool_name].corrupt_response = response
            self._rules[tool_name].corrupt_after_calls = after_calls
        else:
            self._rules[tool_name] = ChaosRule(
                tool_name=tool_name,
                corrupt_response=response,
                corrupt_after_calls=after_calls,
            )
        return self

    def random_failures(self, probability: float = 0.1) -> Self:
        """Enable random failures across all tools (not yet implemented)."""
        # Placeholder for random failure mode
        return self

    def apply(self, tool_name: str, original_func: Callable[..., Any]) -> Callable[..., Any]:
        """Wrap a tool function with chaos injection.

        Args:
            tool_name: Name of the tool
            original_func: Original tool function

        Returns:
            Wrapped function with chaos injection
        """
        rule = self._rules.get(tool_name)

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if rule:
                # Apply latency
                if rule.latency_ms > 0:
                    time.sleep(rule.latency_ms / 1000.0)

                # Check for failure
                if rule.should_fail_now():
                    raise rule.get_error()

                # Check for corruption
                if rule.should_corrupt_now():
                    return rule.corrupt_response

            # Normal execution
            return original_func(*args, **kwargs)

        return wrapper

    def should_record_retry(self, tool_name: str) -> bool:
        """Check if we should record this as a retry after failure."""
        rule = self._rules.get(tool_name)
        if rule and rule.failure_after_calls is not None:
            return rule.call_count > rule.failure_after_calls
        return False

    def get_summary(self) -> dict[str, dict[str, Any]]:
        """Get summary of chaos applied."""
        return {
            name: {
                "calls": rule.call_count,
                "failures": max(0, rule.call_count - (rule.failure_after_calls or 0)),
                "corruptions": max(0, rule.call_count - (rule.corrupt_after_calls or 0)),
            }
            for name, rule in self._rules.items()
        }


def wrap_tool_with_chaos(
    func: Callable[..., Any],
    tool_name: str,
    injector: ChaosInjector,
) -> Callable[..., Any]:
    """Wrap a tool function with chaos injection."""
    return injector.apply(tool_name, func)
