"""Regression tests for ReadinessReporter.report_readiness().

Locks the current behaviour after the ReadinessReporter refactor (bdd64049):
report_readiness(pipeline) aggregates pipeline outcomes and emits a single
"Readiness Summary:" warning. It returns None (never a dict) and performs no
defensive null handling — the invariant is enforced at access time by the
AgentContext.services_required property, which raises RuntimeError.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from agent.shared.health_models import StartupCheckStatus
from agent.startup_reporter import ReadinessReporter


def _empty_pipeline() -> MagicMock:
    pipeline = MagicMock()
    pipeline.outcomes = []
    return pipeline


class _CtxWithRaisingServices:
    """Context whose services_required property enforces the invariant."""

    def __init__(self) -> None:
        self.cfg = SimpleNamespace(mcp=SimpleNamespace(mcp_servers={}))

    @property
    def services_required(self) -> object:
        raise RuntimeError(
            "AgentContext.services not initialized — call build_agent_context() first"
        )


def test_report_readiness_emits_readiness_summary() -> None:
    """REQ-003: report_readiness aggregates the pipeline and warns once."""
    ctx = MagicMock()
    ctx.cfg.mcp.mcp_servers = {}
    ctx.services_required = MagicMock()
    ctx.services_required.runtime_tools.unavailable_servers = frozenset()

    view = MagicMock()
    reporter = ReadinessReporter(ctx, view)

    reporter.report_readiness(_empty_pipeline())

    assert view.write_warning.call_count == 1
    message = str(view.write_warning.call_args[0][0])
    assert "Readiness Summary:" in message
    assert "Service readiness:" in message


def test_report_readiness_propagates_when_services_uninitialized() -> None:
    """REQ-003: invariant enforced at access time — RuntimeError propagates."""
    ctx = _CtxWithRaisingServices()
    view = MagicMock()
    reporter = ReadinessReporter(ctx, view)

    with pytest.raises(RuntimeError, match="not initialized"):
        reporter.report_readiness(_empty_pipeline())


def _readiness_message_for_rag(status: StartupCheckStatus) -> str:
    """Render the readiness summary for a pipeline with one RAG outcome."""
    ctx = MagicMock()
    ctx.cfg.mcp.mcp_servers = {}
    ctx.services_required = MagicMock()
    ctx.services_required.runtime_tools.unavailable_servers = frozenset()
    pipeline = MagicMock()
    pipeline.outcomes = [SimpleNamespace(source="rag_consistency", status=status)]
    view = MagicMock()

    ReadinessReporter(ctx, view).report_readiness(pipeline)

    return str(view.write_warning.call_args[0][0])


def _rag_line(message: str) -> str:
    return next(line for line in message.splitlines() if "RAG consistency:" in line)


def test_report_readiness_rag_line_shows_skipped_count() -> None:
    """REQ-001: a skipped RAG check is rendered with its skipped count."""
    line = _rag_line(_readiness_message_for_rag(StartupCheckStatus.SKIPPED))

    assert "1 skipped" in line
    assert "0 fatal, 0 warnings" in line


def test_report_readiness_rag_line_without_skip_shows_zero_skipped() -> None:
    """REQ-003: a non-skipped RAG check gains no spurious skipped count."""
    line = _rag_line(_readiness_message_for_rag(StartupCheckStatus.OK))

    assert line.startswith("  RAG consistency: OK")
    assert "0 skipped" in line
