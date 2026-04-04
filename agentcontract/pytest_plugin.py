"""pytest plugin for agentcontract."""

from __future__ import annotations

import pytest
from typing import Any, Generator

from rich.console import Console
from rich.table import Table
from rich.text import Text

from agentcontract.contract import ContractRunner
from agentcontract.interceptor import AgentTrace
from agentcontract.snapshot import SnapshotManager

console = Console()


class ContractReport:
    """Collects and reports contract test results."""

    def __init__(self) -> None:
        self.results: list[dict[str, Any]] = []
        self.passed = 0
        self.failed = 0

    def add_result(
        self,
        name: str,
        passed: bool,
        tool_calls: int = 0,
        assertions: int = 0,
        error: str | None = None,
    ) -> None:
        """Add a test result."""
        self.results.append({
            "name": name,
            "passed": passed,
            "tool_calls": tool_calls,
            "assertions": assertions,
            "error": error,
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1

    def print_summary(self) -> None:
        """Print beautiful summary table."""
        if not self.results:
            return

        total = len(self.results)

        table = Table(title="agentcontract summary")
        table.add_column("Status", style="bold")
        table.add_column("Contract", style="cyan")
        table.add_column("Metrics", style="dim")

        for r in self.results:
            status = "PASSED" if r["passed"] else "FAILED"
            status_style = "green" if r["passed"] else "red"
            metrics = f"{r['tool_calls']} tool calls · {r['assertions']} assertions"
            if r["error"]:
                metrics += f"\n[red]{r['error']}[/red]"

            table.add_row(
                f"[{status_style}]{status}[/{status_style}]",
                r["name"],
                metrics,
            )

        console.print()
        console.print(table)

        # Summary line
        color = "green" if self.failed == 0 else "red"
        summary = f"{total} contracts run · {self.passed} passed · {self.failed} failed"
        console.print(f"[bold {color}]{summary}[/bold {color}]")
        console.print()


# Global report instance
_report = ContractReport()


def pytest_configure(config: Any) -> None:
    """Configure pytest with our marker."""
    config.addinivalue_line(
        "markers",
        "contract(name): mark test as an agent contract test"
    )


@pytest.fixture
def contract_runner() -> Generator[ContractRunner, None, None]:
    """Provide a ContractRunner for tests."""
    runner = ContractRunner()
    yield runner


@pytest.fixture
def agent_trace(contract_runner: ContractRunner) -> AgentTrace:
    """Provide access to the agent execution trace."""
    return contract_runner.get_trace()


@pytest.fixture
def snapshot_manager() -> Generator[SnapshotManager, None, None]:
    """Provide a SnapshotManager for tests."""
    mgr = SnapshotManager()
    yield mgr


def pytest_runtest_setup(item: Any) -> None:
    """Setup for contract tests."""
    marker = item.get_closest_marker("contract")
    if marker:
        # Mark as contract test for reporting
        item._is_contract_test = True


def pytest_runtest_makereport(item: Any, call: Any) -> None:
    """Process contract test results."""
    if not hasattr(item, "_is_contract_test") and not getattr(item, "_contract_name", None):
        return

    if call.when == "call":
        name = getattr(item, "_contract_name", item.name)
        passed = call.excinfo is None

        # Try to extract metrics from the result if available
        tool_calls = 0
        assertions = 0
        error_msg = None

        if not passed and call.excinfo:
            error_msg = str(call.excinfo.value)

        _report.add_result(
            name=name,
            passed=passed,
            tool_calls=tool_calls,
            assertions=assertions,
            error=error_msg,
        )


def pytest_sessionfinish(session: Any, exitstatus: Any) -> None:
    """Print contract summary at end of test run."""
    _report.print_summary()


# Hook for contract decorator integration
def pytest_collection_modifyitems(session: Any, config: Any, items: list[Any]) -> None:
    """Modify collected items to detect contract tests."""
    for item in items:
        # Check if test was decorated with @contract
        if hasattr(item, "obj") and hasattr(item.obj, "_is_contract"):
            item._is_contract_test = True
            item._contract_name = getattr(item.obj, "_contract_name", item.name)
            # Add marker
            item.add_marker(pytest.mark.contract)
