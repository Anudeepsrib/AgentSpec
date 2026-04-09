"""Tool call interception and recording."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCall:
    """Represents a single tool call in an agent's execution."""

    name: str
    args: dict[str, Any]
    step: int
    timestamp: float
    duration_ms: float = 0.0
    agent_id: str | None = None
    response: Any = field(default=None, repr=False)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "args": self._serialize_args(self.args),
            "step": self.step,
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms,
            "agent_id": self.agent_id,
        }

    @staticmethod
    def _serialize_args(args: Any) -> Any:
        """Serialize arguments to JSON-compatible format."""
        try:
            json.dumps(args)
            return args
        except (TypeError, ValueError):
            return str(args)


@dataclass
class AgentTrace:
    """Complete execution trace of an agent."""

    tool_calls: list[ToolCall] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    final_output: Any = None

    def record_call(
        self,
        name: str,
        args: dict[str, Any],
        response: Any = None,
        duration_ms: float = 0.0,
        agent_id: str | None = None,
    ) -> ToolCall:
        """Record a tool call."""
        call = ToolCall(
            name=name,
            args=args,
            step=len(self.tool_calls),
            timestamp=time.time(),
            duration_ms=duration_ms,
            agent_id=agent_id,
            response=response,
        )
        self.tool_calls.append(call)
        return call

    def finish(self, output: Any = None) -> None:
        """Mark trace as complete."""
        self.end_time = time.time()
        self.final_output = output

    def get_calls(self, tool_name: str | None = None, agent_id: str | None = None) -> list[ToolCall]:
        """Get all calls, optionally filtered by name and agent_id."""
        calls = self.tool_calls
        if tool_name is not None:
            calls = [c for c in calls if c.name == tool_name]
        if agent_id is not None:
            calls = [c for c in calls if c.agent_id == agent_id]
        return calls

    def has_call(self, tool_name: str, agent_id: str | None = None) -> bool:
        """Check if a tool was called."""
        return len(self.get_calls(tool_name, agent_id)) > 0

    def count_calls(self, tool_name: str, agent_id: str | None = None) -> int:
        """Count calls to a specific tool."""
        return len(self.get_calls(tool_name, agent_id))

    def index_of(self, tool_name: str, agent_id: str | None = None) -> int:
        """Get the step index of the first call to a tool."""
        for i, call in enumerate(self.tool_calls):
            if call.name == tool_name and (agent_id is None or call.agent_id == agent_id):
                return i
        return -1

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "tool_calls": [c.to_dict() for c in self.tool_calls],
            "start_time": self.start_time,
            "end_time": self.end_time,
            "final_output": str(self.final_output) if self.final_output is not None else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentTrace:
        """Create from dictionary."""
        trace = cls(
            tool_calls=[
                ToolCall(
                    name=c["name"],
                    args=c.get("args", {}),
                    step=c["step"],
                    timestamp=c["timestamp"],
                    duration_ms=c.get("duration_ms", 0.0),
                    agent_id=c.get("agent_id"),
                )
                for c in data.get("tool_calls", [])
            ],
            start_time=data.get("start_time", 0.0),
            end_time=data.get("end_time"),
            final_output=data.get("final_output"),
        )
        return trace


class TraceInterceptor:
    """Base class for intercepting tool calls from different frameworks."""

    REDACTED = "[REDACTED]"

    def __init__(
        self,
        *,
        sanitize_keys: list[str] | None = None,
    ) -> None:
        self.trace = AgentTrace()
        self._active: bool = False
        self._sanitize_keys: set[str] = set(sanitize_keys or [])

    def start(self) -> None:
        """Start intercepting."""
        self.trace = AgentTrace()
        self._active = True

    def stop(self) -> None:
        """Stop intercepting."""
        self._active = False
        # Only finish if final_output isn't already set
        if self.trace.final_output is None:
            self.trace.finish()

    def _sanitize_args(self, args: dict[str, Any]) -> dict[str, Any]:
        """Redact sensitive keys from tool call arguments.

        Args:
            args: Original tool call arguments.

        Returns:
            Copy of args with sensitive values replaced by ``[REDACTED]``.
        """
        if not self._sanitize_keys:
            return args
        return {
            k: self.REDACTED if k in self._sanitize_keys else v
            for k, v in args.items()
        }

    def record(
        self,
        name: str,
        args: dict[str, Any],
        response: Any = None,
        duration_ms: float = 0.0,
        agent_id: str | None = None,
    ) -> ToolCall:
        """Record a tool call if active."""
        if not self._active:
            raise RuntimeError("Interceptor not started")
        sanitized = self._sanitize_args(args)
        return self.trace.record_call(name, sanitized, response, duration_ms, agent_id)

    def wrap_tool(
        self,
        func: Callable[..., Any],
        tool_name: str | None = None,
        agent_id: str | None = None,
    ) -> Callable[..., Any]:
        """Wrap a tool function to intercept calls."""
        name = tool_name or getattr(func, "__name__", "unknown")

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration = (time.time() - start) * 1000
                call_args = kwargs if kwargs else ({"args": args} if args else {})
                self.record(name, call_args, result, duration, agent_id)
                return result
            except Exception as e:
                duration = (time.time() - start) * 1000
                call_args = kwargs if kwargs else ({"args": args} if args else {})
                self.record(name, call_args, e, duration, agent_id)
                raise

        return wrapper

    def wrap_tool_async(
        self,
        func: Callable[..., Any],
        tool_name: str | None = None,
        agent_id: str | None = None,
    ) -> Callable[..., Any]:
        """Wrap an async tool function to intercept calls."""
        name = tool_name or getattr(func, "__name__", "unknown")

        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = (time.time() - start) * 1000
                call_args = kwargs if kwargs else ({"args": args} if args else {})
                self.record(name, call_args, result, duration, agent_id)
                return result
            except Exception as e:
                duration = (time.time() - start) * 1000
                call_args = kwargs if kwargs else ({"args": args} if args else {})
                self.record(name, call_args, e, duration, agent_id)
                raise

        return wrapper
