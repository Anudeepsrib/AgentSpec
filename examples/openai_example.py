"""Example: Testing an OpenAI-based flight booking agent with agentspec."""

from typing import Any

from agentspec import ContractRunner, contract
from agentspec.chaos import ChaosInjector


# Simulated OpenAI tool-calling agent
class FlightBookingAgent:
    """A simple flight booking agent that uses OpenAI-style tool calls."""

    def __init__(self) -> None:
        self.tools = {
            "search_flights": self._search_flights,
            "book_flight": self._book_flight,
            "cancel_booking": self._cancel_booking,
        }

    def _search_flights(self, destination: str, date: str | None = None) -> dict:
        """Search for flights."""
        return {
            "flights": [
                {"id": "FL001", "price": 299, "airline": "JetBlue"},
                {"id": "FL002", "price": 350, "airline": "Delta"},
            ]
        }

    def _book_flight(self, flight_id: str, passenger_name: str) -> dict:
        """Book a flight."""
        return {"booking_id": f"BK-{flight_id}", "status": "confirmed"}

    def _cancel_booking(self, booking_id: str) -> dict:
        """Cancel a booking."""
        return {"status": "cancelled"}

    def run(self, user_input: str, interceptor: Any = None) -> dict:
        """Run the agent with interception support."""
        # Simulate tool call detection from LLM response
        # In real usage, this would parse OpenAI tool_calls
        tool_calls = self._parse_intent(user_input)

        results = []
        for tool_name, args in tool_calls:
            if tool_name in self.tools:
                result = self.tools[tool_name](**args)

                # Record via interceptor if available
                if interceptor:
                    interceptor.record(tool_name, args, result)

                results.append({"tool": tool_name, "result": result})

        return {
            "output": f"Completed {len(results)} operations",
            "tool_results": results,
        }

    def _parse_intent(self, user_input: str) -> list[tuple[str, dict]]:
        """Parse user intent into tool calls (simplified)."""
        calls = []

        if "book" in user_input.lower() and "flight" in user_input.lower():
            # First search, then book
            calls.append(("search_flights", {"destination": "NYC", "date": "2024-06-01"}))
            calls.append(("book_flight", {"flight_id": "FL001", "passenger_name": "Test User"}))

        return calls


# Contract tests
@contract("flight_booking_happy_path")
def test_books_correct_flight() -> None:
    """Test that the agent books a flight correctly."""
    agent = FlightBookingAgent()
    runner = ContractRunner()

    result = runner.run(
        agent=agent.run,
        input="Book me a flight to NYC next Tuesday"
    )

    # Assert on the execution
    result.must_call("search_flights")
    result.must_call("book_flight").after("search_flights")
    result.must_call("book_flight").with_args(flight_id="FL001")
    result.must_not_call("cancel_booking")


@contract("flight_booking_with_chaos")
def test_handles_tool_failure() -> None:
    """Test that the agent handles tool failures gracefully."""
    agent = FlightBookingAgent()
    runner = ContractRunner()

    # Inject chaos - make search fail after first call
    chaos = ChaosInjector()
    chaos.fail_tool("search_flights", after_calls=1, error="RateLimitError")

    # This would be called with retry logic in a real agent
    result = runner.run(
        agent=agent.run,
        input="Book me a flight to NYC",
        chaos=chaos
    )

    # Agent should still try to complete
    result.must_call("search_flights")


@contract("flight_booking_snapshot")
def test_booking_matches_snapshot() -> None:
    """Test that booking flow matches expected trajectory."""
    agent = FlightBookingAgent()
    runner = ContractRunner()

    result = runner.run(
        agent=agent.run,
        input="Book me a flight to NYC"
    )

    # Snapshot the full trajectory
    result.snapshot("flight_booking_flow")

    # Also assert specific expectations
    result.tool_call_count("search_flights").at_most(2)
    result.assert_output_contains("Completed")
    result.assert_completed_in(5)


if __name__ == "__main__":
    # Run the tests
    test_books_correct_flight()
    print("✓ test_books_correct_flight passed")

    test_handles_tool_failure()
    print("✓ test_handles_tool_failure passed")

    test_booking_matches_snapshot()
    print("✓ test_booking_matches_snapshot passed")

    print("\nAll OpenAI example tests passed!")
