"""Standalone count assertion functions."""


from agentcontract.interceptor import AgentTrace
from agentcontract.exceptions import CountMismatch


def assert_exactly(trace: AgentTrace, tool_name: str, n: int) -> None:
    """Assert exactly n calls."""
    count = trace.count_calls(tool_name)
    if count != n:
        raise CountMismatch(
            f"Tool '{tool_name}' was called {count} times, expected exactly {n}",
            details={"expected": n, "actual": count},
        )


def assert_at_least(trace: AgentTrace, tool_name: str, n: int) -> None:
    """Assert at least n calls."""
    count = trace.count_calls(tool_name)
    if count < n:
        raise CountMismatch(
            f"Tool '{tool_name}' was called {count} times, expected at least {n}",
            details={"expected_min": n, "actual": count},
        )


def assert_at_most(trace: AgentTrace, tool_name: str, n: int) -> None:
    """Assert at most n calls."""
    count = trace.count_calls(tool_name)
    if count > n:
        raise CountMismatch(
            f"Tool '{tool_name}' was called {count} times, expected at most {n}",
            details={"expected_max": n, "actual": count},
        )
