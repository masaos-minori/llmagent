"""tests/agent/commands/test_command_modules_import.py

Import guard for every module under scripts/agent/commands/: a module that raises at
import time (for example an annotation that names a TYPE_CHECKING-only symbol) fails
here with its own test id instead of breaking the command registry import and every
test that reaches it.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

_COMMANDS_DIR = Path(__file__).resolve().parents[3] / "scripts" / "agent" / "commands"


def _module_names() -> list[str]:
    """Module names from the file system, so discovery never imports the package."""
    return sorted(p.stem for p in _COMMANDS_DIR.glob("*.py") if p.stem != "__init__")


def test_the_discovered_module_list_covers_the_registry_and_mcp_modules() -> None:
    names = _module_names()

    assert "cmd_mcp" in names
    assert "registry" in names
    assert len(names) >= 20


@pytest.mark.parametrize("name", _module_names())
def test_the_command_module_imports(name: str) -> None:
    module = importlib.import_module(f"agent.commands.{name}")

    assert module.__name__ == f"agent.commands.{name}"
