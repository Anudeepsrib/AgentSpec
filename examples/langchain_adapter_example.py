"""LangChain-style adapter example with no external API key.

This mirrors the callback shape used by LangChain runnables and AgentExecutor.
Run:
    python examples/langchain_adapter_example.py
"""

from agentspec import ContractRunner


class FakeLangChainRunnable:
    """Small stand-in for a LangChain object exposing .invoke()."""

    def invoke(self, input_value, config=None):
        callbacks = (config or {}).get("callbacks", [])

        for callback in callbacks:
            callback.on_tool_start({"name": "lookup_customer"}, "alice@example.com", run_id="lc-1")
            callback.on_tool_end(
                {"tier": "premium"},
                run_id="lc-1",
                tool_input={"email": "alice@example.com"},
            )
            callback.on_tool_start({"name": "create_ticket"}, "refund request", run_id="lc-2")
            callback.on_tool_end(
                {"ticket_id": "T-100"},
                run_id="lc-2",
                tool_input={"priority": "normal"},
            )

        return {"output": "ticket created"}


def main() -> None:
    runner = ContractRunner(adapter="langchain", persist=False)
    result = runner.run(agent=FakeLangChainRunnable(), input="Open a refund ticket")

    result.must_call("lookup_customer").with_args(email="alice@example.com")
    result.must_call("create_ticket").after("lookup_customer")
    result.must_not_call("issue_refund")
    print("LangChain-style adapter contract passed")


if __name__ == "__main__":
    main()
