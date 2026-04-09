"""Standalone count assertion functions."""


from agentspec.interceptor import AgentTrace
from agentspec.exceptions import CountMismatch


def assert_exactly(trace: AgentTrace, tool_name: str, n: int, agent_id: str | None = None) -> None:
    """Assert exactly n calls."""
    count = trace.count_calls(tool_name, agent_id)
    if count != n:
        raise CountMismatch(
            f"Tool '{tool_name}' was called {count} times, expected exactly {n}",
            details={"expected": n, "actual": count},
        )


def assert_at_least(trace: AgentTrace, tool_name: str, n: int, agent_id: str | None = None) -> None:
    """Assert at least n calls."""
    count = trace.count_calls(tool_name, agent_id)
    if count < n:
        raise CountMismatch(
            f"Tool '{tool_name}' was called {count} times, expected at least {n}",
            details={"expected_min": n, "actual": count},
        )


def assert_at_most(trace: AgentTrace, tool_name: str, n: int, agent_id: str | None = None) -> None:
    """Assert at most n calls."""
    count = trace.count_calls(tool_name, agent_id)
    if count > n:
        raise CountMismatch(
            f"Tool '{tool_name}' was called {count} times, expected at most {n}",
            details={"expected_max": n, "actual": count},
        )
