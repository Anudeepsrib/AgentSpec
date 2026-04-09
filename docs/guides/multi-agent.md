# Multi-Agent Testing

AgentSpec natively supports testing multi-agent systems where multiple agents interact, delegate, and coordinate tool calls. The `agent_id` parameter isolates traces per agent, preventing cross-contamination.

## Basic Multi-Agent Test

```python
from agentcontract import ContractRunner

runner = ContractRunner()

def orchestrator(user_input, interceptor=None, **kwargs):
    # Planner agent
    plan = interceptor.wrap_tool(lambda q: {"steps": ["search", "book"]}, "create_plan")
    plan(q=user_input)

    # Executor agent
    search = interceptor.wrap_tool(search_fn, "search_flights")
    search(destination="NYC")

    # Record with agent_id for isolation
    interceptor.record("search_flights", {"destination": "NYC"}, agent_id="planner")
    interceptor.record("execute_plan", {"steps": 2}, agent_id="executor")
    return "done"

result = runner.run(agent=orchestrator, input="Book flight")

# Assert across agents
result.must_call("search_flights", agent_id="planner")
result.must_call("execute_plan", agent_id="executor")
```

## Cross-Agent Ordering

Assert that one agent's tool call happens before another agent's:

```python
# Auth agent must call verify_identity before banking agent calls transfer
result.must_call("transfer", agent_id="banking_agent") \
      .after("verify_identity", agent_id="auth_agent")

# Planner must create plan before executor runs
result.must_call("execute_plan", agent_id="executor") \
      .immediately_after("create_plan", agent_id="planner")
```

## Agent-Scoped Count Assertions

```python
# Each agent should call its tools the expected number of times
result.tool_call_count("search", agent_id="research_agent").at_least(1)
result.tool_call_count("execute", agent_id="executor").exactly(1)
```

## Using ContractSuite for Multi-Agent Tests

```python
from agentcontract import ContractSuite

suite = ContractSuite(name="multi_agent_booking", persist=False)

@suite.contract("planner_calls_correct_tools")
def test_planner(runner):
    result = runner.run(agent=orchestrator, input="book flight")
    result.must_call("create_plan", agent_id="planner")
    result.must_not_call("execute_plan", agent_id="planner")  # Planner doesn't execute

@suite.contract("executor_follows_plan")
def test_executor(runner):
    result = runner.run(agent=orchestrator, input="book flight")
    result.must_call("execute_plan", agent_id="executor")
    result.must_call("execute_plan", agent_id="executor").after("create_plan", agent_id="planner")
```

## Best Practices

1. **Always use `agent_id`** -- Without it, tool calls from different agents are indistinguishable
2. **Test cross-agent ordering** -- The most common multi-agent bug is agents executing out of order
3. **Test isolation** -- Assert that agent A does NOT call agent B's tools
4. **Use suites** -- Group related multi-agent contracts for shared setup
