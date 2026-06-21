"""tests/test_cmd_rag_refiner_hint.py
Verifies that _cmd_rag() emits the [warn] refiner fallback hint line when appropriate.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.commands.cmd_ingest import _IngestMixin

# ── Test harness ──────────────────────────────────────────────────────────────


class _FakeCmd(_IngestMixin):
    def __init__(self, ctx: object) -> None:
        self._ctx = ctx


def _make_ctx() -> MagicMock:
    ctx = MagicMock()
    ctx.conv.history = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "world"},
    ]
    ctx.services.hist_mgr = None
    return ctx


# ── _cmd_rag refiner fallback hint ────────────────────────────────────────────


class TestCmdRagRefinerHint:
    def test_refiner_fallback_hint_written(self, capsys: object) -> None:
        """When Refiner status=fallback, hint line is written."""
        ctx = _make_ctx()
        cmd = _FakeCmd(ctx)
        with (
            patch("shared.config_loader.ConfigLoader") as mock_cfg_cls,
            patch("rag.pipeline.RagPipeline") as mock_pipeline_cls,
        ):
            mock_cfg_cls.return_value.load.return_value = {"use_search": True}
            mock_pipeline = MagicMock()
            mock_pipeline.augment = AsyncMock(return_value="[RAG context block]")
            mock_pipeline.last_timings = {}
            mock_pipeline.get_diagnostics = MagicMock(return_value={})
            mock_pipeline.last_stage_results = [
                {
                    "stage_name": "Refiner",
                    "status": "fallback",
                    "elapsed_seconds": 0.1,
                    "fallback_reason": "refiner_returned_empty",
                }
            ]
            mock_pipeline_cls.return_value = mock_pipeline
            import asyncio

            asyncio.run(cmd._cmd_rag("search hello"))
        out = capsys.readouterr().out
        assert "[warn] refiner fallback" in out
        assert "refiner_returned_empty" in out

    def test_no_hint_when_refiner_succeeded(self, capsys: object) -> None:
        """When Refiner status=success, no hint line is written."""
        ctx = _make_ctx()
        cmd = _FakeCmd(ctx)
        with (
            patch("shared.config_loader.ConfigLoader") as mock_cfg_cls,
            patch("rag.pipeline.RagPipeline") as mock_pipeline_cls,
        ):
            mock_cfg_cls.return_value.load.return_value = {"use_search": True}
            mock_pipeline = MagicMock()
            mock_pipeline.augment = AsyncMock(return_value="[RAG context block]")
            mock_pipeline.last_timings = {}
            mock_pipeline.get_diagnostics = MagicMock(return_value={})
            mock_pipeline.last_stage_results = [
                {
                    "stage_name": "Refiner",
                    "status": "success",
                    "elapsed_seconds": 0.1,
                    "fallback_reason": None,
                }
            ]
            mock_pipeline_cls.return_value = mock_pipeline
            import asyncio

            asyncio.run(cmd._cmd_rag("search hello"))
        out = capsys.readouterr().out
        assert "[warn] refiner fallback" not in out

    def test_no_hint_when_refiner_not_used(self, capsys: object) -> None:
        """When no Refiner entry in last_stage_results, no hint is written."""
        ctx = _make_ctx()
        cmd = _FakeCmd(ctx)
        with (
            patch("shared.config_loader.ConfigLoader") as mock_cfg_cls,
            patch("rag.pipeline.RagPipeline") as mock_pipeline_cls,
        ):
            mock_cfg_cls.return_value.load.return_value = {"use_search": True}
            mock_pipeline = MagicMock()
            mock_pipeline.augment = AsyncMock(return_value="[RAG context block]")
            mock_pipeline.last_timings = {}
            mock_pipeline.get_diagnostics = MagicMock(return_value={})
            mock_pipeline.last_stage_results = [
                {
                    "stage_name": "Search",
                    "status": "success",
                    "elapsed_seconds": 0.1,
                    "fallback_reason": None,
                }
            ]
            mock_pipeline_cls.return_value = mock_pipeline
            import asyncio

            asyncio.run(cmd._cmd_rag("search hello"))
        out = capsys.readouterr().out
        assert "[warn] refiner fallback" not in out

    def test_fallback_reason_in_hint(self, capsys: object) -> None:
        """Fallback reason string appears verbatim in the hint line."""
        ctx = _make_ctx()
        cmd = _FakeCmd(ctx)
        with (
            patch("shared.config_loader.ConfigLoader") as mock_cfg_cls,
            patch("rag.pipeline.RagPipeline") as mock_pipeline_cls,
        ):
            mock_cfg_cls.return_value.load.return_value = {"use_search": True}
            mock_pipeline = MagicMock()
            mock_pipeline.augment = AsyncMock(return_value="[RAG context block]")
            mock_pipeline.last_timings = {}
            mock_pipeline.get_diagnostics = MagicMock(return_value={})
            reason = "refiner_exception: HTTPStatusError 429"
            mock_pipeline.last_stage_results = [
                {
                    "stage_name": "Refiner",
                    "status": "fallback",
                    "elapsed_seconds": 0.1,
                    "fallback_reason": reason,
                }
            ]
            mock_pipeline_cls.return_value = mock_pipeline
            import asyncio

            asyncio.run(cmd._cmd_rag("search hello"))
        out = capsys.readouterr().out
        assert "[warn] refiner fallback" in out
        assert reason in out
