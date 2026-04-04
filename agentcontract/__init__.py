"""AgentContract - Deterministic testing for AI agents."""

from agentcontract.contract import contract, ContractRunner
from agentcontract.result import AgentResult, ToolAssertion, CountAssertion
from agentcontract.exceptions import (
    ContractViolation,
    SnapshotMismatch,
    ToolNotCalled,
    ToolCalledUnexpectedly,
    OrderViolation,
    ArgMismatch,
)

__version__ = "0.1.0"
__all__ = [
    "contract",
    "ContractRunner",
    "AgentResult",
    "ToolAssertion",
    "CountAssertion",
    "ContractViolation",
    "SnapshotMismatch",
    "ToolNotCalled",
    "ToolCalledUnexpectedly",
    "OrderViolation",
    "ArgMismatch",
]
