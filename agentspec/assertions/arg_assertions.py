"""Standalone argument assertion functions."""


import re
from typing import Any

from agentspec.exceptions import ArgMismatch
from agentspec.interceptor import AgentTrace


def assert_with_args(
    trace: AgentTrace,
    tool_name: str,
    expected_args: dict[str, Any],
    agent_id: str | None = None,
) -> None:
    """Assert exact argument match for at least one call."""
    calls = trace.get_calls(tool_name, agent_id)
    for call in calls:
        if all(call.args.get(k) == v for k, v in expected_args.items()):
            return

    raise ArgMismatch(
        f"No call to '{tool_name}' had exact args: {expected_args}",
        details={"expected_args": expected_args, "actual_calls": [c.args for c in calls]},
    )


def assert_with_args_containing(
    trace: AgentTrace,
    tool_name: str,
    expected_subset: dict[str, Any],
    agent_id: str | None = None,
) -> None:
    """Assert that args contain expected values (subset match)."""
    calls = trace.get_calls(tool_name, agent_id)
    for call in calls:
        if all(_contains(call.args.get(k), v) for k, v in expected_subset.items()):
            return

    raise ArgMismatch(
        f"No call to '{tool_name}' had args containing: {expected_subset}",
        details={"expected_subset": expected_subset, "actual_calls": [c.args for c in calls]},
    )


def assert_with_args_matching(
    trace: AgentTrace,
    tool_name: str,
    patterns: dict[str, str],
    agent_id: str | None = None,
) -> None:
    """Assert that string args match regex patterns."""
    calls = trace.get_calls(tool_name, agent_id)
    for call in calls:
        if all(_matches_regex(call.args.get(k), v) for k, v in patterns.items()):
            return

    raise ArgMismatch(
        f"No call to '{tool_name}' had args matching patterns: {patterns}",
        details={"expected_patterns": patterns, "actual_calls": [c.args for c in calls]},
    )


def _contains(actual: Any, expected: Any) -> bool:
    """Check if actual contains expected (for subset matching)."""
    if actual == expected:
        return True
    if isinstance(actual, str) and isinstance(expected, str):
        return expected in actual
    if isinstance(actual, dict) and isinstance(expected, dict):
        return all(actual.get(k) == v for k, v in expected.items())
    return False


def _matches_regex(value: Any, pattern: str) -> bool:
    """Check if string value matches regex pattern."""
    if not isinstance(value, str):
        return False
    return bool(re.search(pattern, value))
