"""Exceptions for agentcontract."""


class ContractViolation(AssertionError):
    """Base exception for all contract violations."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            details_str = "\n".join(f"  {k}: {v}" for k, v in self.details.items())
            return f"{self.message}\nDetails:\n{details_str}"
        return self.message


class SnapshotMismatch(ContractViolation):
    """Raised when a snapshot comparison fails."""

    def __init__(
        self,
        message: str,
        expected: list[dict] | None = None,
        actual: list[dict] | None = None,
        diff: str | None = None,
    ) -> None:
        super().__init__(message)
        self.expected = expected or []
        self.actual = actual or []
        self.diff = diff or ""


class ToolNotCalled(ContractViolation):
    """Raised when a required tool was not called."""


class ToolCalledUnexpectedly(ContractViolation):
    """Raised when a tool was called but should not have been."""


class OrderViolation(ContractViolation):
    """Raised when tool call ordering constraints are violated."""


class ArgMismatch(ContractViolation):
    """Raised when tool call arguments don't match expectations."""


class CountMismatch(ContractViolation):
    """Raised when tool call count constraints are violated."""
