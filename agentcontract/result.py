"""AgentResult with fluent assertion API."""

from __future__ import annotations

import re
from typing import Any, Self

import time

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
from agentcontract.assertions.arg_assertions import assert_with_args, assert_with_args_containing, assert_with_args_matching
from agentcontract.assertions.call_assertions import assert_must_call, assert_must_not_call
from agentcontract.assertions.count_assertions import assert_exactly, assert_at_least, assert_at_most
from agentcontract.assertions.order_assertions import assert_before, assert_after, assert_immediately_after



class AgentResult:
    """Result of running an agent with full assertion capabilities."""

    def __init__(self, trace: AgentTrace, snapshot_manager: SnapshotManager | None = None) -> None:
        self.trace = trace
        self._snapshot_manager = snapshot_manager or SnapshotManager()
        self._assertions_made: list[str] = []

    def must_call(self, tool_name: str, agent_id: str | None = None) -> ToolAssertion:
        """Assert that a tool must be called at least once."""
        self._assertions_made.append(f"must_call({tool_name})")
        assert_must_call(self.trace, tool_name, agent_id)
        return ToolAssertion(self, tool_name, agent_id)

    def must_not_call(self, tool_name: str, agent_id: str | None = None) -> Self:
        """Assert that a tool must not be called."""
        self._assertions_made.append(f"must_not_call({tool_name})")
        assert_must_not_call(self.trace, tool_name, agent_id)
        return self

    def tool_call_count(self, tool_name: str, agent_id: str | None = None) -> CountAssertion:
        """Start a count assertion for a tool."""
        return CountAssertion(self, tool_name, agent_id)

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

    def assert_total_duration_under(self, ms: float) -> Self:
        """Assert that the total execution time was under ms milliseconds."""
        self._assertions_made.append(f"assert_total_duration_under({ms})")
        if self.trace.end_time is None:
            total_time = (time.time() - self.trace.start_time) * 1000
        else:
            total_time = (self.trace.end_time - self.trace.start_time) * 1000
        
        if total_time > ms:
            raise ContractViolation(
                f"Agent took {total_time:.2f}ms, exceeding limit of {ms}ms",
                details={"max_allowed_ms": ms, "actual_ms": total_time},
            )
        return self

    def get_assertion_summary(self) -> str:
        """Get a summary of assertions made."""
        return f"{len(self._assertions_made)} assertions"


class ToolAssertion:
    """Fluent assertions about a specific tool call."""

    def __init__(self, result: AgentResult, tool_name: str, agent_id: str | None = None) -> None:
        self._result = result
        self._tool_name = tool_name
        self._agent_id = agent_id

    def with_args(self, **kwargs: Any) -> Self:
        """Assert exact argument match for at least one call."""
        assert_with_args(self._result.trace, self._tool_name, kwargs, self._agent_id)
        return self

    def with_args_containing(self, **kwargs: Any) -> Self:
        """Assert that args contain expected values (subset match)."""
        assert_with_args_containing(self._result.trace, self._tool_name, kwargs, self._agent_id)
        return self

    def with_args_matching(self, **kwargs: str) -> Self:
        """Assert that string args match regex patterns."""
        assert_with_args_matching(self._result.trace, self._tool_name, kwargs, self._agent_id)
        return self

    def before(self, other_tool: str, agent_id: str | None = None) -> Self:
        """Assert this tool was called before another."""
        assert_before(self._result.trace, self._tool_name, other_tool, self._agent_id, agent_id)
        return self

    def after(self, other_tool: str, agent_id: str | None = None) -> Self:
        """Assert this tool was called after another."""
        assert_after(self._result.trace, self._tool_name, other_tool, self._agent_id, agent_id)
        return self

    def immediately_after(self, other_tool: str, agent_id: str | None = None) -> Self:
        """Assert this tool was called immediately after another."""
        assert_immediately_after(self._result.trace, self._tool_name, other_tool, self._agent_id, agent_id)
        return self

    def exactly(self, n: int) -> Self:
        """Assert exactly n calls to this tool."""
        assert_exactly(self._result.trace, self._tool_name, n, self._agent_id)
        return self

    def at_least(self, n: int) -> Self:
        """Assert at least n calls to this tool."""
        assert_at_least(self._result.trace, self._tool_name, n, self._agent_id)
        return self

    def at_most(self, n: int) -> Self:
        """Assert at most n calls to this tool."""
        assert_at_most(self._result.trace, self._tool_name, n, self._agent_id)
        return self

    def within_ms(self, ms: float) -> Self:
        """Assert that at least one call to this tool completed within ms milliseconds."""
        calls = self._result.trace.get_calls(self._tool_name, self._agent_id)
        if not calls:
            raise ToolNotCalled(f"Tool '{self._tool_name}' was not called")
        
        if not any(c.duration_ms <= ms for c in calls):
            durations = [c.duration_ms for c in calls]
            min_duration = min(durations)
            raise ContractViolation(
                f"No call to '{self._tool_name}' completed within {ms}ms. Fastest was {min_duration:.2f}ms.",
                details={"max_allowed_ms": ms, "actual_durations_ms": durations},
            )
        return self


class CountAssertion:
    """Fluent count assertions."""

    def __init__(self, result: AgentResult, tool_name: str, agent_id: str | None = None) -> None:
        self._result = result
        self._tool_name = tool_name
        self._agent_id = agent_id

    def exactly(self, n: int) -> AgentResult:
        """Assert exactly n calls."""
        assert_exactly(self._result.trace, self._tool_name, n, self._agent_id)
        return self._result

    def at_least(self, n: int) -> AgentResult:
        """Assert at least n calls."""
        assert_at_least(self._result.trace, self._tool_name, n, self._agent_id)
        return self._result

    def at_most(self, n: int) -> AgentResult:
        """Assert at most n calls."""
        assert_at_most(self._result.trace, self._tool_name, n, self._agent_id)
        return self._result

