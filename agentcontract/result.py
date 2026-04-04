"""AgentResult with fluent assertion API."""

from __future__ import annotations

import re
from typing import Any, Self

from agentcontract.interceptor import AgentTrace, ToolCall
from agentcontract.snapshot import SnapshotManager
from agentcontract.exceptions import (
    ToolNotCalled,
    ToolCalledUnexpectedly,
    OrderViolation,
    ArgMismatch,
    CountMismatch,
    ContractViolation,
)


class AgentResult:
    """Result of running an agent with full assertion capabilities."""

    def __init__(self, trace: AgentTrace, snapshot_manager: SnapshotManager | None = None) -> None:
        self.trace = trace
        self._snapshot_manager = snapshot_manager or SnapshotManager()
        self._assertions_made: list[str] = []

    def must_call(self, tool_name: str) -> ToolAssertion:
        """Assert that a tool must be called at least once."""
        self._assertions_made.append(f"must_call({tool_name})")
        if not self.trace.has_call(tool_name):
            raise ToolNotCalled(
                f"Tool '{tool_name}' was not called but was required",
                details={"required_tool": tool_name, "actual_calls": [c.name for c in self.trace.tool_calls]},
            )
        return ToolAssertion(self, tool_name)

    def must_not_call(self, tool_name: str) -> Self:
        """Assert that a tool must not be called."""
        self._assertions_made.append(f"must_not_call({tool_name})")
        calls = self.trace.get_calls(tool_name)
        if calls:
            raise ToolCalledUnexpectedly(
                f"Tool '{tool_name}' was called but should not have been",
                details={"forbidden_tool": tool_name, "call_count": len(calls), "steps": [c.step for c in calls]},
            )
        return self

    def tool_call_count(self, tool_name: str) -> CountAssertion:
        """Start a count assertion for a tool."""
        return CountAssertion(self, tool_name)

    def snapshot(self, name: str | None = None, update: bool = False) -> Self:
        """Compare or save a snapshot of this trace."""
        snapshot_name = name or "default"
        self._assertions_made.append(f"snapshot({snapshot_name})")
        self._snapshot_manager.compare(snapshot_name, self.trace, update=update)
        return self

    def assert_output_contains(self, text: str) -> Self:
        """Assert that the final output contains text."""
        self._assertions_made.append(f"assert_output_contains({text!r})")
        output = str(self.trace.final_output or "")
        if text not in output:
            raise ContractViolation(
                f"Output does not contain expected text: {text!r}",
                details={"expected_substring": text, "actual_output": output},
            )
        return self

    def assert_output_matches(self, pattern: str) -> Self:
        """Assert that the final output matches a regex pattern."""
        self._assertions_made.append(f"assert_output_matches({pattern!r})")
        output = str(self.trace.final_output or "")
        if not re.search(pattern, output):
            raise ContractViolation(
                f"Output does not match pattern: {pattern!r}",
                details={"pattern": pattern, "actual_output": output},
            )
        return self

    def assert_completed_in(self, max_steps: int) -> Self:
        """Assert that the agent completed within a step limit."""
        self._assertions_made.append(f"assert_completed_in({max_steps})")
        step_count = len(self.trace.tool_calls)
        if step_count > max_steps:
            raise ContractViolation(
                f"Agent took {step_count} steps, exceeding limit of {max_steps}",
                details={"max_allowed": max_steps, "actual_steps": step_count},
            )
        return self

    def get_assertion_summary(self) -> str:
        """Get a summary of assertions made."""
        return f"{len(self._assertions_made)} assertions"


