"""Tests for ChaosInjector."""

import pytest
import time

from agentcontract.chaos import ChaosInjector, ChaosRule
from agentcontract.chaos.injector import RateLimitError


class TestChaosInjector:
    """Tests for ChaosInjector."""

    def test_fail_tool_after_calls(self) -> None:
        """Test that fail_tool triggers after specified calls."""
        chaos = ChaosInjector()
        chaos.fail_tool("api_call", after_calls=1, error="RuntimeError")

        rule = chaos._rules["api_call"]

        # First call should not fail
        rule.call_count = 0
        assert not rule.should_fail_now()

        # Second call should fail
        assert rule.should_fail_now()

        # Third call should also fail
        assert rule.should_fail_now()

    def test_fail_tool_generates_error(self) -> None:
        """Test that fail_tool generates correct error types."""
        chaos = ChaosInjector()
        chaos.fail_tool("api", after_calls=0, error="RateLimitError", message="Too many requests")

        rule = chaos._rules["api"]
        rule.call_count = 1  # Simulate a call already made

        error = rule.get_error()
        assert isinstance(error, RateLimitError)
        assert "Too many requests" in str(error)

    def test_slow_tool_adds_latency(self) -> None:
        """Test that slow_tool adds configured latency."""
        chaos = ChaosInjector()
        chaos.slow_tool("slow_api", latency_ms=100)

        rule = chaos._rules["slow_api"]
        assert rule.latency_ms == 100

    def test_corrupt_tool_response(self) -> None:
        """Test that corrupt_tool_response corrupts after specified calls."""
        chaos = ChaosInjector()
        chaos.corrupt_tool_response("weather", response={"temp": "corrupted"}, after_calls=1)

        rule = chaos._rules["weather"]
        assert rule.corrupt_response == {"temp": "corrupted"}
        assert rule.corrupt_after_calls == 1

    def test_wrap_function_applies_chaos(self) -> None:
        """Test that apply wraps functions correctly."""

        def original_func() -> str:
            return "success"

        chaos = ChaosInjector()
        chaos.fail_tool("my_tool", after_calls=0, error="ValueError")

        wrapped = chaos.apply("my_tool", original_func)

        with pytest.raises(ValueError):
            wrapped()

    def test_wrap_function_allows_success(self) -> None:
        """Test that apply allows success when not triggered."""

        def original_func() -> str:
            return "success"

        chaos = ChaosInjector()
        chaos.fail_tool("my_tool", after_calls=2, error="ValueError")

        wrapped = chaos.apply("my_tool", original_func)

        # First call should succeed
        assert wrapped() == "success"
        # Second call should succeed
        assert wrapped() == "success"
        # Third call should fail
        with pytest.raises(ValueError):
            wrapped()

    def test_chaos_summary(self) -> None:
        """Test that get_summary provides useful info."""
        chaos = ChaosInjector()
        chaos.fail_tool("api", after_calls=1)
        chaos.slow_tool("db", latency_ms=100)

        # Simulate some calls
        for _ in range(3):
            chaos._rules["api"].should_fail_now()

        summary = chaos.get_summary()
        assert "api" in summary
        assert summary["api"]["calls"] == 3
        assert summary["api"]["failures"] == 2  # After first call

    def test_chaining_configuration(self) -> None:
        """Test that chaos configuration methods chain."""
        chaos = ChaosInjector()

        result = (
            chaos.fail_tool("api", after_calls=1)
            .slow_tool("api", latency_ms=100)
            .corrupt_tool_response("api", response=None)
        )

        assert result is chaos
        assert "api" in chaos._rules
        assert chaos._rules["api"].latency_ms == 100
