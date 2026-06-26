<div align="center">

<img src="docs/logo.png" width="120" alt="AgentSpec logo" />

# AgentSpec

[![CI](https://github.com/Anudeepsrib/AgentSpec/actions/workflows/ci.yml/badge.svg)](https://github.com/Anudeepsrib/AgentSpec/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/Anudeepsrib/AgentSpec/branch/main/graph/badge.svg)](https://codecov.io/gh/Anudeepsrib/AgentSpec)
[![PyPI version](https://img.shields.io/pypi/v/agentspec-contracts.svg)](https://pypi.org/project/agentspec-contracts/)
[![Python versions](https://img.shields.io/pypi/pyversions/agentspec-contracts.svg)](https://pypi.org/project/agentspec-contracts/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

Deterministic contract testing for AI agent tool behavior.

[Quickstart](#quickstart) | [Examples](#examples) | [Roadmap](ROADMAP.md) | [Contributing](CONTRIBUTING.md)

</div>

AgentSpec turns agent behavior into regular Python tests. Instead of asking an
LLM judge whether an answer "seems good", you assert that the agent called the
right tools, in the right order, with the right arguments, and within the
expected step budget.

## Package Naming

The public Python import and primary CLI are `agentspec`:

```python
from agentspec import ContractRunner, contract
```

The PyPI distribution name is `agentspec-contracts`:

```bash
pip install agentspec-contracts
```

The plain `agentspec` name is already used by an unrelated PyPI project, so
this repository uses a distinct distribution name while keeping the clean
`agentspec` import.

## Project Status

AgentSpec is beta software. The core assertion API is useful today, but adapter
coverage and CLI ergonomics are still stabilizing. See [ROADMAP.md](ROADMAP.md)
for realistic beta milestones.

## What AgentSpec Tests

| Contract type | Example |
| --- | --- |
| Required calls | `result.must_call("verify_payment")` |
| Forbidden calls | `result.must_not_call("cancel_reservation")` |
| Ordering | `result.must_call("book").after("search")` |
| Arguments | `result.must_call("search").with_args(destination="NYC")` |
| Counts | `result.tool_call_count("api_call").at_most(3)` |
| Snapshots | `result.snapshot("booking_happy_path")` |

AgentSpec does not score writing quality, hallucination risk, safety policy
compliance, model robustness, or the correctness of external APIs. Use it with
evals, observability, review, and integration tests.

## Quickstart

Install the package and optional adapters:

```bash
pip install agentspec-contracts
pip install "agentspec-contracts[langchain]"  # LangChain and LangGraph callbacks
pip install "agentspec-contracts[all]"        # OpenAI, Anthropic, LangChain
```

Create `tests/test_booking_contract.py`:

```python
from agentspec import ContractRunner, contract


def search_flights(destination: str) -> dict:
    return {"flights": [{"id": "FL-1", "price": 240}]}


def reserve_flight(flight_id: str) -> dict:
    return {"reservation_id": f"RSV-{flight_id}"}


def booking_agent(user_input: str, interceptor=None, **_):
    search = interceptor.wrap_tool(search_flights, "search_flights")
    reserve = interceptor.wrap_tool(reserve_flight, "reserve_flight")

    results = search(destination="NYC")
    reserve(flight_id=results["flights"][0]["id"])
    return "reserved"


@contract("booking_happy_path")
def test_booking_happy_path():
    runner = ContractRunner(persist=False)
    result = runner.run(agent=booking_agent, input="Book a flight to NYC")

    result.must_call("search_flights").with_args(destination="NYC")
    result.must_call("reserve_flight").after("search_flights")
    result.must_not_call("cancel_reservation")
    result.tool_call_count("reserve_flight").exactly(1)
```

Run it:

```bash
agentspec run tests/ --no-persist
# or use pytest directly
pytest tests/test_booking_contract.py -p agentspec.pytest_plugin -q
```

Inspect local traces:

```bash
agentspec ui
```

Trace and snapshot files are stored under `.agentspec/` by default. Do not
commit them unless you have reviewed the contents for sensitive data.

## Examples

Runnable examples live in [examples/](examples/):

| Example | Purpose |
| --- | --- |
| [quickstart.py](examples/quickstart.py) | Zero-key booking contract walkthrough |
| [test_contract_demos.py](examples/test_contract_demos.py) | Passing and intentionally failing contract demos |
| [langchain_adapter_example.py](examples/langchain_adapter_example.py) | LangChain-style `.invoke()` callback integration |
| [langgraph_adapter_example.py](examples/langgraph_adapter_example.py) | LangGraph-style compiled graph callback integration |
| [chaos_example.py](examples/chaos_example.py) | Failure and latency injection |
| [multi_agent_example.py](examples/multi_agent_example.py) | Per-agent trace isolation |

Run the zero-key examples:

```bash
python examples/quickstart.py
pytest examples/test_contract_demos.py -q -rx
python examples/langchain_adapter_example.py
python examples/langgraph_adapter_example.py
```

## LangChain and LangGraph

AgentSpec integrates with LangChain and LangGraph through callback handlers.
Use the adapter when your runnable or compiled graph exposes `.invoke()` or
`.ainvoke()`:

```python
from agentspec import ContractRunner

runner = ContractRunner(adapter="langchain", persist=False)
result = runner.run(agent=compiled_graph, input={"messages": ["book NYC"]})

result.must_call("search_flights")
result.must_call("reserve_flight").after("search_flights")
```

For lower-level integration, use `AgentSpecCallbackHandler` directly and pass it
through a LangChain/LangGraph config:

```python
from agentspec.adapters.langchain import AgentSpecCallbackHandler
from agentspec.interceptor import TraceInterceptor

interceptor = TraceInterceptor()
handler = AgentSpecCallbackHandler(interceptor)
graph.invoke({"messages": ["book NYC"]}, config={"callbacks": [handler]})
```

## CI

The repository CI runs linting, tests, coverage, packaging, dashboard build, and
docs build. Downstream projects can run contracts with the CLI:

```yaml
- name: Install AgentSpec
  run: pip install "agentspec-contracts[langchain]"

- name: Run agent contracts
  run: agentspec run tests/ --no-persist -o agentspec-results.jsonl
```

## Versioning

AgentSpec follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html):

- Patch releases fix bugs without changing public behavior.
- Minor releases add backwards-compatible features.
- Major releases can change public APIs after a documented migration path.

See [CHANGELOG.md](CHANGELOG.md) for release notes.

## License

AgentSpec is distributed under the Apache License 2.0. See [LICENSE](LICENSE).
