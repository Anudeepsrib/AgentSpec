"""CLI for agentcontract."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.panel import Panel

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="agentcontract")
def cli() -> None:
    """agentcontract — deterministic testing for AI agents."""
    pass


@cli.command()
@click.argument("test_path", required=False, default=".")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
@click.option("--snapshot-update", is_flag=True, help="Update all snapshots")
@click.option("-k", "--keyword", help="Only run tests matching keyword")
@click.option("--adapter", type=click.Choice(["openai", "anthropic", "langchain"]), help="Default adapter")
def run(
    test_path: str,
    verbose: bool,
    snapshot_update: bool,
    keyword: str | None,
    adapter: str | None,
) -> None:
    """Run agent contract tests.

    TEST_PATH can be a test file, directory, or pytest node ID.
    """
    import subprocess

    cmd = [sys.executable, "-m", "pytest", test_path]

    if verbose:
        cmd.append("-v")

    if keyword:
        cmd.extend(["-k", keyword])

    # Set snapshot update environment variable
    if snapshot_update:
        os.environ["AGENTCONTRACT_UPDATE_SNAPSHOTS"] = "1"
        console.print("[yellow]Snapshot update mode enabled[/yellow]")

    if adapter:
        os.environ["AGENTCONTRACT_ADAPTER"] = adapter

    # Add our plugin
    cmd.extend(["-p", "agentcontract.pytest_plugin"])

    console.print(f"[dim]Running: {' '.join(cmd)}[/dim]")
    console.print()

    result = subprocess.run(cmd, cwd=os.getcwd())

    sys.exit(result.returncode)


@cli.group(name="snapshot")
def snapshot_cmd() -> None:
    """Manage test snapshots."""
    pass


@snapshot_cmd.command(name="update")
@click.argument("test_path", required=False, default=".")
@click.option("--all", "update_all", is_flag=True, help="Update all snapshots without prompt")
def snapshot_update(test_path: str, update_all: bool) -> None:
    """Update snapshots for failing tests."""
    import subprocess

    if not update_all:
        confirm = click.confirm("This will update all snapshots. Continue?")
        if not confirm:
            console.print("Aborted.")
            return

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        test_path,
        "-p",
        "agentcontract.pytest_plugin",
        "--snapshot-update",
    ]

    os.environ["AGENTCONTRACT_UPDATE_SNAPSHOTS"] = "1"

    console.print("[yellow]Updating all snapshots...[/yellow]")
    result = subprocess.run(cmd, cwd=os.getcwd())
    sys.exit(result.returncode)


@snapshot_cmd.command(name="list")
def snapshot_list() -> None:
    """List all saved snapshots."""
    from agentcontract.snapshot import SnapshotManager

    mgr = SnapshotManager()
    snapshots = mgr.list_snapshots()

    if not snapshots:
        console.print("[dim]No snapshots found in .agentcontract/snapshots/[/dim]")
        return

    console.print(f"[bold]Found {len(snapshots)} snapshots:[/bold]\n")
    for snap in sorted(snapshots):
        size = snap.stat().st_size
        console.print(f"  • {snap.name} ({size} bytes)")


@snapshot_cmd.command(name="clean")
@click.confirmation_option(prompt="Delete all snapshots?")
def snapshot_clean() -> None:
    """Remove all snapshots."""
    from agentcontract.snapshot import SnapshotManager

    mgr = SnapshotManager()
    snapshots = mgr.list_snapshots()

    for snap in snapshots:
        snap.unlink()

    console.print(f"[green]Deleted {len(snapshots)} snapshots[/green]")


@cli.command()
@click.argument("output_path", required=False, default=".")
def init(output_path: str) -> None:
    """Initialize a new agentcontract project.

    Creates example test file and directory structure.
    """
    target = Path(output_path)

    # Create directories
    (target / "tests").mkdir(parents=True, exist_ok=True)
    (target / ".agentcontract" / "snapshots").mkdir(parents=True, exist_ok=True)

    # Create example test file
    example_test = target / "tests" / "example_contract.py"
    if not example_test.exists():
        example_test.write_text("""\"\"\"Example agent contract test.\"\"\"

import pytest
from agentcontract import contract, ContractRunner


@contract("example_booking")
def test_example_flight_booking():
    \"\"\"Example test showing contract assertions.\"\"\"

    def mock_agent(input_text: str, **kwargs) -> dict:
        # Simulated agent behavior
        return {
            "tool_calls": [
                {"name": "search_flights", "args": {"destination": "NYC"}},
                {"name": "book_flight", "args": {"flight_id": "123"}},
            ],
            "output": "Flight booked successfully!"
        }

    runner = ContractRunner()
    result = runner.run(agent=mock_agent, input="Book a flight to NYC")

    # Assertions go here once you have real tool capture
    # result.must_call("search_flights")
    # result.must_call("book_flight").after("search_flights")

    pass
""")

    # Create conftest.py
    conftest = target / "tests" / "conftest.py"
    if not conftest.exists():
        conftest.write_text("""\"\"\"pytest configuration.\"\"\"

pytest_plugins = ["agentcontract.pytest_plugin"]
""")

    console.print(Panel(
        f"[green]Initialized agentcontract project in {target.absolute()}[/green]\n\n"
        f"Next steps:\n"
        f"  1. Write tests in {target / 'tests'}/\n"
        f"  2. Run with: [cyan]agentcontract run[/cyan]\n"
        f"  3. See {example_test.name} for an example",
        title="agentcontract init",
    ))


if __name__ == "__main__":
    cli()
