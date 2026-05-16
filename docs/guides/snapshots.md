# Snapshot Testing

Snapshots capture the exact sequence of tool calls (names, args, order) and compare on subsequent runs.

- `result.snapshot("my_flow")` — saves on first run or with update=True / env var
- Update mode: `AGENTCONTRACT_UPDATE_SNAPSHOTS=1 agentspec run ...` or `agentspec snapshot update`
- Snapshots live in `.agentcontract/snapshots/<name>.json`
- Volatile fields (timestamps, duration) are stripped for stable comparison

Path names are sanitized to prevent traversal.

See `SnapshotManager` and test_snapshot.py for behavior.