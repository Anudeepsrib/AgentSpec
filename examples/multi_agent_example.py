"""Example: Multi-agent contract testing with AgentSpec.

Demonstrates:
- agent_id isolation for multi-agent systems
- Cross-agent ordering assertions
- ContractSuite grouping

Run:  python examples/multi_agent_example.py
Test: pytest examples/multi_agent_example.py -v
"""

from agentspec import contract, ContractRunner, ContractSuite


# ── Simulated multi-agent system ────────────────────────────────────────────

def planner_agent(task: str, interceptor=None, **kwargs):
    """Planner agent: creates plans and delegates to executor."""
    plan = interceptor.wrap_tool(
        lambda task: {"steps": ["search", "validate", "book"]},
        "create_plan",
    )
    delegate = interceptor.wrap_tool(
        lambda plan: {"delegated": True},
        "delegate_to_executor",
    )

    result = plan(task=task)
    delegate(plan=result)
    return {"role": "planner", "plan": result}


def executor_agent(plan: dict, interceptor=None, **kwargs):
    """Executor agent: executes each step in the plan."""
    search = interceptor.wrap_tool(
        lambda q: {"results": [{"id": "FL1"}]},
        "search_flights",
    )
    validate = interceptor.wrap_tool(
        lambda fid: {"valid": True},
        "validate_availability",
    )
    book = interceptor.wrap_tool(
        lambda fid: {"booking_id": "BK-FL1"},
        "book_flight",
    )

    flights = search(q="NYC")
    is_valid = validate(fid="FL1")
    if is_valid["valid"]:
        booking = book(fid="FL1")
    return {"role": "executor", "booking": booking}


def orchestrator(user_input: str, interceptor=None, **kwargs):
    """Orchestrator that runs planner then executor."""
    # Phase 1: Planning
    interceptor.record("create_plan", {"task": user_input}, agent_id="planner")
    interceptor.record("delegate_to_executor", {"steps": 3}, agent_id="planner")

    # Phase 2: Execution
    interceptor.record("search_flights", {"destination": "NYC"}, agent_id="executor")
    interceptor.record("validate_availability", {"flight_id": "FL1"}, agent_id="executor")
    interceptor.record("book_flight", {"flight_id": "FL1"}, agent_id="executor")

    return "Booked FL1 via NYC"


# ── Contract tests ──────────────────────────────────────────────────────────

@contract("multi_agent_ordering")
def test_planner_before_executor():
    """Planner must create plan before executor runs any step."""
    runner = ContractRunner(persist=False)
    result = runner.run(agent=orchestrator, input="Book flight to NYC")

    # Planner creates plan first
    result.must_call("create_plan", agent_id="planner")

    # Executor searches after planning
    result.must_call("search_flights", agent_id="executor").after(
        "delegate_to_executor", agent_id="planner"
    )


@contract("agent_isolation")
def test_agents_dont_cross_boundaries():
    """Planner should not call executor tools and vice versa."""
    runner = ContractRunner(persist=False)
    result = runner.run(agent=orchestrator, input="Book flight")

    # Planner only plans
    result.must_call("create_plan", agent_id="planner")
    result.must_not_call("book_flight", agent_id="planner")

    # Executor only executes
    result.must_call("book_flight", agent_id="executor")
    result.must_not_call("create_plan", agent_id="executor")


# ── Suite-based tests ──────────────────────────────────────────────────────

suite = ContractSuite(name="multi_agent_suite", persist=False)


@suite.contract("executor_tool_count")
def test_executor_tool_count(runner):
    """Executor should call exactly 3 tools."""
    result = runner.run(agent=orchestrator, input="Book")
    result.tool_call_count("search_flights", agent_id="executor").exactly(1)
    result.tool_call_count("validate_availability", agent_id="executor").exactly(1)
    result.tool_call_count("book_flight", agent_id="executor").exactly(1)


if __name__ == "__main__":
    print("=" * 50)
    print("  Multi-Agent Contract Tests")
    print("=" * 50)
    print()

    test_planner_before_executor()
    print("[PASS] test_planner_before_executor")

    test_agents_dont_cross_boundaries()
    print("[PASS] test_agents_dont_cross_boundaries")

    results = suite.run_all()
    for r in results:
        status = "[PASS]" if r["passed"] else "[FAIL]"
        print(f"{status} {r['name']}")

    print()
    print("All multi-agent contracts passed!")
