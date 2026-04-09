"""Snapshot recording, storage, and diffing."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from agentspec.exceptions import SnapshotMismatch
from agentspec.interceptor import AgentTrace

console = Console()


class SnapshotManager:
    """Manages snapshot recording, storage, and comparison."""

    DEFAULT_DIR = ".agentcontract/snapshots"

    def __init__(self, snapshot_dir: str | None = None) -> None:
        self.snapshot_dir = Path(snapshot_dir or self.DEFAULT_DIR)
        self._ensure_dir()

    def _ensure_dir(self) -> None:
        """Ensure snapshot directory exists."""
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

    def _get_snapshot_path(self, name: str) -> Path:
        """Get the file path for a snapshot."""
        safe_name = name.replace("/", "_").replace("\\", "_").replace(" ", "_")
        return self.snapshot_dir / f"{safe_name}.json"

    def exists(self, name: str) -> bool:
        """Check if a snapshot exists."""
        return self._get_snapshot_path(name).exists()

    def save(self, name: str, trace: AgentTrace) -> Path:
        """Save a trace as a snapshot."""
        path = self._get_snapshot_path(name)
        data = trace.to_dict()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return path

    def load(self, name: str) -> dict[str, Any]:
        """Load a snapshot."""
        path = self._get_snapshot_path(name)
        if not path.exists():
            raise FileNotFoundError(f"Snapshot not found: {path}")
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def compare(self, name: str, trace: AgentTrace, update: bool = False) -> None:
        """Compare a trace against a snapshot.

        Args:
            name: Snapshot name
            trace: Current execution trace
            update: If True, update snapshot instead of comparing

        Raises:
            SnapshotMismatch: If traces don't match
        """
        if update or not self.exists(name):
            path = self.save(name, trace)
            console.print(f"[green]Snapshot saved: {path}[/green]")
            return

        expected_data = self.load(name)
        actual_data = trace.to_dict()

        diff = self._compute_diff(expected_data, actual_data)

        if diff:
            raise SnapshotMismatch(
                message=f"Snapshot mismatch: {name}",
                expected=expected_data.get("tool_calls", []),
                actual=actual_data.get("tool_calls", []),
                diff=diff,
            )

    def _compute_diff(self, expected: dict, actual: dict) -> str | None:
        """Compute differences between snapshots.

        Strips non-deterministic fields (timestamp, duration_ms) before
        comparison so that re-runs don't cause false mismatches.
        """
        expected_calls = self._strip_volatile(expected.get("tool_calls", []))
        actual_calls = self._strip_volatile(actual.get("tool_calls", []))

        if expected_calls == actual_calls:
            return None

        lines = []
        max_len = max(len(expected_calls), len(actual_calls))

        for i in range(max_len):
            exp = expected_calls[i] if i < len(expected_calls) else None
            act = actual_calls[i] if i < len(actual_calls) else None

            if exp is None:
                lines.append(f"[green]+ Call {i}: {act['name']} (NEW)[/green]")
            elif act is None:
                lines.append(f"[red]- Call {i}: {exp['name']} (MISSING)[/red]")
            elif exp != act:
                lines.append(f"[yellow]~ Call {i}: {exp['name']}[/yellow]")
                lines.extend(self._diff_call(exp, act, i))
            else:
                lines.append(f"[dim]  Call {i}: {exp['name']} (unchanged)[/dim]")

        return "\n".join(lines)

    def _diff_call(
        self,
        expected: dict[str, Any],
        actual: dict[str, Any],
        idx: int,
    ) -> list[str]:
        """Generate detailed diff for a single call."""
        lines = []

        if expected.get("name") != actual.get("name"):
            lines.append(f"    [red]name: {expected.get('name')} -> {actual.get('name')}[/red]")

        exp_args = expected.get("args", {})
        act_args = actual.get("args", {})

        for key in set(exp_args.keys()) | set(act_args.keys()):
            exp_val = exp_args.get(key, "<missing>")
            act_val = act_args.get(key, "<missing>")

            if exp_val != act_val:
                lines.append(f"    [red]args.{key}: {exp_val} -> {act_val}[/red]")

        return lines

    @staticmethod
    def _strip_volatile(calls: list[dict]) -> list[dict]:
        """Strip non-deterministic fields from tool call dicts for comparison.

        Fields like timestamp and duration_ms change on every run and should
        not cause snapshot mismatches.
        """
        volatile_keys = {"timestamp", "duration_ms"}
        return [{k: v for k, v in call.items() if k not in volatile_keys} for call in calls]

    def list_snapshots(self) -> list[Path]:
        """List all snapshots."""
        return list(self.snapshot_dir.glob("*.json"))

    def update_all(self, traces: dict[str, AgentTrace]) -> list[Path]:
        """Update all snapshots."""
        saved = []
        for name, trace in traces.items():
            path = self.save(name, trace)
            saved.append(path)
        return saved


def print_snapshot_diff(mismatch: SnapshotMismatch) -> None:
    """Print a colored snapshot diff."""
    text = Text()
    text.append("Snapshot Mismatch\n", style="bold red")
    text.append(mismatch.message + "\n\n", style="red")

    if mismatch.diff:
        panel = Panel(
            mismatch.diff,
            title="Detailed Diff",
            border_style="red",
        )
        console.print(panel)
    else:
        console.print("[dim]No detailed diff available[/dim]")

    console.print(
        f"\n[dim]Expected {len(mismatch.expected)} calls, got {len(mismatch.actual)}[/dim]"
    )
