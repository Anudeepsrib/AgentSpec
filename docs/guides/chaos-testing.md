# Chaos Testing

Production environments are messy. APIs rate-limit, databases go down, third-party services timeout. AgentSpec's chaos injection lets you test how your agent handles failures **before** they happen in production.

## Quick Example

```python
from agentcontract import ContractRunner
from agentcontract.chaos import ChaosInjector

chaos = ChaosInjector()
chaos.fail_tool("search_flights", after_calls=1, error="RateLimitError")
chaos.slow_tool("payment_gateway", latency_ms=5000)

runner = ContractRunner()
result = runner.run(agent=my_agent, input="Book a flight", chaos=chaos)

# Agent should retry after rate limit
result.must_call("search_flights").at_least(2)
```

## Chaos Types

### Tool Failures

Simulate a tool failing after N successful calls:

```python
chaos = ChaosInjector()

# Fail after 1 successful call
chaos.fail_tool("search_flights", after_calls=1, error="RateLimitError")

# Fail immediately (after_calls=0)
chaos.fail_tool("payment_gateway", after_calls=0, error="ConnectionError")

# Custom error messages
chaos.fail_tool("database", error="TimeoutError", message="Connection pool exhausted")
```

**Supported error types:**
- `RateLimitError` -- Simulated API rate limiting
- `TimeoutError` -- Network/API timeout
- `ConnectionError` -- Network connectivity failure
- `ValueError` -- Invalid response data
- `RuntimeError` -- Generic runtime failure (default)

### Latency Injection

Add artificial latency to test timeout handling:

```python
chaos = ChaosInjector()
chaos.slow_tool("external_api", latency_ms=3000)  # 3 second delay

result = runner.run(agent=my_agent, input="query", chaos=chaos)
result.assert_completed_in(10)  # Should still complete within 10s
```

### Response Corruption

Return corrupted data to test input validation:

```python
chaos = ChaosInjector()
chaos.corrupt_tool_response(
    "search_flights",
    response={"error": "malformed response", "flights": None},
    after_calls=0,
)

result = runner.run(agent=my_agent, input="search", chaos=chaos)
# Agent should handle corrupt data gracefully
```

### Random Failures

Apply stochastic failures across all tools:

```python
chaos = ChaosInjector(seed=42)  # Deterministic randomness
chaos.random_failures(probability=0.1)  # 10% failure rate

result = runner.run(agent=my_agent, input="complex workflow", chaos=chaos)
```

## Chaining Chaos Rules

The `ChaosInjector` supports method chaining:

```python
chaos = (
    ChaosInjector(seed=42)
    .fail_tool("auth", after_calls=2, error="TimeoutError")
    .slow_tool("search", latency_ms=1000)
    .corrupt_tool_response("validate", response={"valid": False})
    .random_failures(probability=0.05)
)
```

## Chaos Summary

After running, inspect what chaos was applied:

```python
result = runner.run(agent=my_agent, input="test", chaos=chaos)
summary = chaos.get_summary()
# {'search_flights': {'calls': 3, 'failures': 2, 'corruptions': 0}}
```

## Best Practices

1. **Test retry logic** -- Fail tools after N calls and assert the agent retries
2. **Test graceful degradation** -- Corrupt responses and verify the agent doesn't crash
3. **Test timeout handling** -- Add latency and verify performance bounds still hold
4. **Use deterministic seeds** -- `ChaosInjector(seed=42)` ensures reproducible chaos
5. **Combine with assertions** -- Chaos without assertions is just breaking things
