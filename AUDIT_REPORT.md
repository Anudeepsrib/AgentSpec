# AgentSpec Adoption Readiness Report

**Date:** 2026-06-26  
**Repository:** https://github.com/Anudeepsrib/AgentSpec  
**Goal:** Prepare AgentSpec for credible public beta adoption.

## Current Package Posture

- Product name: AgentSpec
- Python import: `agentspec`
- Primary CLI: `agentspec`
- PyPI distribution: `agentspec-contracts`
- Deprecated compatibility alias: `agentcontract`
- License: Apache-2.0
- Version: `0.3.0`

The distribution name changed because the `agentspec` and `agentcontract` PyPI
names are already occupied by unrelated projects. Public install docs now use
`agentspec-contracts`.

## Readiness Improvements

- README now has real CI and coverage badges, Apache license text, beta status,
  quickstart, examples, adapter guidance, CI usage, and SemVer notes.
- `pyproject.toml` now uses the unique `agentspec-contracts` distribution name
  and repository-hosted documentation URLs.
- Runtime state defaults to `.agentspec/` for runs and snapshots.
- `AGENTSPEC_*` environment variables are the documented names.
- Legacy `AGENTCONTRACT_*` variables and `agentcontract` import/CLI aliases
  remain supported for compatibility.
- Changelog, contributing guide, roadmap, security docs, and MkDocs navigation
  are updated.
- LangChain and LangGraph adapter demos were added with no external API keys.
- Passing and intentionally failing contract demos were added.
- The pytest plugin now reports expected failures as `XFAIL`.
- CI package build now builds dashboard assets before creating sdist/wheel.

## Verification

- `ruff check .`
- `ruff format --check .`
- `pytest tests/ -q`
- `python -m compileall -q agentspec agentcontract tests examples`
- `python examples/quickstart.py`
- `pytest examples/test_contract_demos.py -q -rx`
- `python examples/langchain_adapter_example.py`
- `python examples/langgraph_adapter_example.py`
- `npm ci --silent`
- `npm run build`
- `python -m build`
- `mkdocs build --strict`

All checks above passed in the local workspace.

## Remaining Beta Risks

- The `agentspec-contracts` PyPI project still needs to be published and
  verified by a maintainer.
- Coverage badge accuracy depends on Codecov being configured for the
  repository.
- LangChain and LangGraph examples use callback-compatible fakes; real
  framework integration tests should be added before claiming hard support.
- The local dashboard is packaged only when dashboard assets are built before
  release.
- Hosted documentation is not configured yet; GitHub and MkDocs output are the
  current source of truth.

## Recommended Next Steps

1. Publish `agentspec-contracts` to PyPI.
2. Configure Codecov or replace the coverage badge with the chosen coverage
   provider.
3. Add real LangChain and LangGraph integration tests.
4. Decide whether generated `site/` should remain committed or be published by
   CI only.
5. Tag the first beta release after reviewing the package artifacts.
