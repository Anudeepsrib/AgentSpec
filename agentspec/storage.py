"""Run log persistence — stores every contract execution as JSONL.

Each line in the runs log file is a JSON object representing one complete
agent trace. This gives developers a historical audit trail of all contract
executions without requiring any external infrastructure.

Usage:
    from agentspec.storage import RunLogger

    logger = RunLogger()
    logger.log(trace)           # Append trace to current run file
    entries = logger.read()     # Read all entries from the log
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agentspec.interceptor import AgentTrace


class RunLogger:
    """Persists contract execution traces as JSONL files.

    Each run session creates entries in a date-stamped file under
    ``.agentspec/runs/``. This provides a zero-config audit trail
    without requiring databases or external services.
    """

    DEFAULT_DIR = ".agentspec/runs"

    def __init__(
        self,
        runs_dir: str | None = None,
        *,
        enabled: bool = True,
    ) -> None:
        self.runs_dir = Path(runs_dir or self.DEFAULT_DIR)
        self._enabled = enabled

    def _ensure_dir(self) -> None:
        """Create the runs directory if it doesn't exist."""
        if self._enabled:
            self.runs_dir.mkdir(parents=True, exist_ok=True)

    def _current_log_path(self) -> Path:
        """Get the log file path for today."""
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return self.runs_dir / f"runs_{date_str}.jsonl"

    def log(
        self,
        trace: AgentTrace,
        *,
        contract_name: str | None = None,
        passed: bool | None = None,
        error: str | None = None,
    ) -> Path | None:
        """Append a trace entry to the run log.

        Args:
            trace: The agent execution trace to persist.
            contract_name: Optional name of the contract that was run.
            passed: Whether the contract passed (None if not yet evaluated).
            error: Error message if the contract failed.

        Returns:
            Path to the log file, or None if persistence is disabled.
        """
        if not self._enabled:
            return None

        self._ensure_dir()
        path = self._current_log_path()

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "contract": contract_name,
            "passed": passed,
            "error": error,
            "trace": trace.to_dict(),
            "tool_count": len(trace.tool_calls),
            "duration_ms": (
                (trace.end_time - trace.start_time) * 1000 if trace.end_time is not None else None
            ),
        }

        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")

        return path

    def read(self, date: str | None = None) -> list[dict[str, Any]]:
        """Read all entries from a run log file.

        Args:
            date: Date string (YYYY-MM-DD) to read. Defaults to today.

        Returns:
            List of log entry dicts.
        """
        path = self.runs_dir / f"runs_{date}.jsonl" if date else self._current_log_path()

        if not path.exists():
            return []

        entries = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
        return entries

    def list_logs(self) -> list[Path]:
        """List all run log files."""
        if not self.runs_dir.exists():
            return []
        return sorted(self.runs_dir.glob("runs_*.jsonl"))

    def clear(self, date: str | None = None) -> int:
        """Clear run log files.

        Args:
            date: If provided, only clear that date's log. Otherwise clear all.

        Returns:
            Number of files deleted.
        """
        if date:
            path = self.runs_dir / f"runs_{date}.jsonl"
            if path.exists():
                path.unlink()
                return 1
            return 0

        logs = self.list_logs()
        for log in logs:
            log.unlink()
        return len(logs)
