"""Tests for all assertion methods."""

import pytest

from agentspec.exceptions import (
    ArgMismatch,
    CountMismatch,
    OrderViolation,
)
from agentspec.interceptor import AgentTrace
from agentspec.result import AgentResult


class TestOrderAssertions:
    """Tests for ordering assertions."""

    def test_before_passes_when_correct_order(self) -> None:
        """Test before() passes when order is correct."""
        trace = AgentTrace()
        trace.record_call("search_flights", {})
        trace.record_call("book_flight", {})

        result = AgentResult(trace)

        # Should not raise
        result.must_call("search_flights").before("book_flight")

    def test_before_fails_when_wrong_order(self) -> None:
        """Test before() fails when order is wrong."""
        trace = AgentTrace()
        trace.record_call("book_flight", {})
        trace.record_call("search_flights", {})

        result = AgentResult(trace)

        with pytest.raises(OrderViolation):
            # search_flights was called AFTER book_flight, so this fails
            result.must_call("search_flights").before("book_flight")

    def test_after_passes_when_correct_order(self) -> None:
        """Test after() passes when order is correct."""
        trace = AgentTrace()
        trace.record_call("search_flights", {})
        trace.record_call("book_flight", {})

        result = AgentResult(trace)
        result.must_call("book_flight").after("search_flights")

    def test_after_fails_when_wrong_order(self) -> None:
        """Test after() fails when order is wrong."""
        trace = AgentTrace()
        trace.record_call("book_flight", {})
        trace.record_call("search_flights", {})

        result = AgentResult(trace)

        with pytest.raises(OrderViolation):
            result.must_call("book_flight").after("search_flights")

    def test_immediately_after_passes(self) -> None:
        """Test immediately_after() when correct."""
        trace = AgentTrace()
        trace.record_call("search_flights", {})
        trace.record_call("book_flight", {})

        result = AgentResult(trace)
        result.must_call("book_flight").immediately_after("search_flights")

    def test_immediately_after_fails_when_not_adjacent(self) -> None:
        """Test immediately_after() fails when not adjacent."""
        trace = AgentTrace()
        trace.record_call("search_flights", {})
        trace.record_call("check_price", {})
        trace.record_call("book_flight", {})

        result = AgentResult(trace)

        with pytest.raises(OrderViolation):
            result.must_call("book_flight").immediately_after("search_flights")


class TestArgAssertions:
    """Tests for argument assertions."""

    def test_with_args_exact_match(self) -> None:
        """Test with_args() with exact match."""
        trace = AgentTrace()
        trace.record_call("search_flights", {"destination": "NYC", "date": "2024-01-01"})

        result = AgentResult(trace)
        result.must_call("search_flights").with_args(destination="NYC", date="2024-01-01")

    def test_with_args_partial_fails(self) -> None:
        """Test with_args() fails on partial match."""
        trace = AgentTrace()
        trace.record_call("search_flights", {"destination": "NYC"})

        result = AgentResult(trace)

        with pytest.raises(ArgMismatch):
            result.must_call("search_flights").with_args(destination="NYC", date="2024-01-01")

    def test_with_args_containing_subset_match(self) -> None:
        """Test with_args_containing() with subset."""
        trace = AgentTrace()
        trace.record_call("search_flights", {"destination": "NYC", "date": "2024-01-01", "passengers": 2})

        result = AgentResult(trace)
        result.must_call("search_flights").with_args_containing(destination="NYC")

    def test_with_args_containing_string_contains(self) -> None:
        """Test with_args_containing() with string substring."""
        trace = AgentTrace()
        trace.record_call("search", {"query": "flights to new york city"})

        result = AgentResult(trace)
        result.must_call("search").with_args_containing(query="new york")

    def test_with_args_matching_regex(self) -> None:
        """Test with_args_matching() with regex."""
        trace = AgentTrace()
        trace.record_call("search", {"query": "flight NYC-12345"})

        result = AgentResult(trace)
        result.must_call("search").with_args_matching(query=r"NYC-\d+")

    def test_with_args_matching_fails_on_mismatch(self) -> None:
        """Test with_args_matching() fails on regex mismatch."""
        trace = AgentTrace()
        trace.record_call("search", {"query": "flight to LA"})

        result = AgentResult(trace)

        with pytest.raises(ArgMismatch):
            result.must_call("search").with_args_matching(query=r"NYC-\d+")


class TestCountAssertions:
    """Tests for count assertions."""

    def test_exactly_passes_when_correct(self) -> None:
        """Test exactly() passes with correct count."""
        trace = AgentTrace()
        trace.record_call("search", {})
        trace.record_call("search", {})

        result = AgentResult(trace)
        result.must_call("search").exactly(2)

    def test_exactly_fails_when_wrong(self) -> None:
        """Test exactly() fails with wrong count."""
        trace = AgentTrace()
        trace.record_call("search", {})

        result = AgentResult(trace)

        with pytest.raises(CountMismatch):
            result.must_call("search").exactly(2)

    def test_at_least_passes(self) -> None:
        """Test at_least() passes."""
        trace = AgentTrace()
        trace.record_call("retry", {})
        trace.record_call("retry", {})
        trace.record_call("retry", {})

        result = AgentResult(trace)
        result.must_call("retry").at_least(2)

    def test_at_least_fails_when_too_few(self) -> None:
        """Test at_least() fails with too few calls."""
        trace = AgentTrace()
        trace.record_call("retry", {})

        result = AgentResult(trace)

        with pytest.raises(CountMismatch):
            result.must_call("retry").at_least(2)

    def test_at_most_passes(self) -> None:
        """Test at_most() passes."""
        trace = AgentTrace()
        trace.record_call("api_call", {})

        result = AgentResult(trace)
        result.must_call("api_call").at_most(2)

    def test_at_most_fails_when_too_many(self) -> None:
        """Test at_most() fails with too many calls."""
        trace = AgentTrace()
        trace.record_call("api_call", {})
        trace.record_call("api_call", {})
        trace.record_call("api_call", {})

        result = AgentResult(trace)

        with pytest.raises(CountMismatch):
            result.must_call("api_call").at_most(2)

    def test_count_assertion_from_result(self) -> None:
        """Test count assertion via tool_call_count()."""
        trace = AgentTrace()
        trace.record_call("search", {})
        trace.record_call("search", {})

        result = AgentResult(trace)
        result.tool_call_count("search").exactly(2)
