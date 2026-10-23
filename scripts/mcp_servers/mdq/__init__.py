"""scripts/mcp_servers/mdq/__init__.py — MDQ MCP server package."""

from __future__ import annotations

import importlib
from types import ModuleType

__all__ = ["models", "server", "service", "tools"]

_ALIASES = {
    "models": "mdq_models",
    "server": "mdq_server",
    "service": "mdq_service",
    "tools": "mdq_tools",
}


def __getattr__(name: str) -> ModuleType:
    """Import a submodule alias on first access so importing the package runs no server code."""
    target = _ALIASES.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = importlib.import_module(f"{__name__}.{target}")
    globals()[name] = module
    return module
