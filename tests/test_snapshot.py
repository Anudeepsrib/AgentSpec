"""Tests for snapshot functionality."""

import json
import tempfile

import pytest

from agentspec.exceptions import SnapshotMismatch
from agentspec.interceptor import AgentTrace
from agentspec.snapshot import SnapshotManager


def test_snapshot_manager_saves_trace() -> None:
    """Test that SnapshotManager saves traces correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = SnapshotManager(tmpdir)

        trace = AgentTrace()
        trace.record_call("search_flights", {"destination": "NYC"})
        trace.record_call("book_flight", {"flight_id": "123"})

        path = mgr.save("test_contract", trace)

        assert path.exists()
        assert path.name == "test_contract.json"

        data = json.loads(path.read_text())
        assert len(data["tool_calls"]) == 2
        assert data["tool_calls"][0]["name"] == "search_flights"


def test_snapshot_manager_loads_trace() -> None:
    """Test that SnapshotManager loads traces correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = SnapshotManager(tmpdir)

        trace = AgentTrace()
        trace.record_call("search_flights", {"destination": "NYC"})
        mgr.save("test_contract", trace)

        loaded = mgr.load("test_contract")
        assert len(loaded["tool_calls"]) == 1
        assert loaded["tool_calls"][0]["args"]["destination"] == "NYC"


def test_snapshot_manager_detects_mismatch() -> None:
    """Test that SnapshotManager detects differences."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = SnapshotManager(tmpdir)

        # Save original
        trace1 = AgentTrace()
        trace1.record_call("search_flights", {"destination": "NYC"})
        mgr.save("test_contract", trace1)

        # Try to compare different trace
        trace2 = AgentTrace()
        trace2.record_call("search_flights", {"destination": "LA"})

        with pytest.raises(SnapshotMismatch) as exc_info:
            mgr.compare("test_contract", trace2)

        assert "mismatch" in str(exc_info.value).lower()


def test_snapshot_manager_allows_update() -> None:
    """Test that SnapshotManager allows updating snapshots."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = SnapshotManager(tmpdir)

        trace1 = AgentTrace()
        trace1.record_call("search_flights", {"destination": "NYC"})
        mgr.save("test_contract", trace1)

        trace2 = AgentTrace()
        trace2.record_call("search_flights", {"destination": "LA"})

        # Should not raise with update=True
        mgr.compare("test_contract", trace2, update=True)

        # Verify updated
        loaded = mgr.load("test_contract")
        assert loaded["tool_calls"][0]["args"]["destination"] == "LA"


def test_snapshot_manager_creates_nonexistent() -> None:
    """Test that SnapshotManager creates snapshot if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = SnapshotManager(tmpdir)

        trace = AgentTrace()
        trace.record_call("search_flights", {})

        # Should create without raising
        mgr.compare("new_contract", trace)


def test_snapshot_list_and_paths() -> None:
    """Test listing snapshots."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = SnapshotManager(tmpdir)

        trace = AgentTrace()
        mgr.save("contract_a", trace)
        mgr.save("contract_b", trace)

        snapshots = mgr.list_snapshots()
        assert len(snapshots) == 2
        assert all(s.suffix == ".json" for s in snapshots)
