# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-XX-XX

### Added
- Initial release of agentcontract
- Core Contract API with `@contract` decorator
- `ContractRunner` for executing agent tests
- `AgentResult` with fluent assertion API:
  - `must_call()` / `must_not_call()` assertions
  - `before()` / `after()` / `immediately_after()` ordering
  - `with_args()` / `with_args_containing()` / `with_args_matching()` argument validation
  - `exactly()` / `at_least()` / `at_most()` count assertions
- Snapshot testing system with diff output
- Framework adapters:
  - OpenAI adapter
  - Anthropic adapter
  - LangChain adapter
- ChaosInjector for resilience testing:
  - `fail_tool()` for injected failures
  - `slow_tool()` for latency injection
  - `corrupt_tool_response()` for response corruption
- pytest plugin with beautiful summary output
- CLI with `run`, `snapshot`, and `init` commands
- Full test suite with pytest
- Complete documentation and examples

### Features

#### Core Assertions
- Tool call detection and validation
- Ordering constraints for sequential tool calls
- Argument matching (exact, subset, regex)
- Call counting with bounds checking
- Output content assertions

#### Snapshot Testing
- JSON-based trajectory storage
- Automatic snapshot creation on first run
- Colored diff output on mismatch
- `agentcontract snapshot update` for bulk updates

#### Framework Support
- Generic adapter interface for any framework
- Built-in adapters for major LLM frameworks
- Easy extension for custom agents

#### Chaos Engineering
- Configurable failure injection
- Latency simulation
- Response corruption
- Retry behavior validation

#### Developer Experience
- Rich terminal output with colored diffs
- Clear, actionable error messages
- Full type hints throughout
- pytest integration with summary tables
- CLI for common operations

## Roadmap

### [0.2.0] - Planned
- Async agent support
- Multi-agent scenario testing
- Performance benchmarking assertions
- Enhanced chaos strategies (random, circuit breaker)

### [0.3.0] - Planned
- Web dashboard for trace visualization
- Integration with popular agent frameworks
- Contract sharing and registry
- Advanced snapshot management

### [1.0.0] - Future
- Stable API guarantee
- Full documentation site
- Plugin ecosystem
- Enterprise features

---

[0.1.0]: https://github.com/agentcontract/agentcontract/releases/tag/v0.1.0
