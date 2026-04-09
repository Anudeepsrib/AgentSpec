# 🚀 Getting Started with AgentSpec

**The first agent testing framework built around strict deterministic contracts.**

## 🛠 Installation

```bash
pip install agentcontract
```

For specific framework adapter support:

```bash
pip install agentcontract[openai]      # OpenAI support
pip install agentcontract[anthropic]   # Anthropic support
pip install agentcontract[langchain]   # LangChain support
pip install agentcontract[all]         # All adapters
```

## 🏗 Quick Start

### 1. Write Your First Contract Test

AgentSpec introduces strict, binary validations over probabilistic vibes. You can use standard synchronous agents, or explicitly execute asynchronous implementations.

```python
import pytest
from agentcontract import contract, ContractRunner

@pytest.mark.asyncio
@contract("my_first_async_contract")
async def test_agent_behavior():
    runner = ContractRunner()
    
    # Run your agent asynchronously (also supports .run() for sync)
    result = await runner.arun(
        agent=my_async_agent,
        input="Book a flight to NYC"
    )
    
    # Assert on exact tool triggers and order
    result.must_call("search_flights")
    result.must_call("book_flight").after("search_flights")
    result.must_not_call("cancel_booking")
```

### 2. Run Your Tests

Integrates beautifully natively into standard pytest execution protocols.

```bash
# Run all contract tests via CLI
agentcontract run

# Run specific test file
agentcontract run tests/test_contracts.py

# Update deterministic snapshots
agentcontract snapshot update
```

### 3. Set Up Trajectory Snapshots

Snapshots record the exact JSON expected trajectory of tool calls preventing regression:

```python
def test_with_snapshot():
    runner = ContractRunner()
    result = runner.run(agent=my_agent, input="Book flight")
    
    # Locks the trajectory against a golden snapshot file
    result.snapshot("flight_booking_flow")
```

First run automatically creates the snapshot, and all subsequent runs verify against it with comprehensive code diffs on failure.

---

## 🔐 Key Concepts

### Contracts
A **Contract** is a deterministic assertion about agent behavior:
- Which tools are called
- In what order
- With what arguments
- How many times
- How quickly they execute

**Unlike LLM-as-judge scoring, contracts are strictly pass/fail.**

### Assertions API

#### Call Assertions
- `result.must_call("tool_name")` - Tool must be called
- `result.must_not_call("tool_name")` - Tool must not be called

#### Multi-Agent Tracking
AgentSpec uniquely tracks isolated calls within multi-agent swarms.
- `result.must_call("search", agent_id="research_agent")`

#### Order Constraints
- `result.must_call("a").before("b")`
- `result.must_call("a").after("b")`
- `result.must_call("a").immediately_after("b")`

#### Parameter Validations
- `result.must_call("tool").with_args(**kwargs)` - Exact dict match
- `result.must_call("tool").with_args_containing(**kwargs)` - Subset parameter match
- `result.must_call("tool").with_args_matching(**patterns)` - Regex parameter match

#### Telemetry Performance Metrics
- `result.assert_total_duration_under(ms=3000)` - Full execution bounded
- `result.must_call("tool").within_ms(ms=100)` - Singular tool logic fast response verification

#### Count Verifications
- `result.tool_call_count("tool").exactly(n)`
- `result.tool_call_count("tool").at_least(n)`
- `result.tool_call_count("tool").at_most(n)`

---

## 🔌 Framework Integration

AgentSpec is designed to be fully agnostic. We supply adapters for the primary ecosystems automatically bridging function tracking.

### OpenAI
```python
from agentcontract import ContractRunner

runner = ContractRunner(adapter="openai")
result = await runner.arun(agent=openai_async_client, input="Book flight")
result.must_call("search_flights")
```

### Anthropic
```python
runner = ContractRunner(adapter="anthropic")
result = runner.run(agent=anthropic_client, input="Research topic")
```

### Custom Agents
If you prefer rolling your own solution, explicitly utilize the `interceptor`.

```python
def my_agent(input_text, interceptor=None):
    if interceptor:
        wrapped_tool = interceptor.wrap_tool(my_tool, "my_tool")
        wrapped_tool(arg="value")
    return "Done"

runner = ContractRunner()
result = runner.run(agent=my_agent, input="test")
```

---

## 🌪 Chaos Testing
Don't wait for AWS us-east-1 to crash to see if your agent has retry loops.

```python
from agentcontract.chaos import ChaosInjector

chaos = ChaosInjector()

# Enforce explicit stochasticity 
chaos.random_failures(probability=0.1)

# Targeted component failure
chaos.fail_tool("api", after_calls=1, error="RateLimitError")
chaos.slow_tool("db", latency_ms=3000)

result = await runner.arun(agent=my_agent, input="test", chaos=chaos)
result.must_call("api").at_least(2)  # Proof the LLM retried successfully
```

---

## ⚙️ CI Integration
Add directly to your GitHub Actions pipeline for instant telemetry protection.

```yaml
- name: Run agent contracts
  run: |
    pip install agentcontract
    agentcontract run tests/
```

### Next Steps 🚀
- Read the API reference.
- Integrate Contract tests natively into your codebase.
- Join the community discussions!
