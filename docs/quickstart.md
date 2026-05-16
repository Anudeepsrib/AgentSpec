# Quick Start

This guide walks you through writing and running your first agent contract test.

## 1. Install

```bash
pip install agentcontract
# or for dev: pip install -e ".[dev,all]"
```

Import as `agentspec` (PyPI distribution name `agentcontract` is for backward compat).

## 2. Write a Contract Test

Create `tests/test_booking.py`:

```python
from agentspec import contract, ContractRunner

def search_flights(destination: str) -> dict:
    return {"flights": [{"id": "FL001"}]}

def book_flight(flight_id: str) -> dict:
    return {"booking_id": f"BK-{flight_id}"}

@contract("flight_booking")
def test_flight_booking():
    runner = ContractRunner(persist=False)  # disable for CI if sensitive

    def mock_agent(input_text, interceptor=None, **_):
        # Wrap tools so calls are recorded automatically
        s = interceptor.wrap_tool(search_flights, "search_flights")
        b = interceptor.wrap_tool(book_flight, "book_flight")
        s(destination="NYC")
        b(flight_id="FL001")
        return "booked"

    result = runner.run(agent=mock_agent, input="Book to NYC")

    # Deterministic assertions
    result.must_call("search_flights")
    result.must_call("book_flight").after("search_flights")
    result.must_call("search_flights").with_args(destination="NYC")
    result.must_not_call("cancel")
    result.tool_call_count("search_flights").exactly(1)
    result.snapshot("booking_happy_path")  # optional golden snapshot
```

## 3. Run

```bash
agentspec run tests/ -k booking --no-persist
# or
pytest tests/test_booking.py -p agentspec.pytest_plugin -q
```

## 4. Snapshots & Update

```bash
agentspec snapshot list
agentspec snapshot update tests/ --all   # or set AGENTCONTRACT_UPDATE_SNAPSHOTS=1
```

## 5. Local UI

```bash
agentspec ui
# open http://127.0.0.1:8080
```

## Sanitization & Privacy

By default, known sensitive keys are redacted in traces, logs, and snapshots.

```python
runner = ContractRunner(sanitize_keys=["custom_secret"])
```

See [Security](security.md) and [Sanitizing Traces](../README.md) for details.

## Next
- [Writing Contracts](guides/writing-contracts.md)
- [Chaos Testing](guides/chaos-testing.md)
- [Snapshots](guides/snapshots.md)
- [CI Integration](guides/ci-integration.md)