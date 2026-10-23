"""scripts/mcp_servers/cicd/__init__.py — CI/CD MCP server package (GitHub Actions backend)."""

from __future__ import annotations

import importlib
from types import ModuleType

__all__ = ["server"]

_ALIASES = {"server": "cicd_server"}


def __getattr__(name: str) -> ModuleType:
    """Import a submodule alias on first access so importing the package runs no server code."""
    target = _ALIASES.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = importlib.import_module(f"{__name__}.{target}")
    globals()[name] = module
    return module
