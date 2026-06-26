# Roadmap

AgentSpec is deliberately beta-sized. The near-term focus is the deterministic
contract-testing core, adapter hardening, and release quality.

## 0.3.x Beta Stabilization

- Publish and verify the `agentspec-contracts` PyPI distribution.
- Keep the `agentspec` import and CLI stable across patch releases.
- Improve failure messages for ordering and argument mismatches.
- Add more zero-key examples for common tool-calling patterns.
- Document migration notes from the legacy `agentcontract` alias.

## 0.4.0 Adapter Hardening

- Expand LangChain and LangGraph callback coverage with real integration tests.
- Add clearer adapter error messages when optional dependencies are missing.
- Support async callback examples for `.ainvoke()` workflows.
- Improve trace sanitization controls for nested and custom argument types.

## 0.5.0 Contract Authoring

- Add a small contract template generator to `agentspec init`.
- Add focused snapshot review commands for changed traces.
- Add JSON schema validation for exported result files.
- Document stable extension points for custom adapters.

## Not In The Current Beta Roadmap

- Hosted SaaS dashboard
- Enterprise telemetry backend
- Visual drag-and-drop contract editor
- LLM-as-judge scoring
- Compliance certification claims
