# Writing Contracts

See the Quick Start and README examples. Use `@contract("name")` decorator or direct `ContractRunner`.

Key patterns:

- Wrap tools with `interceptor.wrap_tool(tool, "name")` or `runner.wrap_tool`
- Use fluent assertions on `AgentResult`
- Call `result.snapshot("name")` for golden path locking
- Use `ContractSuite` for shared config (adapter, sanitize_keys, persist)

For async agents use `await runner.arun(...)` and `@pytest.mark.asyncio`.

Full API details are in the source under `agentspec/`.