"""pytest configuration for agentcontract tests."""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Note: pytest plugin is auto-registered via pyproject.toml [project.entry-points."pytest11"]
# Do NOT add pytest_plugins = ["agentcontract.pytest_plugin"] here — it causes double-registration.
