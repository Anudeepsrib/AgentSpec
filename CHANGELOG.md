# Changelog

All notable changes to AgentSpec are documented in this file.

This project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
and the [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format.

## [0.3.0] - 2026-06-26

### Added
- Public adoption baseline: README badges, clearer package naming, quickstart,
  adapter examples, passing/failing contract demos, contributor guide, and beta
  roadmap.
- LangChain-style and LangGraph-style adapter examples that exercise the
  callback path without requiring external API keys.
- Explicit semantic versioning and release guidance for maintainers.

### Changed
- The canonical PyPI distribution metadata now uses `agentspec-contracts`
  because `agentspec` is already occupied on PyPI by an unrelated project.
- The canonical import and CLI remain `agentspec`.
- Local trace and snapshot state now defaults to `.agentspec/`.
- README and docs now consistently describe the Apache-2.0 license.

### Removed
- Removed the pre-beta `agentcontract` import shim and CLI alias.
- Removed support for legacy `AGENTCONTRACT_*` environment variables.

## [0.2.0] - 2026-04-08

### Added
- Asynchronous agent support through `ContractRunner.arun()` and
  `wrap_tool_async`.
- Multi-agent trackers through the `agent_id` property, allowing concurrent
  interactions to be isolated in assertions.
- Performance assertions for total run duration and individual tool calls.
- Advanced chaos testing with configurable random failures and tool wrappers.

### Changed
- Assertion logic moved from a monolithic result module into
  `agentspec/assertions/` modules for easier maintenance.

## [0.1.0] - 2024-XX-XX

### Added
- Initial release of the AgentSpec contract-testing API.
- Core `@contract` decorator.
- `ContractRunner` for executing agent tests.
- `AgentResult` with fluent assertion API:
  - `must_call()` / `must_not_call()`
  - `before()` / `after()` / `immediately_after()`
  - `with_args()` / `with_args_containing()` / `with_args_matching()`
  - `exactly()` / `at_least()` / `at_most()`
- Snapshot testing with JSON trajectory storage.
- OpenAI, Anthropic, and LangChain adapter scaffolding.
- Chaos injection for failures, latency, and response corruption.
- Pytest plugin and CLI entrypoint.

[0.3.0]: https://github.com/Anudeepsrib/AgentSpec/releases/tag/v0.3.0
[0.2.0]: https://github.com/Anudeepsrib/AgentSpec/releases/tag/v0.2.0
[0.1.0]: https://github.com/Anudeepsrib/AgentSpec/releases/tag/v0.1.0
