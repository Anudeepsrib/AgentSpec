"""Passing and intentionally failing AgentSpec contract demos.

Run:
    pytest examples/test_contract_demos.py -q -rx

The second test is marked xfail so the demo suite stays green while still
showing the failure mode and message shape.
"""

import pytest

from agentspec import ContractRunner, contract


def verify_identity(user_id: str) -> dict[str, str]:
    return {"user_id": user_id, "status": "verified"}


def transfer_funds(amount: int) -> dict[str, str]:
    return {"transfer_id": f"TX-{amount}", "status": "queued"}


def safe_banking_agent(user_input: str, interceptor=None, **_):
    verify = interceptor.wrap_tool(verify_identity, "verify_identity")
    transfer = interceptor.wrap_tool(transfer_funds, "transfer_funds")

    verify(user_id="user-123")
    transfer(amount=50)
    return "transfer queued"


def unsafe_banking_agent(user_input: str, interceptor=None, **_):
    transfer = interceptor.wrap_tool(transfer_funds, "transfer_funds")

    transfer(amount=50)
    return "transfer queued"


@contract("safe_transfer_passes")
def test_safe_transfer_passes() -> None:
    runner = ContractRunner(persist=False)
    result = runner.run(agent=safe_banking_agent, input="Send $50")

    result.must_call("verify_identity")
    result.must_call("transfer_funds").after("verify_identity")
    result.tool_call_count("transfer_funds").exactly(1)


@pytest.mark.xfail(strict=True, reason="Demonstrates a real contract failure")
@contract("unsafe_transfer_fails")
def test_unsafe_transfer_fails() -> None:
    runner = ContractRunner(persist=False)
    result = runner.run(agent=unsafe_banking_agent, input="Send $50")

    result.must_call("verify_identity")
    result.must_call("transfer_funds").after("verify_identity")
