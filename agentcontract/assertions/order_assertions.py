"""Standalone order assertion functions."""


from agentcontract.interceptor import AgentTrace
from agentcontract.exceptions import OrderViolation


def assert_before(trace: AgentTrace, tool: str, before_tool: str,
                  my_agent_id: str | None = None, other_agent_id: str | None = None) -> None:
    """Assert that tool was called before another tool."""
    my_idx = trace.index_of(tool, my_agent_id)
    other_idx = trace.index_of(before_tool, other_agent_id)

    if my_idx == -1:
        raise OrderViolation(f"Tool '{tool}' was not called")
    if other_idx == -1:
        raise OrderViolation(f"Reference tool '{before_tool}' was not called")

    if my_idx >= other_idx:
        raise OrderViolation(f"'{tool}' (step {my_idx}) should be before '{before_tool}' (step {other_idx})")


def assert_after(trace: AgentTrace, tool: str, after_tool: str,
                 my_agent_id: str | None = None, other_agent_id: str | None = None) -> None:
    """Assert that tool was called after another tool."""
    my_idx = trace.index_of(tool, my_agent_id)
    other_idx = trace.index_of(after_tool, other_agent_id)

    if my_idx == -1:
        raise OrderViolation(f"Tool '{tool}' was not called")
    if other_idx == -1:
        raise OrderViolation(f"Reference tool '{after_tool}' was not called")

    if my_idx <= other_idx:
        raise OrderViolation(f"'{tool}' (step {my_idx}) should be after '{after_tool}' (step {other_idx})")


def assert_immediately_after(trace: AgentTrace, tool: str, after_tool: str,
                               my_agent_id: str | None = None, other_agent_id: str | None = None) -> None:
    """Assert that tool was called immediately after another tool."""
    my_idx = trace.index_of(tool, my_agent_id)
    other_idx = trace.index_of(after_tool, other_agent_id)

    if my_idx == -1:
        raise OrderViolation(f"Tool '{tool}' was not called")
    if other_idx == -1:
        raise OrderViolation(f"Reference tool '{after_tool}' was not called")

    if my_idx != other_idx + 1:
        raise OrderViolation(
            f"'{tool}' (step {my_idx}) should be immediately after '{after_tool}' (step {other_idx})"
        )
