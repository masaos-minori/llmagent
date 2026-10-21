"""
tests/test_import_smoke.py
Regression lock: shared.tool_executor, agent.factory, agent.context, and
agent.repository_gateway must import without raising. Prevents silent
regression of the NameError('RuntimeToolRegistry' undefined) startup crash
caused by a missing `from __future__ import annotations` in
scripts/shared/tool_executor.py.

It also locks the removal of the component re-exports from the `agent` package:
the twelve component names must not resolve on `agent`, and importing a submodule
must not load `agent.repl` through a package-level import.
"""

from __future__ import annotations

import os
import subprocess  # nosec B404 — fixed command string run in a child interpreter, no external input
import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"

_REMOVED_REEXPORTS = (
    "AuditEventEmitter",
    "BgTaskMonitor",
    "ConversationStateManager",
    "LlmTurnExecutor",
    "AgentREPL",
    "ReplInputLoop",
    "ResourceShutdownCoordinator",
    "SessionPersister",
    "SignalHandler",
    "StartupBanner",
    "WalCheckpointManager",
    "WorkflowEngineAdapter",
)


def test_import_shared_tool_executor() -> None:
    import shared.tool_executor  # noqa: F401 — imported to verify module resolves cleanly


def test_import_agent_factory() -> None:
    from agent import factory  # noqa: F401 — imported to verify module resolves cleanly


def test_import_agent_context() -> None:
    from agent import context  # noqa: F401 — imported to verify module resolves cleanly


def test_import_agent_repository_gateway() -> None:
    from agent import (
        repository_gateway,  # noqa: F401 — imported to verify module resolves cleanly
    )


@pytest.mark.parametrize("name", _REMOVED_REEXPORTS)
def test_agent_package_does_not_reexport_components(name: str) -> None:
    import agent

    assert not hasattr(agent, name), f"agent.{name} was re-exported again"
    assert name not in getattr(agent, "__all__", ())


def test_importing_agent_context_does_not_load_agent_repl() -> None:
    # A child interpreter is required: other tests in this process may already have
    # imported agent.repl, which would hide a package-level import side effect.
    code = (
        "import sys; import agent.context; "
        "sys.exit(1 if 'agent.repl' in sys.modules else 0)"
    )
    result = subprocess.run(  # noqa: S603 — fixed argv and code string, no external input
        [sys.executable, "-I", "-c", code],
        env={**os.environ, "PYTHONPATH": str(_SCRIPTS_DIR)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"importing agent.context loaded agent.repl: {result.stderr}"
    )
