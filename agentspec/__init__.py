"""AgentSpec — Deterministic testing for AI agents."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from agentspec.contract import ContractRunner, ContractSuite, contract
from agentspec.exceptions import (
    ArgMismatch,
    ContractViolation,
    OrderViolation,
    SnapshotMismatch,
    ToolCalledUnexpectedly,
    ToolNotCalled,
)
from agentspec.result import AgentResult, CountAssertion, ToolAssertion
from agentspec.storage import RunLogger

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
