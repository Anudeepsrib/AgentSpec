# AgentSpec

**Deterministic contract testing for AI agent tool behavior.**

AgentSpec lets you write code that asserts exactly which tools your agent must call, in what order, with what arguments, and how many times—providing binary pass/fail results instead of probabilistic "vibes" scoring.

- [Getting Started](getting-started.md)
- [Quick Start](quickstart.md)
- [Guides](guides/chaos-testing.md)
- [GitHub](https://github.com/Anudeepsrib/AgentSpec)

> **Note**: This site is a local MkDocs preview. The `agentspec.dev` domain is currently for sale and not owned by the project. Full hosted docs are planned.

## Key Capabilities
- Fluent assertions: `must_call`, `before`, `with_args`, `tool_call_count().exactly()`
- Snapshot "golden path" locking
- Configurable PII redaction (password, token, api_key, ssn, ...)
- Chaos injection for resilience testing
- Local trace visualizer (`agentspec ui`)
- Pytest integration + CLI (`agentspec run`)
- Optional adapters for OpenAI / Anthropic / LangChain

See the [README](../README.md) for full positioning and limitations.

## Installation

```bash
pip install agentcontract
# Import as:
from agentspec import contract, ContractRunner
```

## Status
Beta. See [README](../README.md#project-status) for details on what is and is not tested.