class ToolAssertion:
    """Fluent assertions about a specific tool call."""

    def __init__(self, result: AgentResult, tool_name: str) -> None:
        self._result = result
        self._tool_name = tool_name
        self._calls = result.trace.get_calls(tool_name)

    def with_args(self, **kwargs: Any) -> Self:
        """Assert exact argument match for at least one call."""
        for call in self._calls:
            if all(call.args.get(k) == v for k, v in kwargs.items()):
                return self
        raise ArgMismatch(
            f"No call to '{self._tool_name}' had exact args: {kwargs}",
            details={
                "tool": self._tool_name,
                "expected_args": kwargs,
                "actual_calls": [c.args for c in self._calls],
            },
        )

    def with_args_containing(self, **kwargs: Any) -> Self:
        """Assert that args contain expected values (subset match)."""
        for call in self._calls:
            if all(self._contains(call.args.get(k), v) for k, v in kwargs.items()):
                return self
        raise ArgMismatch(
            f"No call to '{self._tool_name}' had args containing: {kwargs}",
            details={
                "tool": self._tool_name,
                "expected_subset": kwargs,
                "actual_calls": [c.args for c in self._calls],
            },
        )

    def with_args_matching(self, **kwargs: str) -> Self:
        """Assert that string args match regex patterns."""
        for call in self._calls:
            if all(
                self._matches_regex(call.args.get(k), v) for k, v in kwargs.items()
            ):
                return self
        raise ArgMismatch(
            f"No call to '{self._tool_name}' had args matching patterns: {kwargs}",
            details={
                "tool": self._tool_name,
                "expected_patterns": kwargs,
                "actual_calls": [c.args for c in self._calls],
            },
        )

    def before(self, other_tool: str) -> Self:
        """Assert this tool was called before another."""
        my_idx = self._result.trace.index_of(self._tool_name)
        other_idx = self._result.trace.index_of(other_tool)

        if my_idx == -1:
            raise ToolNotCalled(f"Tool '{self._tool_name}' was not called")
        if other_idx == -1:
            raise ToolNotCalled(f"Reference tool '{other_tool}' was not called")

        if my_idx >= other_idx:
            raise OrderViolation(
                f"'{self._tool_name}' (step {my_idx}) should be before '{other_tool}' (step {other_idx})",
                details={"expected_before": self._tool_name, "expected_after": other_tool},
            )
        return self

    def after(self, other_tool: str) -> Self:
        """Assert this tool was called after another."""
        my_idx = self._result.trace.index_of(self._tool_name)
        other_idx = self._result.trace.index_of(other_tool)

        if my_idx == -1:
            raise ToolNotCalled(f"Tool '{self._tool_name}' was not called")
        if other_idx == -1:
            raise ToolNotCalled(f"Reference tool '{other_tool}' was not called")

        if my_idx <= other_idx:
            raise OrderViolation(
                f"'{self._tool_name}' (step {my_idx}) should be after '{other_tool}' (step {other_idx})",
                details={"expected_after": self._tool_name, "expected_before": other_tool},
            )
        return self

    def immediately_after(self, other_tool: str) -> Self:
        """Assert this tool was called immediately after another."""
        my_idx = self._result.trace.index_of(self._tool_name)
        other_idx = self._result.trace.index_of(other_tool)

        if my_idx == -1:
            raise ToolNotCalled(f"Tool '{self._tool_name}' was not called")
        if other_idx == -1:
            raise ToolNotCalled(f"Reference tool '{other_tool}' was not called")

        if my_idx != other_idx + 1:
            raise OrderViolation(
                f"'{self._tool_name}' (step {my_idx}) should be immediately after '{other_tool}' (step {other_idx})",
                details={"expected_after": self._tool_name, "expected_immediately_before": other_tool},
            )
        return self

    def exactly(self, n: int) -> Self:
        """Assert exactly n calls to this tool."""
        count = len(self._calls)
        if count != n:
            raise CountMismatch(
                f"Tool '{self._tool_name}' was called {count} times, expected exactly {n}",
                details={"tool": self._tool_name, "expected": n, "actual": count},
            )
        return self

    def at_least(self, n: int) -> Self:
        """Assert at least n calls to this tool."""
        count = len(self._calls)
        if count < n:
            raise CountMismatch(
                f"Tool '{self._tool_name}' was called {count} times, expected at least {n}",
                details={"tool": self._tool_name, "expected_min": n, "actual": count},
            )
        return self

    def at_most(self, n: int) -> Self:
        """Assert at most n calls to this tool."""
        count = len(self._calls)
        if count > n:
            raise CountMismatch(
                f"Tool '{self._tool_name}' was called {count} times, expected at most {n}",
                details={"tool": self._tool_name, "expected_max": n, "actual": count},
            )
        return self

    @staticmethod
    def _contains(actual: Any, expected: Any) -> bool:
        """Check if actual contains expected (for subset matching)."""
        if actual == expected:
            return True
        if isinstance(actual, str) and isinstance(expected, str):
            return expected in actual
        if isinstance(actual, dict) and isinstance(expected, dict):
            return all(actual.get(k) == v for k, v in expected.items())
        return False

    @staticmethod
    def _matches_regex(value: Any, pattern: str) -> bool:
        """Check if string value matches regex pattern."""
        if not isinstance(value, str):
            return False
        return bool(re.search(pattern, value))


class CountAssertion:
    """Fluent count assertions."""

    def __init__(self, result: AgentResult, tool_name: str) -> None:
        self._result = result
        self._tool_name = tool_name
        self._count = result.trace.count_calls(tool_name)

    def exactly(self, n: int) -> AgentResult:
        """Assert exactly n calls."""
        if self._count != n:
            raise CountMismatch(
                f"Tool '{self._tool_name}' was called {self._count} times, expected exactly {n}",
                details={"tool": self._tool_name, "expected": n, "actual": self._count},
            )
        return self._result

    def at_least(self, n: int) -> AgentResult:
        """Assert at least n calls."""
        if self._count < n:
            raise CountMismatch(
                f"Tool '{self._tool_name}' was called {self._count} times, expected at least {n}",
                details={"tool": self._tool_name, "expected_min": n, "actual": self._count},
            )
        return self._result

    def at_most(self, n: int) -> AgentResult:
        """Assert at most n calls."""
        if self._count > n:
            raise CountMismatch(
                f"Tool '{self._tool_name}' was called {self._count} times, expected at most {n}",
                details={"tool": self._tool_name, "expected_max": n, "actual": self._count},
            )
        return self._result
