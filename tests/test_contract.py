"""Tests for the core contract system."""

import pytest
from agentspec import contract, ContractRunner, AgentResult
from agentspec.interceptor import AgentTrace
from agentspec.exceptions import ToolNotCalled, ToolCalledUnexpectedly


def test_contract_runner_creates_result() -> None:
    """Test that ContractRunner creates AgentResult."""
    runner = ContractRunner()
    trace = AgentTrace()

    # Simulate some calls
    trace.record_call("search_flights", {"destination": "NYC"})
    trace.record_call("book_flight", {"flight_id": "123"})

    result = AgentResult(trace)

    assert isinstance(result, AgentResult)
    assert len(result.trace.tool_calls) == 2


def test_must_call_passes_when_tool_called() -> None:
    """Test must_call passes when tool was called."""
    runner = ContractRunner()
    trace = AgentTrace()
    trace.record_call("search_flights", {"destination": "NYC"})

    result = AgentResult(trace)

    # Should not raise
    assertion = result.must_call("search_flights")
    assert assertion is not None


def test_must_call_fails_when_tool_not_called() -> None:
    """Test must_call fails when tool was not called."""
    runner = ContractRunner()
    trace = AgentTrace()

    result = AgentResult(trace)

    with pytest.raises(ToolNotCalled) as exc_info:
        result.must_call("search_flights")

    assert "search_flights" in str(exc_info.value)


def test_must_not_call_passes_when_tool_not_called() -> None:
    """Test must_not_call passes when tool was not called."""
    trace = AgentTrace()
    trace.record_call("search_flights", {})

    result = AgentResult(trace)

    # Should not raise
    result.must_not_call("cancel_booking")


def test_must_not_call_fails_when_tool_called() -> None:
    """Test must_not_call fails when tool was called."""
    trace = AgentTrace()
    trace.record_call("cancel_booking", {})

    result = AgentResult(trace)

    with pytest.raises(ToolCalledUnexpectedly) as exc_info:
        result.must_not_call("cancel_booking")

    assert "cancel_booking" in str(exc_info.value)


def test_contract_decorator_preserves_function() -> None:
    """Test that @contract decorator preserves function metadata."""

    @contract("test_contract")
    def my_test_function() -> str:
        """My docstring."""
        return "result"

    assert my_test_function.__name__ == "my_test_function"
    assert my_test_function.__doc__ == "My docstring."
    assert hasattr(my_test_function, "_is_contract")
    assert my_test_function._contract_name == "test_contract"


def test_contract_decorator_runs_function() -> None:
    """Test that decorated function runs correctly."""

    @contract("test_contract")
    def my_test_function() -> str:
        return "success"

    result = my_test_function()
    assert result == "success"


def test_result_tracks_assertions() -> None:
    """Test that AgentResult tracks assertion count."""
    trace = AgentTrace()
    trace.record_call("search_flights", {})

    result = AgentResult(trace)
    result.must_call("search_flights")

    summary = result.get_assertion_summary()
    assert "1 assertions" in summary
