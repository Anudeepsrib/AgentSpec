# Contributing to AgentSpec

Thanks for helping make AgentSpec useful for real agent teams. The project is
in beta, so the best contributions are focused, tested, and easy for maintainers
to review.

## Development Setup

```bash
git clone https://github.com/Anudeepsrib/AgentSpec.git
cd AgentSpec
python -m venv .venv
.venv\Scripts\activate  # Windows PowerShell
python -m pip install --upgrade pip
pip install -e ".[dev,all,docs]"
```

On macOS or Linux, activate the environment with:

```bash
source .venv/bin/activate
```

## Local Checks

Run these before opening a pull request:

```bash
ruff check .
ruff format --check .
pytest tests/ --cov=agentspec --cov=agentcontract
python -m compileall -q agentspec agentcontract tests examples
mkdocs build --strict
```

The dashboard has a separate Node toolchain:

```bash
cd dashboard
npm ci
npm run build
```

## Pull Request Guidelines

- Keep changes scoped to one bug, feature, or documentation improvement.
- Add or update tests when behavior changes.
- Update `README.md`, `docs/`, or examples when public APIs change.
- Update `CHANGELOG.md` for user-visible changes.
- Prefer deterministic examples that do not require external API keys.
- Do not commit `.agentspec/`, `.agentcontract/`, coverage files, or dashboard
  build artifacts.

## Package and Naming Rules

- Product name: `AgentSpec`
- Python import: `agentspec`
- Primary CLI: `agentspec`
- PyPI distribution: `agentspec-contracts`
- Deprecated compatibility alias: `agentcontract`

Do not add new docs that tell users to `pip install agentspec` or
`pip install agentcontract`; those names belong to unrelated PyPI projects.

## Release Process

AgentSpec follows Semantic Versioning.

1. Update the version in `pyproject.toml`.
2. Add a dated entry to `CHANGELOG.md`.
3. Run the local checks above.
4. Build artifacts with `python -m build`.
5. Publish the package as `agentspec-contracts`.
6. Create a GitHub release using the changelog entry.

## Reporting Issues

Bug reports should include:

- AgentSpec version
- Python version and operating system
- Minimal contract test or traceback
- Whether persistence was enabled
- Any adapter involved, such as LangChain, LangGraph, OpenAI, or Anthropic

Security reports should follow [SECURITY.md](SECURITY.md).
