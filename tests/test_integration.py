"""Integration tests for storage, sanitization, and full contract lifecycle."""

import json
import os
import shutil
import tempfile
from pathlib import Path

from agentspec import ContractRunner, contract
from agentspec.interceptor import AgentTrace, TraceInterceptor
from agentspec.storage import RunLogger

# ── RunLogger Tests ──────────────────────────────────────────────────────────


class TestRunLogger:
    """Tests for the JSONL run log persistence module."""

    def setup_method(self) -> None:
        self.tmp_dir = tempfile.mkdtemp()
        self.logger = RunLogger(runs_dir=self.tmp_dir)

    def teardown_method(self) -> None:
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_log_creates_file(self) -> None:
        trace = AgentTrace()
        trace.record_call("search", {"q": "test"})
        trace.finish("done")

        path = self.logger.log(trace, contract_name="test_contract")
        assert path is not None
        assert path.exists()
        assert path.suffix == ".jsonl"

    def test_log_appends_entries(self) -> None:
        trace1 = AgentTrace()
        trace1.record_call("tool_a", {"x": 1})
        trace1.finish("ok")

        trace2 = AgentTrace()
        trace2.record_call("tool_b", {"y": 2})
        trace2.finish("ok")

        self.logger.log(trace1, contract_name="first")
        self.logger.log(trace2, contract_name="second")

        entries = self.logger.read()
        assert len(entries) == 2
        assert entries[0]["contract"] == "first"
        assert entries[1]["contract"] == "second"

    def test_log_disabled(self) -> None:
        disabled_logger = RunLogger(runs_dir=self.tmp_dir, enabled=False)
        trace = AgentTrace()
        trace.finish()

        result = disabled_logger.log(trace)
        assert result is None

    def test_log_records_metadata(self) -> None:
        trace = AgentTrace()
        trace.record_call("search", {"q": "test"})
        trace.record_call("book", {"id": "1"})
        trace.finish("completed")

        self.logger.log(trace, contract_name="meta_test", passed=True)
        entries = self.logger.read()

        assert len(entries) == 1
        entry = entries[0]
        assert entry["contract"] == "meta_test"
        assert entry["passed"] is True
        assert entry["tool_count"] == 2
        assert entry["duration_ms"] is not None
        assert "trace" in entry

    def test_list_logs(self) -> None:
        trace = AgentTrace()
        trace.finish()
        self.logger.log(trace)

        logs = self.logger.list_logs()
        assert len(logs) >= 1

    def test_clear_all(self) -> None:
        trace = AgentTrace()
        trace.finish()
        self.logger.log(trace)

        count = self.logger.clear()
        assert count >= 1
        assert self.logger.list_logs() == []


# ── Sanitization Tests ──────────────────────────────────────────────────────


class TestSanitization:
    """Tests for PII redaction in TraceInterceptor."""

    def test_sanitize_keys_redacts_values(self) -> None:
        interceptor = TraceInterceptor(sanitize_keys=["password", "ssn"])
        interceptor.start()
        interceptor.record(
            "create_user",
            {"name": "John", "password": "secret123", "ssn": "123-45-6789"},
        )
        interceptor.stop()

        call = interceptor.trace.tool_calls[0]
        assert call.args["name"] == "John"
        assert call.args["password"] == "[REDACTED]"
        assert call.args["ssn"] == "[REDACTED]"

    def test_no_sanitize_keys_passes_through(self) -> None:
        interceptor = TraceInterceptor()
        interceptor.start()
        interceptor.record("tool", {"password": "secret"})
        interceptor.stop()

        call = interceptor.trace.tool_calls[0]
        assert call.args["password"] == "secret"

    def test_sanitize_via_contract_runner(self) -> None:
        runner = ContractRunner(
            persist=False,
            sanitize_keys=["api_key"],
        )

        def agent(input_text, interceptor=None, **kwargs):
            interceptor.record("call_api", {"url": "https://api.example.com", "api_key": "sk-abc123"})
            return "ok"

        result = runner.run(agent=agent, input="test")
        call = result.trace.tool_calls[0]
        assert call.args["url"] == "https://api.example.com"
        assert call.args["api_key"] == "[REDACTED]"


# ── Full Lifecycle Tests ────────────────────────────────────────────────────


class TestFullLifecycle:
    """Integration tests for the complete contract pipeline."""

    def setup_method(self) -> None:
        self.tmp_dir = tempfile.mkdtemp()
        self.snapshot_dir = os.path.join(self.tmp_dir, "snapshots")
        self.runs_dir = os.path.join(self.tmp_dir, "runs")

    def teardown_method(self) -> None:
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_run_persist_snapshot_lifecycle(self) -> None:
        """Full pipeline: run agent → persist log → save snapshot → compare."""
        runner = ContractRunner(
            snapshot_dir=self.snapshot_dir,
            persist=False,
        )

        def mock_agent(input_text, interceptor=None, **kwargs):
            search = interceptor.wrap_tool(
                lambda dest: {"flights": [{"id": "FL1"}]},
                "search_flights",
            )
            book = interceptor.wrap_tool(
                lambda fid: {"booking": "BK1"},
                "book_flight",
            )
            search(dest="NYC")
            book(fid="FL1")
            return "Booked"

        result = runner.run(agent=mock_agent, input="Book NYC flight")

        # Assertions work
        result.must_call("search_flights")
        result.must_call("book_flight").after("search_flights")
        result.must_not_call("cancel_booking")
        result.tool_call_count("search_flights").exactly(1)

        # Snapshot save works
        result.snapshot("lifecycle_test", update=True)

        # Snapshot file exists
        snap_path = Path(self.snapshot_dir) / "lifecycle_test.json"
        assert snap_path.exists()

        # Snapshot content is valid JSON
        with open(snap_path) as f:
            data = json.load(f)
        assert len(data["tool_calls"]) == 2

    def test_snapshot_comparison_passes_on_identical_run(self) -> None:
        """Two identical runs should produce matching snapshots."""
        def make_runner():
            return ContractRunner(
                snapshot_dir=self.snapshot_dir,
                persist=False,
            )

        def mock_agent(input_text, interceptor=None, **kwargs):
            tool = interceptor.wrap_tool(lambda x: x, "echo")
            tool(x="hello")
            return "done"

        # Run 1: save snapshot
        r1 = make_runner()
        result1 = r1.run(agent=mock_agent, input="test")
        result1.snapshot("compare_test", update=True)

        # Run 2: compare against snapshot (should not raise)
        r2 = make_runner()
        result2 = r2.run(agent=mock_agent, input="test")
        result2.snapshot("compare_test")  # Should pass — no SnapshotMismatch

    def test_contract_decorator_with_full_pipeline(self) -> None:
        """The @contract decorator works end-to-end."""

        @contract("decorator_lifecycle")
        def my_contract_test():
            runner = ContractRunner(persist=False)

            def agent(input_text, interceptor=None, **kwargs):
                fn = interceptor.wrap_tool(lambda: "ok", "ping")
                fn()
                return "pong"

            result = runner.run(agent=agent, input="ping")
            result.must_call("ping")
            return result

        # Should not raise
        my_contract_test()
