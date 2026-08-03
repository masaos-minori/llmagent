"""
tests/test_import_smoke.py
Regression lock: shared.tool_executor, agent.factory, agent.context, and
agent.repository_gateway must import without raising. Prevents silent
regression of the NameError('RuntimeToolRegistry' undefined) startup crash
caused by a missing `from __future__ import annotations` in
scripts/shared/tool_executor.py.
"""

from __future__ import annotations


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
