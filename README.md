# agentcontract

<div align="center">

```
    _                                _             _   _             
   / \   ___ _ __ ___  ___ _ __ ___ | | ___   __ _| |_(_) ___  _ __  
  / _ \ / __| '_ ` _ \/ __| '__/ _ \| |/ _ \ / _` | __| |/ _ \| '_ \ 
 / ___ \\__ \ | | | | | (__| | | (_) | | (_) | (_| | |_| | (_) | | | |
/_/   \_\___/_| |_| |_|\___|_|  \___/|_|\___/ \__,_|\__|_|\___/|_| |_|
```

**The first agent testing framework built around deterministic contracts, not vibes.**

[![PyPI version](https://badge.fury.io/py/agentcontract.svg)](https://pypi.org/project/agentcontract/)
[![Python versions](https://img.shields.io/pypi/pyversions/agentcontract.svg)](https://pypi.org/project/agentcontract/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/agentcontract/agentcontract/workflows/CI/badge.svg)](https://github.com/agentcontract/agentcontract/actions)
[![Coverage](https://codecov.io/gh/agentcontract/agentcontract/branch/main/graph/badge.svg)](https://codecov.io/gh/agentcontract/agentcontract)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

</div>

---

## Overview

**agentcontract** is the first deterministic testing framework for AI agents. Unlike traditional agent evaluation tools that score LLM output quality using probabilistic metrics, agentcontract provides **deterministic contracts** that assert exactly what your agent MUST do, MUST NOT do, and MUST do in what order.

Think of it as:
- **Pact** for agent/API contracts — but for tool calls
- **Jest snapshots** — but for agent trajectories  
- **Chaos engineering** — but for agent resilience testing

### The Problem

You shipped an agent to production without tests. Now it's 3 AM and your PagerDuty is screaming. The booking agent is calling `cancel_reservation` before `verify_payment`. Customers are losing reservations. The LLM "vibe check" passed in CI but real users hit edge cases your evals never covered.

**Stop scoring agent output quality.** Start enforcing agent behavior.

---

## Quick Start

### Installation

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

### Your First Contract Test

```python
from agentcontract import contract, ContractRunner

@contract("flight_booking")
def test_books_correct_flight():
    runner = ContractRunner(adapter="openai")
    result = runner.run(
        agent=my_booking_agent,
        input="Book me a flight to NYC next Tuesday"
    )

    result.must_call("search_flights")
    result.must_call("book_flight").after("search_flights")
    result.must_call("book_flight").with_args_containing(destination="NYC")
    result.must_not_call("cancel_booking")
    result.snapshot()  # Record golden trajectory
```

Run your tests:

```bash
agentcontract run tests/
```

Output:

```
=================== agentcontract summary ===================
PASSED  test_books_correct_flight       4 tool calls · 2 assertions
PASSED  test_no_double_booking          2 tool calls · 3 assertions
FAILED  test_handles_rate_limit         SnapshotMismatch: search_flights called 3x (expected 2x)

3 contracts run · 2 passed · 1 failed
```

---

## Core Concepts

### Contracts vs Traditional Testing

| Traditional Agent Evals | agentcontract |
|---|---|
| *"Is this output good?"* (Subjective) | *"Did the agent call `verify_identity` before `transfer_funds`?"* (Deterministic) |
| LLM-as-judge scoring | Binary pass/fail assertions |
| Probabilistic, flaky | Fast, reliable, cheap |
| Expensive API calls | Local execution |

### The Contract Philosophy

```python
# This is a Contract. It passes or fails. No 0.7 "score".
result.must_call("verify_identity").before("transfer_funds")
result.must_call("transfer_funds").with_args(amount__lte=10000)
result.must_not_call("admin_override")
```

---

## API Reference

### Call Assertions

```python
# Tool must be called at least once
result.must_call("search_flights")

# Tool must NOT be called
result.must_not_call("cancel_booking")

# Exactly N calls
result.must_call("retry_payment").exactly(3)

# Count assertions
result.tool_call_count("api_call").at_most(5)
```

### Order Assertions

```python
# Sequential ordering
result.must_call("search_flights")
result.must_call("select_flight").after("search_flights")
result.must_call("book_flight").immediately_after("select_flight")

# Chain them
result.must_call("auth").before("query").before("update")
```

### Argument Assertions

```python
# Exact argument match
result.must_call("book_flight").with_args(
    destination="NYC",
    class="business"
)

# Subset match (arguments contain these values)
result.must_call("search").with_args_containing(
    query="flights to New York"
)

# Regex pattern matching on string args
result.must_call("validate_email").with_args_matching(
    email=r"^[\w.-]+@[\w.-]+\.\w+$"
)
```

### Output & Trajectory Assertions

```python
# Output content
result.assert_output_contains("Booking confirmed")
result.assert_output_matches(r"Confirmation: \w{8}")

# Step limits
result.assert_completed_in(max_steps=10)

# Snapshot the full trajectory
result.snapshot("booking_flow")
```

---

## Framework Integration

agentcontract works with **any** agent framework through thin adapters:

### OpenAI

```python
from agentcontract import ContractRunner

runner = ContractRunner(adapter="openai")
result = runner.run(agent=openai_client, input="Book flight")

result.must_call("search_flights")
result.must_call("book_flight").after("search_flights")
```

### Anthropic

```python
runner = ContractRunner(adapter="anthropic")
result = runner.run(agent=anthropic_client, input="Research quantum computing")

result.must_call("web_search")
result.must_call("synthesize").after("web_search")
```

### LangChain

```python
runner = ContractRunner(adapter="langchain")
result = runner.run(agent=langchain_agent, input="Process support ticket")

result.must_call("lookup_customer")
result.must_call("process_refund").after("lookup_customer")
```

### Custom Agents

```python
def my_agent(input_text, interceptor=None):
    # Your agent logic
    result = search_flights(input_text)
    
    # Record via interceptor
    if interceptor:
        interceptor.record("search_flights", {"query": input_text}, result)
    
    return result

runner = ContractRunner()
result = runner.run(agent=my_agent, input="test")
result.must_call("search_flights")
```

---

## Chaos Testing

Production is messy. Tools timeout, APIs rate-limit, databases go down. Test agent resilience:

```python
from agentcontract.chaos import ChaosInjector

chaos = ChaosInjector()
chaos.fail_tool("search_flights", after_calls=1, error="RateLimitError")
chaos.slow_tool("payment_gateway", latency_ms=5000)
chaos.corrupt_tool_response("inventory_check", response={"stock": -1})

result = runner.run(agent=my_agent, input="Book flight", chaos=chaos)

# Assert the agent still completes (with retries)
result.must_call("search_flights").at_least(2)  # Retried after failure
result.must_call("payment_gateway")  # Still attempted despite latency
```

---

## Snapshot Testing

Record a "golden" trajectory once. Fail if future runs deviate.

### What gets recorded:

```json
{
  "tool_calls": [
    {"name": "search_flights", "args": {"dest": "NYC"}, "step": 0},
    {"name": "select_flight", "args": {"id": "FL001"}, "step": 1},
    {"name": "book_flight", "args": {"id": "FL001", "passenger": "John"}, "step": 2}
  ],
  "start_time": 1712345678.0,
  "end_time": 1712345680.0
}
```

### First run (creates snapshot):

```python
result.snapshot("booking_flow")  # Saved to .agentcontract/snapshots/
```

### Subsequent runs (compare):

```python
result.snapshot("booking_flow")  # Raises SnapshotMismatch if different
```

### Diff output on failure:

```
Snapshot Mismatch: booking_flow

Detailed Diff
────────────────────────────────
~ Call 1: book_flight
    args.passenger: "John" -> "Jane"
  Call 2: send_email (unchanged)
+ Call 3: notify_admin (NEW)

Expected 3 calls, got 4
```

### Update snapshots:

```bash
agentcontract snapshot update  # Update all after intentional changes
```

---

## CLI Commands

```bash
# Run all contract tests
agentcontract run

# Run specific test file
agentcontract run tests/test_flights.py

# Update all snapshots
agentcontract snapshot update

# List snapshots
agentcontract snapshot list

# Clean all snapshots
agentcontract snapshot clean

# Initialize new project
agentcontract init
```

---

## CI Integration

### GitHub Actions

```yaml
name: Agent Contracts

on: [push, pull_request]

jobs:
  contracts:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']
    
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install agentcontract[all]
      
      - name: Run contracts
        run: agentcontract run tests/
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Local Development

```bash
# Install in development mode
pip install -e ".[dev,all]"

# Run tests with coverage
pytest tests/ --cov=agentcontract

# Lint code
ruff check .
black --check .
mypy agentcontract/
```

---

## Comparison Table

| Feature | agentcontract | DeepEval | LangSmith | Scenario |
|---|---|---|---|---|
| Deterministic assertions | ✅ | ❌ | ❌ | ❌ |
| Framework agnostic | ✅ | ✅ | ❌ | ✅ |
| Snapshot diffing | ✅ | ❌ | ❌ | ❌ |
| Zero cloud required | ✅ | ❌ | ❌ | ✅ |
| Chaos injection | ✅ | ❌ | ❌ | ❌ |
| CI-native | ✅ | ⚠️ | ⚠️ | ✅ |
| Python | ✅ | ✅ | ✅ | ✅ |
| Tool call ordering | ✅ | ❌ | ❌ | ❌ |
| Arg contract testing | ✅ | ❌ | ❌ | ❌ |

**Key differences:**
- **Deterministic**: Contracts pass/fail. No probabilistic scoring.
- **Framework-agnostic**: Works with OpenAI, Anthropic, LangChain, or custom agents.
- **Local-first**: No API keys, no cloud dependency, no vendor lock-in.
- **CI-native**: Designed for pytest with beautiful terminal output.

---

## Architecture

```
agentcontract/
├── Core API (contract.py, result.py)
├── Interceptor (interceptor.py)          # Tool call capture
├── Snapshot system (snapshot.py)         # Golden trajectory storage
├── Adapters/                             # Framework integrations
│   ├── OpenAI
│   ├── Anthropic
│   └── LangChain
├── Chaos/                               # Resilience testing
├── pytest_plugin.py                     # pytest integration
└── CLI (cli.py)                         # Command-line tools
```

---

## Philosophy

**1. Deterministic-first**
Contracts are binary: pass or fail. No confidence scores, no "maybe," no LLM-as-judge subjectivity.

**2. Framework-agnostic**
Your tests should outlive your framework. agentcontract works with any agent architecture.

**3. Zero vendor lock-in**
No cloud dependency, no API keys, no external services. Everything runs locally in CI.

**4. Lives in your repo**
Contracts are code. Snapshots are versioned. Tests are `pytest`. Everything is git-trackable.

---

## Roadmap

### [0.2.0] — Next
- Async agent support
- Multi-agent scenario testing
- Performance benchmarking assertions

### [0.3.0] — Coming Soon
- Web dashboard for trace visualization
- Contract sharing and registry

### [1.0.0] — Future
- Stable API guarantee
- Full documentation site
- Plugin ecosystem

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
git clone https://github.com/agentcontract/agentcontract.git
cd agentcontract
pip install -e ".[dev,all]"
pytest tests/
```

### Areas for Contribution

- **New adapters** for emerging frameworks
- **Enhanced chaos strategies** (circuit breakers, random failures)
- **Visualization tools** for trace analysis
- **Documentation** and examples
- **Performance optimizations**

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

<div align="center">

**Built by agents, for agents.** 🚀

Stop vibing. Start contracting.

[📚 Documentation](https://github.com/agentcontract/agentcontract/blob/main/docs/getting-started.md) • [🐛 Issue Tracker](https://github.com/agentcontract/agentcontract/issues) • [💬 Discussions](https://github.com/agentcontract/agentcontract/discussions)

</div>
