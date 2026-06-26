# Quick Start

This guide creates one deterministic contract test with no API keys.

## 1. Install

```bash
pip install agentspec-contracts
```

Import as `agentspec`.

## 2. Write a Contract Test

Create `tests/test_booking.py`:

```python
from agentspec import ContractRunner, contract


def search_flights(destination: str) -> dict:
    return {"flights": [{"id": "FL001"}]}


def book_flight(flight_id: str) -> dict:
    return {"booking_id": f"BK-{flight_id}"}


@contract("flight_booking")
def test_flight_booking():
    runner = ContractRunner(persist=False)

    def mock_agent(input_text, interceptor=None, **_):
        search = interceptor.wrap_tool(search_flights, "search_flights")
        book = interceptor.wrap_tool(book_flight, "book_flight")
        search(destination="NYC")
        book(flight_id="FL001")
        return "booked"

    result = runner.run(agent=mock_agent, input="Book to NYC")

    result.must_call("search_flights")
    result.must_call("book_flight").after("search_flights")
    result.must_call("search_flights").with_args(destination="NYC")
    result.must_not_call("cancel")
    result.tool_call_count("search_flights").exactly(1)
```

## 3. Run

```bash
agentspec run tests/ -k booking --no-persist
pytest tests/test_booking.py -p agentspec.pytest_plugin -q
```

## 4. Snapshot Optional Behavior

```python
result.snapshot("booking_happy_path")
```

Update snapshots intentionally:

```bash
agentspec snapshot update tests/ --all
# or
AGENTSPEC_UPDATE_SNAPSHOTS=1 agentspec run tests/
```

## 5. Local UI

```bash
agentspec ui
```

Open `http://127.0.0.1:8080`.

## Sanitization and Privacy

By default, known sensitive keys are redacted in traces, logs, and snapshots.

```python
runner = ContractRunner(sanitize_keys=["custom_secret"])
```

See [Security](security.md).
