# CI Integration

AgentSpec is designed for CI pipelines. Contract tests are fast, deterministic, and produce machine-readable output.

## GitHub Actions

### Using the Built-In Action

```yaml
# .github/workflows/contracts.yml
name: Agent Contracts
on: [push, pull_request]

jobs:
  contracts:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: ./.github/actions/agentspec
        with:
          test-path: tests/
          python-version: '3.11'
          snapshot-mode: verify
          fail-on-regression: true
```

### Manual Setup

```yaml
name: Agent Contracts
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install
        run: pip install -e ".[dev,all]"

      - name: Run contracts
        run: agentcontract run tests/ -v -o results.jsonl

      - name: Upload results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: contract-results
          path: results.jsonl
```

## JSONL Export

Export test results for programmatic consumption:

```bash
agentcontract run tests/ -o results.jsonl
```

**Output format** (one JSON object per line):
```json
{
  "timestamp": "2024-06-01T12:00:00Z",
  "contract": "booking_flow",
  "passed": true,
  "error": null,
  "tool_count": 3,
  "duration_ms": 42.7,
  "trace": { "tool_calls": [...] }
}
```

## Snapshot Workflows

### Verify Mode (Default)

```bash
agentcontract run tests/          # Compare against saved snapshots
```

If snapshots have changed, the test fails with a diff showing exactly what changed.

### Update Mode

```bash
agentcontract run tests/ --snapshot-update   # Overwrite all snapshots
agentcontract snapshot update tests/         # Interactive update
```

### Recommended CI Pattern

```yaml
# On PRs: verify snapshots match
- name: Verify contracts
  run: agentcontract run tests/ -v

# After merge to main: update snapshots if needed
- name: Update snapshots
  if: github.ref == 'refs/heads/main'
  run: agentcontract run tests/ --snapshot-update
```

## Sensitive Environments

For environments where trace data shouldn't be persisted to disk:

```bash
agentcontract run tests/ --no-persist
```

This disables the JSONL run log entirely. Useful for GDPR/CCPA compliance.

## PII Redaction

Configure redaction at the runner level:

```python
runner = ContractRunner(sanitize_keys=["password", "ssn", "api_key"])
# All traces automatically redact these fields as [REDACTED]
```

## Integration with Other CI Systems

### GitLab CI

```yaml
contract-tests:
  image: python:3.11
  script:
    - pip install -e ".[dev]"
    - agentcontract run tests/ -v -o results.jsonl
  artifacts:
    paths:
      - results.jsonl
    when: always
```

### CircleCI

```yaml
jobs:
  contracts:
    docker:
      - image: cimg/python:3.11
    steps:
      - checkout
      - run: pip install -e ".[dev]"
      - run: agentcontract run tests/ -v -o results.jsonl
      - store_artifacts:
          path: results.jsonl
```
