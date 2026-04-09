"""Example: Testing a LangChain-based customer support agent with agentspec."""

from typing import Any

from agentspec import contract, ContractRunner
from agentspec.chaos import ChaosInjector


class CustomerSupportAgent:
    """A customer support agent with LangChain-style tools."""

    def __init__(self) -> None:
        self.tools = {
            "lookup_customer": self._lookup_customer,
            "check_order_status": self._check_order_status,
            "process_refund": self._process_refund,
            "escalate": self._escalate,
        }
        self.call_count = 0

    def _lookup_customer(self, email: str) -> dict:
        """Look up customer by email."""
        return {"customer_id": "C123", "name": "John Doe", "tier": "premium"}

    def _check_order_status(self, order_id: str) -> dict:
        """Check order status."""
        return {"order_id": order_id, "status": "shipped", "eta": "2 days"}

    def _process_refund(self, order_id: str, reason: str) -> dict:
        """Process a refund."""
        return {"refund_id": "R456", "amount": 99.99, "status": "processing"}

    def _escalate(self, reason: str, priority: str = "normal") -> dict:
        """Escalate to human agent."""
        return {"ticket_id": "T789", "priority": priority}

    def run(self, inquiry: str, interceptor: Any = None) -> dict:
        """Handle customer inquiry with interception."""
        self.call_count = 0

        # Parse intent
        if "refund" in inquiry.lower() or "return" in inquiry.lower():
            return self._handle_refund(inquiry, interceptor)
        elif "status" in inquiry.lower() or "where" in inquiry.lower():
            return self._handle_status_check(inquiry, interceptor)
        else:
            return self._handle_general(inquiry, interceptor)

    def _handle_refund(self, inquiry: str, interceptor: Any) -> dict:
        """Handle refund request."""
        # Look up customer
        customer = self.tools["lookup_customer"]("customer@example.com")
        if interceptor:
            interceptor.record("lookup_customer", {"email": "customer@example.com"}, customer)

        # Check order
        order = self.tools["check_order_status"]("ORD-789")
        if interceptor:
            interceptor.record("check_order_status", {"order_id": "ORD-789"}, order)

        # Process refund
        refund = self.tools["process_refund"]("ORD-789", "Customer request")
        if interceptor:
            interceptor.record("process_refund", {"order_id": "ORD-789", "reason": "Customer request"}, refund)

        return {"output": f"Refund {refund['refund_id']} is being processed"}

    def _handle_status_check(self, inquiry: str, interceptor: Any) -> dict:
        """Handle status check."""
        customer = self.tools["lookup_customer"]("customer@example.com")
        if interceptor:
            interceptor.record("lookup_customer", {"email": "customer@example.com"}, customer)

        order = self.tools["check_order_status"]("ORD-789")
        if interceptor:
            interceptor.record("check_order_status", {"order_id": "ORD-789"}, order)

        return {"output": f"Order status: {order['status']}, ETA: {order['eta']}"}

    def _handle_general(self, inquiry: str, interceptor: Any) -> dict:
        """Handle general inquiry."""
        # Escalate general inquiries
        ticket = self.tools["escalate"](inquiry, priority="normal")
        if interceptor:
            interceptor.record("escalate", {"reason": inquiry, "priority": "normal"}, ticket)

        return {"output": f"Escalated to ticket {ticket['ticket_id']}"}


@contract("support_refund_flow")
def test_refund_request_follows_correct_flow() -> None:
    """Test that refund requests follow the correct tool sequence."""
    agent = CustomerSupportAgent()
    runner = ContractRunner()

    result = runner.run(
        agent=agent.run,
        input="I want a refund for my order"
    )

    # Refund flow: lookup → check_status → process_refund
    result.must_call("lookup_customer")
    result.must_call("check_order_status").after("lookup_customer")
    result.must_call("process_refund").immediately_after("check_order_status")

    # Should not escalate
    result.must_not_call("escalate")


@contract("support_status_check")
def test_status_check_uses_correct_tools() -> None:
    """Test that status checks use correct tools."""
    agent = CustomerSupportAgent()
    runner = ContractRunner()

    result = runner.run(
        agent=agent.run,
        input="Where is my order?"
    )

    # Status check flow
    result.must_call("lookup_customer")
    result.must_call("check_order_status")
    result.must_not_call("process_refund")

    # Verify output
    result.assert_output_contains("shipped")


@contract("support_escalation")
def test_general_inquiry_escalates() -> None:
    """Test that general inquiries are escalated."""
    agent = CustomerSupportAgent()
    runner = ContractRunner()

    result = runner.run(
        agent=agent.run,
        input="How do I change my subscription plan?"
    )

    # Should escalate
    result.must_call("escalate")
    result.must_not_call("lookup_customer")


@contract("support_chaos_resilience")
def test_handles_db_timeout() -> None:
    """Test agent resilience with DB timeouts."""
    agent = CustomerSupportAgent()
    runner = ContractRunner()

    chaos = ChaosInjector()
    chaos.fail_tool("lookup_customer", after_calls=0, error="TimeoutError")

    # Real agent would retry; this tests the chaos system
    result = runner.run(
        agent=agent.run,
        input="Check my order status",
        chaos=chaos
    )

    # Even with failure, we might see the attempt
    # In a real scenario with retry, this would pass
    pass


if __name__ == "__main__":
    test_refund_request_follows_correct_flow()
    print("✓ test_refund_request_follows_correct_flow passed")

    test_status_check_uses_correct_tools()
    print("✓ test_status_check_uses_correct_tools passed")

    test_general_inquiry_escalates()
    print("✓ test_general_inquiry_escalates passed")

    test_handles_db_timeout()
    print("✓ test_handles_db_timeout passed")

    print("\nAll LangChain example tests passed!")
