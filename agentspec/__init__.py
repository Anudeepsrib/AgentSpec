"""AgentSpec — Deterministic testing for AI agents."""

from __future__ import annotations

from importlib.metadata import version, PackageNotFoundError

from agentspec.contract import contract, ContractRunner, ContractSuite
from agentspec.result import AgentResult, ToolAssertion, CountAssertion
from agentspec.storage import RunLogger
from agentspec.exceptions import (
    ContractViolation,
    SnapshotMismatch,
    ToolNotCalled,
    ToolCalledUnexpectedly,
    OrderViolation,
    ArgMismatch,
)

try:
    __version__ = version("agentcontract")
except PackageNotFoundError:
    __version__ = "0.0.0-dev"

__all__ = [
    "contract",
    "ContractRunner",
    "ContractSuite",
    "AgentResult",
    "ToolAssertion",
    "CountAssertion",
    "RunLogger",
    "ContractViolation",
    "SnapshotMismatch",
    "ToolNotCalled",
    "ToolCalledUnexpectedly",
    "OrderViolation",
    "ArgMismatch",
]
