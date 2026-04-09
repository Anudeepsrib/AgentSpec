"""Quickstart: Your first AgentSpec contract test.

This example works with zero API keys — no OpenAI, Anthropic, or any
external service required. Run it directly:

    python examples/quickstart.py

Or with pytest:

    pytest examples/quickstart.py -v
"""

from agentcontract import contract, ContractRunner, ContractSuite


# ── Step 1: Define your tools ───────────────────────────────────────────────
# These are the tools your agent calls. In production, they'd hit real APIs.

def search_flights(destination: str, date: str = "2024-06-01") -> dict:
    """Search for flights to a destination."""
    return {
        "flights": [
            {"id": "FL001", "price": 299, "airline": "JetBlue"},
            {"id": "FL002", "price": 350, "airline": "Delta"},
        ]
    }


def book_flight(flight_id: str, passenger: str = "Test User") -> dict:
    """Book a specific flight."""
    return {"booking_id": f"BK-{flight_id}", "status": "confirmed"}


def cancel_booking(booking_id: str) -> dict:
    """Cancel a booking."""
    return {"status": "cancelled"}


# ── Step 2: Define your agent ──────────────────────────────────────────────
# A mock agent that simulates tool-calling behavior.

def booking_agent(user_input: str, interceptor=None, **kwargs):
    """A simple agent that searches and books flights.

    The `interceptor` is automatically injected by ContractRunner.
    Use `interceptor.wrap_tool()` to make tool calls visible to AgentSpec.
    """
    # Wrap tools for automatic interception
    search = interceptor.wrap_tool(search_flights, "search_flights")
    book = interceptor.wrap_tool(book_flight, "book_flight")

    # Agent logic: search then book the cheapest
    results = search(destination="NYC", date="2024-06-15")
    cheapest = min(results["flights"], key=lambda f: f["price"])
    booking = book(flight_id=cheapest["id"], passenger="Alice")

    return f"Booked flight {cheapest['id']} for $cheapest['price']: {booking['booking_id']}"


# ── Step 3: Write contract tests ───────────────────────────────────────────

@contract("booking_happy_path")
def test_books_correct_flight():
    """Test: Agent searches before booking and picks the right flight."""
    runner = ContractRunner(persist=False)
    result = runner.run(agent=booking_agent, input="Book me a flight to NYC")

    # These are DETERMINISTIC — no flaky LLM-as-judge
    result.must_call("search_flights")
    result.must_call("book_flight").after("search_flights")
    result.must_call("search_flights").with_args(destination="NYC")
    result.must_not_call("cancel_booking")
    result.tool_call_count("search_flights").exactly(1)
    result.tool_call_count("book_flight").exactly(1)


@contract("booking_performance")
def test_booking_completes_fast():
    """Test: The full booking flow completes within 5 seconds."""
    runner = ContractRunner(persist=False)
    result = runner.run(agent=booking_agent, input="Book me a flight to NYC")

    result.assert_completed_in(5)  # seconds


# ── Step 4: Use ContractSuites for grouped tests ──────────────────────────

suite = ContractSuite(
    name="booking_suite",
    persist=False,
    sanitize_keys=["password"],  # Auto-redact sensitive fields
)


@suite.contract("search_only")
def test_search_only(runner):
    """Test: A search-only flow doesn't trigger booking."""
    def search_only_agent(user_input, interceptor=None, **kwargs):
        search = interceptor.wrap_tool(search_flights, "search_flights")
        search(destination="LAX")
        return "Found 2 flights"

    result = runner.run(agent=search_only_agent, input="Find flights to LA")
    result.must_call("search_flights")
    result.must_not_call("book_flight")


@suite.contract("ordered_flow")
def test_ordered_flow(runner):
    """Test: Tools are called in the correct order."""
    result = runner.run(agent=booking_agent, input="Book a flight to NYC")
    result.must_call("search_flights").before("book_flight")


# ── Run everything ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  AgentSpec Quickstart -- Zero API Keys Required")
    print("=" * 60)
    print()

    # Run individual contracts
    test_books_correct_flight()
    print("[PASS] test_books_correct_flight passed")

    test_booking_completes_fast()
    print("[PASS] test_booking_completes_fast passed")

    # Run suite
    print()
    results = suite.run_all()
    for r in results:
        status = "[PASS]" if r["passed"] else "[FAIL]"
        print(f"{status} {r['name']}")

    print()
    total = len(results) + 2
    print(f"All {total} contracts passed!")
    print()
    print("Next steps:")
    print("  - Run with pytest:       pytest examples/quickstart.py -v")
    print("  - Save snapshots:        result.snapshot('my_flow')")
    print("  - Visualize traces:      agentcontract ui")
    print("  - Add chaos:             from agentcontract.chaos import ChaosInjector")
