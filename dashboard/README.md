# AgentSpec Dashboard

Local React dashboard for inspecting AgentSpec snapshots through `agentspec ui`.

## Development

```bash
npm ci
npm run build
npm run lint
```

The Python package build expects `dashboard/dist` to exist, so build the
dashboard before running `python -m build`.
