"""CLI for agentspec."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.panel import Panel

from agentspec import __version__

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="AgentSpec")
def cli() -> None:
    """AgentSpec — deterministic testing for AI agents."""
    pass


@cli.command()
@click.argument("test_path", required=False, default=".")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
@click.option("--snapshot-update", is_flag=True, help="Update all snapshots")
@click.option("-k", "--keyword", help="Only run tests matching keyword")
@click.option("--adapter", type=click.Choice(["openai", "anthropic", "langchain"]), help="Default adapter")
@click.option("--no-persist", is_flag=True, help="Disable run log persistence (for sensitive environments)")
@click.option("-o", "--output", "output_path", help="Export results to JSONL file (for CI artifacts)")
def run(
    test_path: str,
    verbose: bool,
    snapshot_update: bool,
    keyword: str | None,
    adapter: str | None,
    no_persist: bool,
    output_path: str | None,
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

    if no_persist:
        os.environ["AGENTCONTRACT_NO_PERSIST"] = "1"
        console.print("[dim]Run log persistence disabled[/dim]")

    # Add our plugin
    cmd.extend(["-p", "agentspec.pytest_plugin"])

    console.print(f"[dim]Running: {' '.join(cmd)}[/dim]")
    console.print()

    result = subprocess.run(cmd, cwd=os.getcwd())

    # Export results if --output specified
    if output_path and not no_persist:
        import shutil
        from agentspec.storage import RunLogger
        logger = RunLogger()
        logs = logger.list_logs()
        if logs:
            latest = logs[-1]
            shutil.copy2(str(latest), output_path)
            console.print(f"[green]Results exported to {output_path}[/green]")
        else:
            console.print("[yellow]No run logs to export[/yellow]")

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
        "agentspec.pytest_plugin",
        "--snapshot-update",
    ]

    os.environ["AGENTCONTRACT_UPDATE_SNAPSHOTS"] = "1"

    console.print("[yellow]Updating all snapshots...[/yellow]")
    result = subprocess.run(cmd, cwd=os.getcwd())
    sys.exit(result.returncode)


@snapshot_cmd.command(name="list")
def snapshot_list() -> None:
    """List all saved snapshots."""
    from agentspec.snapshot import SnapshotManager

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
    from agentspec.snapshot import SnapshotManager

    mgr = SnapshotManager()
    snapshots = mgr.list_snapshots()

    for snap in snapshots:
        snap.unlink()

    console.print(f"[green]Deleted {len(snapshots)} snapshots[/green]")


@cli.command()
@click.argument("output_path", required=False, default=".")
def init(output_path: str) -> None:
    """Initialize a new AgentSpec project.

    Creates example test file and directory structure.
    """
    target = Path(output_path)

    # Create directories
    (target / "tests").mkdir(parents=True, exist_ok=True)
    (target / ".agentcontract" / "snapshots").mkdir(parents=True, exist_ok=True)

    # Create example test file
    example_test = target / "tests" / "example_contract.py"
    if not example_test.exists():
        example_test.write_text('''"""Example agent contract test — run with: agentspec run"""

from agentspec import contract, ContractRunner


def search_flights(destination: str) -> dict:
    """Simulated search tool."""
    return {"flights": [{"id": "FL001", "price": 299}]}


def book_flight(flight_id: str) -> dict:
    """Simulated booking tool."""
    return {"booking_id": f"BK-{flight_id}", "status": "confirmed"}


@contract("example_booking")
def test_flight_booking():
    """A working contract test with real tool call interception."""
    runner = ContractRunner()

    def mock_agent(input_text: str, interceptor=None, **kwargs):
        # Wrap tools so calls are automatically recorded
        wrapped_search = interceptor.wrap_tool(search_flights, "search_flights")
        wrapped_book = interceptor.wrap_tool(book_flight, "book_flight")

        # Agent logic
        results = wrapped_search(destination="NYC")
        booking = wrapped_book(flight_id="FL001")
        return f"Booked {booking['booking_id']}"

    result = runner.run(agent=mock_agent, input="Book a flight to NYC")

    # Deterministic assertions
    result.must_call("search_flights")
    result.must_call("book_flight").after("search_flights")
    result.must_call("search_flights").with_args(destination="NYC")
    result.must_not_call("cancel_booking")
    result.tool_call_count("search_flights").exactly(1)
''')

    # Create conftest.py
    conftest = target / "tests" / "conftest.py"
    if not conftest.exists():
        conftest.write_text("""\"\"\"pytest configuration.\"\"\"

pytest_plugins = ["agentspec.pytest_plugin"]
""")

    console.print(Panel(
        f"[green]Initialized AgentSpec project in {target.absolute()}[/green]\n\n"
        f"Next steps:\n"
        f"  1. Write tests in {target / 'tests'}/\n"
        f"  2. Run with: [cyan]agentspec run[/cyan]\n"
        f"  3. See {example_test.name} for an example",
        title="AgentSpec init",
    ))


@cli.command()
@click.option("--port", default=8080, help="Port to serve the dashboard on")
@click.option("--host", default="127.0.0.1", help="Host to bind to")
def ui(port: int, host: str) -> None:
    """Launch the AgentSpec Trace Visualizer dashboard."""
    import http.server
    import socketserver
    import json
    from agentspec.snapshot import SnapshotManager
    
    # Path to dashboard build
    local_dist = Path(__file__).parent.parent / "dashboard" / "dist"
    packaged_dist = Path(__file__).parent / "ui_dist"
    
    if packaged_dist.exists():
        dist_dir = packaged_dist
    elif local_dist.exists():
        dist_dir = local_dist
    else:
        console.print("[red]Error: Dashboard assets not found. Please build the dashboard.[/red]")
        sys.exit(1)
        
    class DashboardHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(dist_dir), **kwargs)
            
        def do_GET(self):
            if self.path == '/api/snapshots':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.end_headers()
                
                # Fetch snapshots
                mgr = SnapshotManager()
                snaps = []
                for snap_path in mgr.list_snapshots():
                    try:
                        with open(snap_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            snaps.append({
                                'id': snap_path.stem,
                                'name': snap_path.stem,
                                'filename': snap_path.name,
                                'path': str(snap_path),
                                'trace': data
                            })
                    except Exception:
                        pass
                        
                # Sort by start_time descending
                snaps.sort(key=lambda x: x.get('trace', {}).get('start_time', 0), reverse=True)
                
                self.wfile.write(json.dumps(snaps).encode())
                return
                
            return super().do_GET()
            
    # To prevent 'Address already in use' errors
    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.TCPServer((host, port), DashboardHandler) as httpd:
        console.print(Panel(
            f"[bold green]AgentSpec Trace Visualizer[/bold green]\n\n"
            f"🚀 Server running on [cyan]http://{host}:{port}[/cyan]\n"
            f"📂 Serving from [dim]{dist_dir}[/dim]\n\n"
            f"Press Ctrl+C to stop.",
            title="Dashboard",
        ))
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            console.print("\nShutting down.")
            sys.exit(0)


if __name__ == "__main__":
    cli()
