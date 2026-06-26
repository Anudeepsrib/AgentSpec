# Getting Started

## Installation

Install the PyPI distribution:

```bash
pip install agentspec-contracts
```

Import the library as `agentspec`:

```python
from agentspec import ContractRunner, contract
```

The `agentspec` and `agentcontract` PyPI names are owned by unrelated projects,
so AgentSpec's distribution is `agentspec-contracts`.

## Framework-Specific Extras

```bash
pip install "agentspec-contracts[openai]"      # OpenAI tool call interception
pip install "agentspec-contracts[anthropic]"   # Anthropic tool_use block interception
pip install "agentspec-contracts[langchain]"   # LangChain/LangGraph callbacks
pip install "agentspec-contracts[all]"         # All adapters
```

## Development Installation

```bash
git clone https://github.com/Anudeepsrib/AgentSpec.git
cd AgentSpec
pip install -e ".[dev,all,docs]"
```

## Core Concepts

A contract is a deterministic assertion about what an AI agent must do, must
not do, and in what order.

```python
from agentspec import ContractRunner, contract


@contract("booking_flow")
def test_correct_booking():
    runner = ContractRunner(persist=False)
    result = runner.run(agent=my_agent, input="Book a flight to NYC")

    result.must_call("search_flights")
    result.must_call("book_flight").after("search_flights")
    result.must_not_call("cancel_booking")
```

## Tool Call Interception

AgentSpec wraps your agent's tool calls so every invocation is recorded:

```python
def my_agent(user_input, interceptor=None, **kwargs):
    search = interceptor.wrap_tool(real_search_fn, "search_flights")
    book = interceptor.wrap_tool(real_book_fn, "book_flight")

    results = search(destination="NYC")
    booking = book(flight_id=results["flights"][0]["id"])
    return f"Booked: {booking['booking_id']}"
```

## Assertion API

| Method | Description |
| --- | --- |
| `must_call(tool)` | Assert a tool was called |
| `must_not_call(tool)` | Assert a tool was not called |
| `.after(other_tool)` | Assert ordering |
| `.before(other_tool)` | Assert ordering |
| `.immediately_after(other_tool)` | Assert adjacency |
| `.with_args(key=value)` | Assert exact argument match |
| `.with_args_containing(key=value)` | Assert argument subset |
| `.with_args_matching(key=regex)` | Assert regex match |
| `tool_call_count(tool)` | Get count assertion |
| `.exactly(n)` / `.at_least(n)` / `.at_most(n)` | Count constraints |
| `assert_completed_in(steps)` | Step budget |
| `snapshot(name)` | Save or compare trajectory snapshot |

## Running Tests

```bash
agentspec run tests/
agentspec run tests/ -v
agentspec run tests/ -k booking
agentspec ui
```

## Next Steps

- [Quick Start](quickstart.md)
- [LangChain and LangGraph Adapters](guides/langchain-langgraph.md)
- [Chaos Testing](guides/chaos-testing.md)
- [CI Integration](guides/ci-integration.md)
