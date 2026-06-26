# Security & Privacy

## Trace Data Sensitivity

AgentSpec records every tool name, arguments, response, and timing for executed contracts. These traces are stored in:

- In-memory `AgentTrace`
- `.agentspec/runs/*.jsonl` (if `persist=True`, default)
- `.agentspec/snapshots/*.json`
- Exported JSONL via `agentspec run -o ...`
- Served via `agentspec ui` local dashboard

**Tool arguments may contain PII, secrets, or user data.**

## Configurable Redaction

By default, AgentSpec redacts values for keys containing: password, token, api_key, authorization, secret, credit_card, ssn, private_key, access_token, etc. (case-insensitive, recursive for nested dicts).

Configure additional keys:

```python
runner = ContractRunner(sanitize_keys=["my_custom_pii", "session_id"])
```

To disable all redaction (not recommended):

```python
runner = ContractRunner(sanitize_keys=[])
```

Redaction happens at record time; already-redacted values stay redacted in logs, snapshots, and UI.

## Disabling Persistence

For sensitive environments or CI that may archive artifacts:

```bash
agentspec run tests/ --no-persist
# or env:
AGENTSPEC_NO_PERSIST=1
```

Or in code: `ContractRunner(persist=False)`

When disabled, no `.agentspec/runs/` files are written.

## CI Artifact Risks

Never upload `.agentspec/runs/` or raw snapshots to public CI artifacts, S3, or GitHub Releases without redaction review.

Recommended: use `--no-persist -o sanitized-results.jsonl` and inspect the export.

The `agentspec ui` is local-only (127.0.0.1 by default) and does not expose data over network unless you change host.

## Not Legal Compliance

"Configurable sensitive-field redaction" and "privacy-aware trace logging" are engineering features. They are **not a substitute for legal compliance review**, data protection impact assessments, or formal GDPR/CCPA certification.

See the repository [SECURITY.md](https://github.com/Anudeepsrib/AgentSpec/blob/main/SECURITY.md) for reporting vulnerabilities.

## Reporting Issues

If you discover a sanitization bypass or trace leakage, open a private security advisory on GitHub.
