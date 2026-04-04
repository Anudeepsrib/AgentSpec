# Getting Started with agentcontract

## Installation

```bash
pip install agentcontract
```

For specific framework support:

```bash
pip install agentcontract[openai]      # OpenAI support
pip install agentcontract[anthropic]   # Anthropic support
pip install agentcontract[langchain]   # LangChain support
pip install agentcontract[all]         # All adapters
```

## Quick Start

### 1. Write Your First Contract Test

```python
from agentcontract import contract, ContractRunner

@contract("my_first_contract")
def test_agent_behavior():
    runner = ContractRunner()
    
    # Run your agent
    result = runner.run(
        agent=my_agent,
        input="Book a flight to NYC"
    )
    
    # Assert on tool calls
    result.must_call("search_flights")
    result.must_call("book_flight").after("search_flights")
    result.must_not_call("cancel_booking")
```

### 2. Run Your Tests

```bash
# Run all contract tests
agentcontract run

# Run specific test file
agentcontract run tests/test_contracts.py

# Update snapshots
agentcontract snapshot update
```

### 3. Set Up Snapshots

Snapshots record the expected trajectory of tool calls:

```python
def test_with_snapshot():
    runner = ContractRunner()
    result = runner.run(agent=my_agent, input="Book flight")
    
    # Compare against golden snapshot
    result.snapshot("flight_booking_flow")
```

First run creates the snapshot, subsequent runs verify against it.

## Key Concepts

### Contracts

A **Contract** is a deterministic assertion about agent behavior:
- Which tools are called
- In what order
- With what arguments
- How many times

Unlike LLM-as-judge scoring, contracts are pass/fail with clear error messages.

### Assertions

**Call Assertions:**
- `result.must_call("tool_name")` - Tool must be called
- `result.must_not_call("tool_name")` - Tool must not be called

**Order Assertions:**
- `result.must_call("a").before("b")` - Call before another
- `result.must_call("a").after("b")` - Call after another
- `result.must_call("a").immediately_after("b")` - Adjacent calls

**Argument Assertions:**
- `result.must_call("tool").with_args(**kwargs)` - Exact match
- `result.must_call("tool").with_args_containing(**kwargs)` - Subset match
- `result.must_call("tool").with_args_matching(**patterns)` - Regex match

**Count Assertions:**
- `result.tool_call_count("tool").exactly(n)`
- `result.tool_call_count("tool").at_least(n)`
- `result.tool_call_count("tool").at_most(n)`

## Framework Integration

### OpenAI

```python
from agentcontract import ContractRunner

runner = ContractRunner(adapter="openai")
result = runner.run(agent=openai_client, input="Book flight")
result.must_call("search_flights")
```

### Anthropic

```python
runner = ContractRunner(adapter="anthropic")
result = runner.run(agent=anthropic_client, input="Research topic")
```

### LangChain

```python
runner = ContractRunner(adapter="langchain")
result = runner.run(agent=langchain_agent, input="Process request")
```

### Custom Agents

```python
def my_agent(input_text, interceptor=None):
    # Your agent logic
    if interceptor:
        interceptor.record("my_tool", {"arg": "value"}, result)
    return result

runner = ContractRunner()
result = runner.run(agent=my_agent, input="test")
```

## Chaos Testing

Test agent resilience with injected failures:

```python
from agentcontract.chaos import ChaosInjector

chaos = ChaosInjector()
chaos.fail_tool("api", after_calls=1, error="RateLimitError")
chaos.slow_tool("db", latency_ms=3000)

result = runner.run(agent=my_agent, input="test", chaos=chaos)
result.must_call("api").at_least(2)  # Expect retry
```

## CI Integration

Add to your GitHub Actions workflow:

```yaml
- name: Run agent contracts
  run: |
    pip install agentcontract
    agentcontract run tests/
```

## Next Steps

- See `examples/` for complete examples
- Read the API reference
- Join the community discussions
