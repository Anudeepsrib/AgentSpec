"""AgentSpec — Deterministic testing for AI agents."""

from __future__ import annotations

from importlib.metadata import version, PackageNotFoundError

from agentcontract.contract import contract, ContractRunner, ContractSuite
from agentcontract.result import AgentResult, ToolAssertion, CountAssertion
from agentcontract.storage import RunLogger
from agentcontract.exceptions import (
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
