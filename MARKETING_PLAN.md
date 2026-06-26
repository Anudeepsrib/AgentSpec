# AgentSpec Open-Source Adoption Plan

This plan keeps AgentSpec focused on credible beta adoption: useful examples,
clear maintainer practices, and honest positioning around deterministic
tool-call contract testing.

## Positioning

- Lead with "deterministic contract tests for agent tool behavior."
- Avoid compliance, safety, and production-readiness claims that the library
  does not certify.
- Be explicit that AgentSpec complements evals, observability, integration
  tests, and human review.
- Use `agentspec-contracts` for install instructions and `agentspec` for import
  examples.

## Near-Term Adoption Work

- Publish a release candidate to PyPI as `agentspec-contracts`.
- Add one complete example each for:
  - LangChain runnable callbacks
  - LangGraph compiled graph callbacks
  - passing and failing contract tests
  - snapshot review
- Open issues labeled `good first issue`, `adapter`, `docs`, and `beta`.
- Add a short "why contracts, not vibes" blog post to the repository or GitHub
  Discussions.
- Ask early users to share small anonymous tool-call contract examples.

## Community Channels

- GitHub Issues for bugs and feature requests.
- GitHub Discussions for design questions and examples.
- README and MkDocs as the source of truth until hosted docs are configured.

## Launch Checklist

- CI badge is green on `main`.
- Coverage badge is wired to Codecov or replaced with an accurate alternative.
- `python -m build` succeeds after dashboard assets are built.
- `mkdocs build --strict` succeeds.
- README install instructions do not point to unrelated PyPI packages.
- License text, classifiers, and README all say Apache-2.0.

## Not Current Goals

- Hosted dashboard
- Enterprise telemetry
- Visual contract editor
- Compliance certification
- Agent behavior guarantees beyond what the tests assert
