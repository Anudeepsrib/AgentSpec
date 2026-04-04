"""Tool call interception and recording."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable
from collections.abc import Sequence
import json


@dataclass
class ToolCall:
    """Represents a single tool call in an agent's execution."""

    name: str
    args: dict[str, Any]
    step: int
    timestamp: float
    duration_ms: float = 0.0
    response: Any = field(default=None, repr=False)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "args": self._serialize_args(self.args),
            "step": self.step,
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms,
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
    ) -> ToolCall:
        """Record a tool call."""
        call = ToolCall(
            name=name,
            args=args,
            step=len(self.tool_calls),
            timestamp=time.time(),
            duration_ms=duration_ms,
            response=response,
        )
        self.tool_calls.append(call)
        return call

    def finish(self, output: Any = None) -> None:
        """Mark trace as complete."""
        self.end_time = time.time()
        self.final_output = output

    def get_calls(self, tool_name: str | None = None) -> list[ToolCall]:
        """Get all calls, optionally filtered by name."""
        if tool_name is None:
            return list(self.tool_calls)
        return [c for c in self.tool_calls if c.name == tool_name]

    def has_call(self, tool_name: str) -> bool:
        """Check if a tool was called."""
        return any(c.name == tool_name for c in self.tool_calls)

    def count_calls(self, tool_name: str) -> int:
        """Count calls to a specific tool."""
        return sum(1 for c in self.tool_calls if c.name == tool_name)

    def index_of(self, tool_name: str) -> int:
        """Get the step index of the first call to a tool."""
        for i, call in enumerate(self.tool_calls):
            if call.name == tool_name:
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

    def __init__(self) -> None:
        self.trace = AgentTrace()
        self._active: bool = False

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

    def record(
        self,
        name: str,
        args: dict[str, Any],
        response: Any = None,
        duration_ms: float = 0.0,
    ) -> ToolCall:
        """Record a tool call if active."""
        if not self._active:
            raise RuntimeError("Interceptor not started")
        return self.trace.record_call(name, args, response, duration_ms)

    def wrap_tool(
        self,
        func: Callable[..., Any],
        tool_name: str | None = None,
    ) -> Callable[..., Any]:
        """Wrap a tool function to intercept calls."""
        name = tool_name or getattr(func, "__name__", "unknown")

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration = (time.time() - start) * 1000
                call_args = kwargs if kwargs else ({"args": args} if args else {})
                self.record(name, call_args, result, duration)
                return result
            except Exception as e:
                duration = (time.time() - start) * 1000
                call_args = kwargs if kwargs else ({"args": args} if args else {})
                self.record(name, call_args, e, duration)
                raise

        return wrapper
