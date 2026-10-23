"""scripts/mcp_servers/git/__init__.py"""

import importlib
from types import ModuleType

__all__ = ["server"]

_ALIASES = {"server": "git_server"}


def __getattr__(name: str) -> ModuleType:
    """Import a submodule alias on first access so importing the package runs no server code."""
    target = _ALIASES.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = importlib.import_module(f"{__name__}.{target}")
    globals()[name] = module
    return module
