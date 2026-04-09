# Getting Started

## Installation

Install AgentSpec via pip:

```bash
pip install agentcontract
```

*Note: The PyPI package name is `agentcontract` for backward compatibility. Import it as `agentspec` in your code.*

### Framework-Specific Extras

```bash
pip install agentcontract[openai]      # OpenAI tool call interception
pip install agentcontract[anthropic]   # Anthropic tool_use block interception
pip install agentcontract[langchain]   # LangChain/LangGraph callback integration
pip install agentcontract[all]         # All adapters
```

### Development Installation

```bash
git clone https://github.com/Anudeepsrib/AgentSpec.git
cd AgentSpec
pip install -e ".[dev,all]"
```

## Core Concepts

### What is a Contract?

A **contract** is a deterministic assertion about what an AI agent _must do_, _must not do_, and _in what order_. Unlike LLM-as-judge evaluations that score output quality, contracts enforce binary pass/fail behavioral requirements.

```python
from agentspec import contract, ContractRunner

@contract("booking_flow")
def test_correct_booking():
    runner = ContractRunner()
    result = runner.run(agent=my_agent, input="Book a flight to NYC")

    result.must_call("search_flights")
    result.must_call("book_flight").after("search_flights")
    result.must_not_call("cancel_booking")
```

### How Tool Call Interception Works

AgentSpec wraps your agent's tool calls so every invocation is recorded:

```python
def my_agent(user_input, interceptor=None, **kwargs):
    search = interceptor.wrap_tool(real_search_fn, "search_flights")
    book = interceptor.wrap_tool(real_book_fn, "book_flight")

    results = search(destination="NYC")
    booking = book(flight_id=results[0]["id"])
    return f"Booked: {booking['id']}"
```

### The Assertion API

| Method | Description |
|---|---|
| `must_call(tool)` | Assert tool was called |
| `must_not_call(tool)` | Assert tool was NOT called |
| `.after(other_tool)` | Assert ordering |
| `.before(other_tool)` | Assert ordering |
| `.immediately_after(other_tool)` | Assert adjacency |
| `.with_args(key=val)` | Assert exact argument match |
| `.with_args_containing(key=val)` | Assert argument subset |
| `.with_args_matching(key=regex)` | Assert regex match |
| `tool_call_count(tool)` | Get count assertion |
| `.exactly(n)` / `.at_least(n)` / `.at_most(n)` | Count constraints |
| `assert_completed_in(seconds)` | Performance bound |
| `snapshot(name)` | Save/compare trajectory snapshot |

## Running Tests

```bash
agentspec run tests/         # Run all contract tests
agentspec run tests/ -v      # Verbose output
agentspec run tests/ -k booking  # Filter by keyword
agentspec ui                 # Launch trace visualizer
```

## Next Steps

- [Chaos Testing](guides/chaos-testing.md) -- Test agent resilience
- [Multi-Agent Testing](guides/multi-agent.md) -- Test agent swarms
- [CI Integration](guides/ci-integration.md) -- Add contracts to your pipeline
