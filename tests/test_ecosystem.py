"""Tests for Sprint 3: Ecosystem features — Adapters, ContractSuite, callback handler."""

from __future__ import annotations

from unittest.mock import MagicMock

from agentspec import ContractSuite
from agentspec.adapters.anthropic import AnthropicAdapter
from agentspec.adapters.langchain import AgentSpecCallbackHandler, LangChainAdapter
from agentspec.interceptor import TraceInterceptor

# ── Anthropic Adapter Tests ─────────────────────────────────────────────────


class TestAnthropicAdapter:
    """Tests for the Anthropic adapter using mock clients."""

    def _make_mock_client(self, tool_use_blocks: list[dict]) -> MagicMock:
        """Build a mock Anthropic client that returns tool_use blocks."""
        mock_client = MagicMock()

        # Build content blocks
        content = []
        for block_data in tool_use_blocks:
            block = MagicMock()
            block.type = "tool_use"
            block.name = block_data["name"]
            block.input = block_data.get("input", {})
            content.append(block)

        response = MagicMock()
        response.content = content

        mock_client.messages.create.return_value = response
        return mock_client

    def test_intercepts_tool_use_blocks(self) -> None:
        interceptor = TraceInterceptor()
        adapter = AnthropicAdapter(interceptor)

        client = self._make_mock_client(
            [
                {"name": "search", "input": {"q": "flights"}},
                {"name": "book", "input": {"id": "FL1"}},
            ]
        )

        interceptor.start()
        adapter.run(
            client,
            input={"messages": [{"role": "user", "content": "book flight"}], "model": "claude-3"},
        )
        interceptor.stop()

        assert len(interceptor.trace.tool_calls) == 2
        assert interceptor.trace.tool_calls[0].name == "search"
        assert interceptor.trace.tool_calls[1].name == "book"

    def test_callable_agent_passes_interceptor(self) -> None:
        interceptor = TraceInterceptor()
        adapter = AnthropicAdapter(interceptor)

        def my_agent(input_text, interceptor=None, **kwargs):
            interceptor.record("custom_tool", {"arg": "value"})
            return "done"

        interceptor.start()
        adapter.run(my_agent, input="hello")
        interceptor.stop()

        assert len(interceptor.trace.tool_calls) == 1
        assert interceptor.trace.tool_calls[0].name == "custom_tool"


# ── LangChain Adapter Tests ────────────────────────────────────────────────


class TestLangChainAdapter:
    """Tests for the LangChain adapter and callback handler."""

    def test_callback_handler_records_tool_calls(self) -> None:
        interceptor = TraceInterceptor()
        handler = AgentSpecCallbackHandler(interceptor)

        interceptor.start()

        # Simulate tool start/end
        run_id = object()
        handler.on_tool_start(
            serialized={"name": "search_flights"},
            input_str="NYC",
            run_id=run_id,
        )
        handler.on_tool_end(
            output={"flights": []},
            run_id=run_id,
            tool_input={"destination": "NYC"},
        )

        interceptor.stop()

        assert len(interceptor.trace.tool_calls) == 1
        assert interceptor.trace.tool_calls[0].name == "search_flights"

    def test_adapter_with_invoke_agent(self) -> None:
        interceptor = TraceInterceptor()
        adapter = LangChainAdapter(interceptor)

        # Mock a LangGraph-style agent with .invoke()
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {"output": "booked"}

        interceptor.start()
        result = adapter.run(mock_agent, input="book a flight")
        interceptor.stop()

        mock_agent.invoke.assert_called_once()
        assert result == {"output": "booked"}

    def test_adapter_with_callable_agent(self) -> None:
        interceptor = TraceInterceptor()
        adapter = LangChainAdapter(interceptor)

        def my_agent(input_text, interceptor=None, **kwargs):
            interceptor.record("tool", {"a": 1})
            return "ok"

        interceptor.start()
        adapter.run(my_agent, input="test")
        interceptor.stop()

        assert len(interceptor.trace.tool_calls) == 1


# ── ContractSuite Tests ─────────────────────────────────────────────────────


class TestContractSuite:
    """Tests for the ContractSuite grouping mechanism."""

    def test_suite_registers_contracts(self) -> None:
        suite = ContractSuite(name="test_suite", persist=False)

        @suite.contract("one")
        def test_one(runner):
            pass

        @suite.contract("two")
        def test_two(runner):
            pass

        assert len(suite._contracts) == 2

    def test_suite_run_all_passes(self) -> None:
        suite = ContractSuite(name="passing_suite", persist=False)

        @suite.contract("pass_test")
        def test_pass(runner):
            def agent(input_text, interceptor=None, **kwargs):
                interceptor.record("tool", {"x": 1})
                return "ok"

            result = runner.run(agent=agent, input="test")
            result.must_call("tool")

        results = suite.run_all()
        assert len(results) == 1
        assert results[0]["passed"] is True
        assert results[0]["error"] is None

    def test_suite_run_all_captures_failures(self) -> None:
        suite = ContractSuite(name="failing_suite", persist=False)

        @suite.contract("fail_test")
        def test_fail(runner):
            def agent(input_text, interceptor=None, **kwargs):
                return "nothing"

            result = runner.run(agent=agent, input="test")
            result.must_call("nonexistent_tool")  # This will fail

        results = suite.run_all()
        assert len(results) == 1
        assert results[0]["passed"] is False
        assert results[0]["error"] is not None

    def test_suite_inherits_sanitize_keys(self) -> None:
        suite = ContractSuite(
            name="sanitize_suite",
            persist=False,
            sanitize_keys=["secret"],
        )

        captured_args = {}

        @suite.contract("sanitize_test")
        def test_sanitize(runner):
            def agent(input_text, interceptor=None, **kwargs):
                interceptor.record(
                    "api_call", {"url": "https://api.example.com", "secret": "sk-abc"}
                )
                return "ok"

            result = runner.run(agent=agent, input="test")
            captured_args.update(result.trace.tool_calls[0].args)

        suite.run_all()
        assert captured_args["url"] == "https://api.example.com"
        assert captured_args["secret"] == "[REDACTED]"

    def test_suite_contracts_have_metadata(self) -> None:
        suite = ContractSuite(name="meta_suite", persist=False)

        @suite.contract("meta_test")
        def test_meta(runner):
            pass

        assert hasattr(test_meta, "_is_contract")
        assert test_meta._is_contract is True
        assert test_meta._contract_name == "meta_suite::meta_test"
