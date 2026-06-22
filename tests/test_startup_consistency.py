"""tests/test_startup_consistency.py
Verifies that _check_services() emits write_warning on RAG inconsistency.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


def _make_orchestrator():
    """Return a minimal StartupOrchestrator with mocked _view."""
    from agent.startup import StartupOrchestrator

    orch = StartupOrchestrator.__new__(StartupOrchestrator)
    orch._view = MagicMock()
    orch._cfg = MagicMock()
    orch._ctx = MagicMock()
    return orch


@pytest.mark.asyncio
async def test_write_warning_on_inconsistency():
    """Inconsistent index -> write_warning called with each issue."""
    orch = _make_orchestrator()
    # Patch other checks to avoid real dependencies
    with (
        patch("agent.startup.RagMaintenanceService") as mock_svc_cls,
        patch("agent.startup.audit_security_defaults"),
        patch("agent.startup.check_readiness") as mock_readiness,
        patch("agent.startup.check_tool_definitions_runtime") as mock_tools,
    ):
        mock_svc = MagicMock()
        mock_svc.consistency.return_value = MagicMock(
            is_consistent=False, issues=["fts_gap=3", "orphan_vec=1"]
        )
        mock_svc_cls.return_value = mock_svc

        mock_readiness.return_value = MagicMock(warning_messages=lambda: [])
        mock_tools.return_value = MagicMock(warning_messages=lambda: [])

        # Call only the consistency portion; other checks are mocked
        orch._check_embedding_dimensions = MagicMock()
        await orch._check_services()

    calls = [str(c) for c in orch._view.write_warning.call_args_list]
    assert any("fts_gap=3" in c for c in calls)


@pytest.mark.asyncio
async def test_no_warning_on_consistent():
    """Consistent index -> write_warning not called for RAG."""
    orch = _make_orchestrator()
    with (
        patch("agent.startup.RagMaintenanceService") as mock_svc_cls,
        patch("agent.startup.audit_security_defaults"),
        patch("agent.startup.check_readiness") as mock_readiness,
        patch("agent.startup.check_tool_definitions_runtime") as mock_tools,
    ):
        mock_svc = MagicMock()
        mock_svc.consistency.return_value = MagicMock(is_consistent=True, issues=[])
        mock_svc_cls.return_value = mock_svc

        mock_readiness.return_value = MagicMock(warning_messages=lambda: [])
        mock_tools.return_value = MagicMock(warning_messages=lambda: [])

        orch._check_embedding_dimensions = MagicMock()
        await orch._check_services()

    # write_warning may be called for other checks; check that RAG issue was not
    calls = [str(c) for c in orch._view.write_warning.call_args_list]
    assert not any("[RAG]" in c for c in calls)


@pytest.mark.asyncio
async def test_no_crash_on_exception():
    """Exception from consistency check -> no crash; logged at DEBUG only."""
    orch = _make_orchestrator()
    with (
        patch("agent.startup.RagMaintenanceService") as mock_svc_cls,
        patch("agent.startup.audit_security_defaults"),
        patch("agent.startup.check_readiness") as mock_readiness,
        patch("agent.startup.check_tool_definitions_runtime") as mock_tools,
    ):
        mock_svc = MagicMock()
        mock_svc.consistency.side_effect = FileNotFoundError("rag.sqlite not found")
        mock_svc_cls.return_value = mock_svc

        mock_readiness.return_value = MagicMock(warning_messages=lambda: [])
        mock_tools.return_value = MagicMock(warning_messages=lambda: [])

        orch._check_embedding_dimensions = MagicMock()
        # Should not raise
        await orch._check_services()

    # No write_warning for RAG since it was skipped silently
    calls = [str(c) for c in orch._view.write_warning.call_args_list]
    assert not any("[RAG]" in c for c in calls)
