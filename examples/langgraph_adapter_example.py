"""LangGraph-style adapter example with no external API key.

LangGraph compiled graphs expose .invoke() and pass callbacks through config.
Run:
    python examples/langgraph_adapter_example.py
"""

from agentspec import ContractRunner


class FakeCompiledGraph:
    """Small stand-in for a LangGraph compiled graph."""

    def invoke(self, state, config=None):
        callbacks = (config or {}).get("callbacks", [])

        for callback in callbacks:
            callback.on_tool_start({"name": "search_flights"}, "NYC", run_id="lg-1")
            callback.on_tool_end(
                {"flights": [{"id": "FL-1"}]},
                run_id="lg-1",
                tool_input={"destination": "NYC"},
            )
            callback.on_tool_start({"name": "reserve_flight"}, "FL-1", run_id="lg-2")
            callback.on_tool_end(
                {"reservation_id": "RSV-FL-1"},
                run_id="lg-2",
                tool_input={"flight_id": "FL-1"},
            )

        return {"messages": [*state.get("messages", []), "reserved"]}


def main() -> None:
    runner = ContractRunner(adapter="langchain", persist=False)
    result = runner.run(agent=FakeCompiledGraph(), input={"messages": ["book NYC"]})

    result.must_call("search_flights").with_args(destination="NYC")
    result.must_call("reserve_flight").after("search_flights")
    result.tool_call_count("reserve_flight").exactly(1)
    print("LangGraph-style adapter contract passed")


if __name__ == "__main__":
    main()
