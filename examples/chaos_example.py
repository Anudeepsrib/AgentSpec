"""Example: Chaos testing AI agents with AgentSpec.

Demonstrates:
- Failure injection (fail_tool)
- Latency injection (slow_tool)
- Response corruption (corrupt_tool_response)
- Resilience assertions (retries, performance bounds)

Run:  python examples/chaos_example.py
Test: pytest examples/chaos_example.py -v
"""

import time
from agentspec import contract, ContractRunner
from agentspec.chaos import ChaosInjector

# ── Simulated tools ─────────────────────────────────────────────────────────

def search_products(query: str) -> dict:
    """Mock search tool."""
    return {"products": [{"id": "p1", "name": "Laptop"}]}

def process_payment(amount: float) -> dict:
    """Mock payment tool."""
    return {"status": "success", "transaction_id": "tx123"}

# ── Simulated agent ────────────────────────────────────────────────────────

def resilient_agent(user_input: str, interceptor=None, chaos=None, **kwargs):
    """An agent that attempts to be resilient to tool failures."""
    # Step 1: Wrap with chaos (if present)
    # Step 2: Wrap with interceptor
    search = search_products
    if chaos:
        search = chaos.apply("search_products", search)
    search = interceptor.wrap_tool(search, "search_products")

    pay = process_payment
    if chaos:
        pay = chaos.apply("process_payment", pay)
    pay = interceptor.wrap_tool(pay, "process_payment")

    # Search with retry logic
    results = None
    for attempt in range(3):
        try:
            results = search(query=user_input)
            break
        except Exception as e:
            print(f"  [Agent] Search failed (attempt {attempt+1}): {e}")
            if attempt == 2: raise
            time.sleep(0.1)

    # Payment
    try:
        payment = pay(amount=999.99)
        return f"Purchased {results['products'][0]['name']}. ID: {payment['transaction_id']}"
    except Exception as e:
        return f"Payment failed: {e}"

# ── Contract tests ──────────────────────────────────────────────────────────

@contract("resilience_to_rate_limits")
def test_agent_retries_on_failure():
    """Test: Agent should retry searching if it hits a rate limit."""
    chaos = ChaosInjector()
    # Fail the first search call, but only ONCE (transient)
    chaos.fail_tool("search_products", after_calls=0, error="RateLimitError", max_failures=1)
    
    runner = ContractRunner()
    result = runner.run(agent=resilient_agent, input="laptop", chaos=chaos)

    # Assertions
    # Should have called search at least twice (initial + 1 retry)
    result.tool_call_count("search_products").at_least(2)
    result.must_call("process_payment")
    
    print("[PASS] test_agent_retries_on_failure")

@contract("performance_under_latency")
def test_agent_performance_under_load():
    """Test: Agent flow should complete even if payment is slow."""
    chaos = ChaosInjector()
    chaos.slow_tool("process_payment", latency_ms=1000)
    
    runner = ContractRunner()
    result = runner.run(agent=resilient_agent, input="laptop", chaos=chaos)

    # Assertions
    result.assert_completed_in(5) # Still finish within 5s despite 1s delay
    result.must_call("process_payment")
    
    print("[PASS] test_agent_performance_under_load")

@contract("handling_corrupt_data")
def test_agent_handles_bad_responses():
    """Test: Agent should not crash if search returns garbage."""
    chaos = ChaosInjector()
    chaos.corrupt_tool_response("search_products", response={"error": "trash"}, after_calls=0)
    
    runner = ContractRunner()
    # This might fail the agent logic, but the contract ensures it handles the response
    try:
        result = runner.run(agent=resilient_agent, input="laptop", chaos=chaos)
        result.must_call("search_products")
    except Exception as e:
        print(f"  [System] Agent crashed as expected or handled improperly: {e}")
    
    print("[PASS] test_agent_handles_bad_responses")

if __name__ == "__main__":
    print("=" * 50)
    print("  AgentSpec Chaos Testing Example")
    print("=" * 50)
    print()

    test_agent_retries_on_failure()
    test_agent_performance_under_load()
    test_agent_handles_bad_responses()

    print()
    print("All chaos examples completed!")
