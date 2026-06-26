# Security Policy

## Reporting a Vulnerability

If you discover a security issue (sanitization bypass, path traversal in snapshot names, arbitrary file exposure in UI, secret leakage in traces, or CLI command injection), please report it privately via a GitHub Security Advisory:

https://github.com/Anudeepsrib/AgentSpec/security/advisories/new

Do not open a public issue for vulnerabilities.

We will acknowledge within 72 hours and aim to release fixes promptly.

## Sensitive Data Handling

- Traces and run logs (`.agentspec/runs/`) may contain unredacted tool arguments unless `sanitize_keys` or defaults catch them.
- Snapshots capture args at save time.
- The local dashboard (`agentspec ui`) serves traces over localhost only.
- Never commit `.agentspec/` directories or push trace artifacts to public CI without review.
- Use `--no-persist` or `ContractRunner(persist=False)` in sensitive tests.

## Supply Chain

- Optional adapters (OpenAI, Anthropic, LangChain) are not required for core install.
- Dashboard is a separate Vite/React build; audit `dashboard/package.json` and run `npm audit`.
- CI uses no real API keys.

## Supported Versions

Only the latest main branch / tagged release receives security fixes.

## Credits

Thank you to reporters who help keep AgentSpec safe for the AI agent testing community.
