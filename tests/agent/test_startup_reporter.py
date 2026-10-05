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
