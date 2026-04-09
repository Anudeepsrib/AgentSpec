"""Standalone call assertion functions."""

from agentspec.exceptions import ToolCalledUnexpectedly, ToolNotCalled
from agentspec.interceptor import AgentTrace


def assert_must_call(trace: AgentTrace, tool_name: str, agent_id: str | None = None) -> None:
    """Assert that a tool was called."""
    if not trace.has_call(tool_name, agent_id):
        raise ToolNotCalled(f"Tool '{tool_name}' was not called but was required")


def assert_must_not_call(trace: AgentTrace, tool_name: str, agent_id: str | None = None) -> None:
    """Assert that a tool was not called."""
    calls = trace.get_calls(tool_name, agent_id)
    if calls:
        raise ToolCalledUnexpectedly(
            f"Tool '{tool_name}' was called {len(calls)} times but should not have been"
        )
