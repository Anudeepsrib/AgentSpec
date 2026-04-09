# agentcontract/__init__.py
# Deprecated: this package has been renamed to agentspec.
# This shim exists for backward compatibility only.
import warnings
warnings.warn(
    "Importing from 'agentcontract' is deprecated. "
    "Use 'from agentspec import ...' instead.",
    DeprecationWarning,
    stacklevel=2,
)
from agentspec import *  # noqa: F401, F403
