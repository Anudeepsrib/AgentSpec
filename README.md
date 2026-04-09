<div align="center">

<img src="docs/logo.png" width="120" style="margin-bottom: 20px" />

# AgentSpec

[![PyPI version](https://badge.fury.io/py/agentcontract.svg)](https://pypi.org/project/agentcontract/)
[![Python versions](https://img.shields.io/pypi/pyversions/agentcontract.svg)](https://pypi.org/project/agentcontract/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://img.shields.io/badge/Build-Passing-brightgreen.svg)]()
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

*Stop scoring agent output quality with "vibes". Start enforcing agent behavior with code.*

[Documentation](https://agentspec.dev) • [Features](#key-features) • [Installation](#installation) • [Contributing](CONTRIBUTING.md)

</div>

---

> [!CAUTION]
> You shipped an agent to production without tests. Now it's 3 AM and your PagerDuty is screaming. The booking agent called `cancel_reservation` before `verify_payment`. The LLM "vibe check" passed in CI, but real users hit catastrophic edge cases your evals never caught. *AgentSpec fixes this.*

## 🌟 What is AgentSpec?

AgentSpec is the first deterministic testing framework for AI agents. Unlike traditional agent evaluation tools that score LLM output quality using probabilistic metrics, AgentSpec provides deterministic contracts that assert exactly what your agent MUST do, MUST NOT do, and MUST do in what order.

## ⚡️ Key Features

| Feature | Description |
|:---|:---|
| 🛡 **Deterministic Assertions** | Test tool executions, parameter accuracy, strict ordering, and thresholds with 100% determinism. |
| 🧪 **ContractSuites** | Group related contracts with shared configuration, sanitization rules, and batch execution. |
| 🛡 **PII Sanitization** | Automatically redact sensitive tool arguments (e.g., passwords, keys) from traces for GDPR compliance. |
| ⏱ **Async & Sync Support** | Native support for `.arun()` and `pytest-asyncio` workflows. |
| 👯‍♀️ **Multi-Agent Tracking** | Isolate concurrent interactions using `agent_id` to prevent cross-contamination. |
| 🌩 **Advanced Chaos Injection** | Simulate tool failures, latency spikes, response corruption, or random stochastic chaos. |
| 📸 **Trajectory Snapshots** | Capture "golden" paths as JSON to lock down complex multi-step behaviors. |
| 💎 **Trace Visualizer UI** | Beautiful local web dashboard to visually trace agent execution via `agentspec ui`. |
| 🔌 **Ecosystem Ready** | Native adapters for OpenAI, Anthropic, LangChain/LangGraph, and simple Custom adapters. |
| 🚀 **CI Integration** | Specialized GitHub Actions and JSONL export for seamless CI/CD artifact collection. |

## 🚀 Quick Start

### Installation

```bash
pip install agentcontract
```
*Note: Package name is retained as `agentcontract` for backward compatibility. Import it as `agentspec` in your code.*

### Your First Contract Test

```python
from agentspec import contract, ContractRunner

@contract("flight_booking")
def test_books_correct_flight():
    # Sanitize sensitive data automatically
    runner = ContractRunner(adapter="openai", sanitize_keys=["credit_card"])
    
    result = runner.run(
        agent=my_agent,
        input="Book a flight to NYC"
    )

    # Deterministic behavior enforcement
    result.must_call("search_flights")
    result.must_call("book_flight").after("search_flights")
    result.must_call("book_flight").with_args_containing(destination="NYC")
    result.must_not_call("cancel_booking")
    
    # Save a golden snapshot
    result.snapshot("happy_path") 
```

### Run and Export Results

```bash
# Run tests and export to JSONL for CI
agentspec run tests/ -o results.jsonl

# Visualize traces locally
agentspec ui
```

## 🧩 Architectural Contracts

### The Contract Philosophy vs. Traditional Testing

| Traditional Agent Evals | AgentSpec |
|---|---|
| *"Is this output good?"* (Subjective) | *"Did the agent call `verify_identity` before `transfer`?"* (Deterministic) |
| LLM-as-judge scoring | Binary pass/fail assertions |
| Probabilistic, flaky | Fast, reliable, cheap |
| Expensive API calls | Local execution |

### Powerful Assertion Syntax

```python
# Call and Order constraints
result.must_call("search_flights")
result.must_not_call("cancel_booking")
result.must_call("auth").before("query").before("update")

# Argument subsets and Regex matches
result.must_call("search").with_args_containing(query="flights to New York")
result.must_call("validate_email").with_args_matching(email=r"^[\w.-]+@[\w.-]+\.\w+$")

# Complex Multi-Agent workflows
result.must_call("transfer", agent_id="banking_agent").immediately_after("auth", agent_id="auth_agent")

# Quantitative scaling
result.tool_call_count("api_call").at_most(5)
```

## 🌪 Chaos Testing

Test how your agent handles real-world failures:

```python
from agentspec.chaos import ChaosInjector

chaos = ChaosInjector()
chaos.fail_tool("search_flights", after_calls=1, error="RateLimitError")
chaos.slow_tool("payment_gateway", latency_ms=5000)

result = runner.run(agent=my_agent, input="Book flight", chaos=chaos)
result.must_call("search_flights").at_least(2) # Verify retry logic
```

## 📈 Roadmap

### 0.4.0 — Policy Engine
- Define global behavioral policies across all agents.
- Drift detection: detect when agent behavior deviates from historical benchmarks.
- OTLP export for distributed tracing integration.

### 1.0.0 — Horizon
- Stable API guarantee.
- Enterprise telemetry endpoints.
- Visual Contract Editor.

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
git clone https://github.com/Anudeepsrib/AgentSpec.git
cd AgentSpec
pip install -e ".[dev,all]"
pytest tests/
```

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

<div align="center">

**Built by Agents. For Agents.**

[Documentation](https://agentspec.dev) • [Issue Tracker](https://github.com/Anudeepsrib/AgentSpec/issues)

</div>
