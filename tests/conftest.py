"""pytest configuration for agentcontract tests."""

import pytest
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

pytest_plugins = ["agentcontract.pytest_plugin"]
