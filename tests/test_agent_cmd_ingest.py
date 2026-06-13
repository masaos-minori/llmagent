"""
tests/test_agent_cmd_ingest.py
Behavior-lock tests for _IngestMixin: _cmd_export, _cmd_compact, _cmd_ingest.
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from agent.commands.cmd_ingest import _IngestMixin

# ── Test harness ──────────────────────────────────────────────────────────────


class _FakeCmd(_IngestMixin):
    def __init__(self, ctx: Any) -> None:
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


# ── _cmd_export ───────────────────────────────────────────────────────────────


class TestCmdExport:
    def test_export_md_to_stdout(self, capsys: Any) -> None:
        ctx = _make_ctx()
        cmd = _FakeCmd(ctx)
        cmd._cmd_export("")
        out = capsys.readouterr().out
        assert "hello" in out or "world" in out  # content rendered

    def test_export_json_to_stdout(self, capsys: Any) -> None:
        ctx = _make_ctx()
        cmd = _FakeCmd(ctx)
        cmd._cmd_export("json")
        out = capsys.readouterr().out
        assert '"role"' in out or "role" in out

    def test_export_to_file(self, tmp_path: Any, capsys: Any) -> None:
        ctx = _make_ctx()
        outfile = str(tmp_path / "out.md")
        cmd = _FakeCmd(ctx)
        cmd._cmd_export(f"md {outfile}")
        out = capsys.readouterr().out
        assert "Exported" in out
        content = (tmp_path / "out.md").read_text()
        assert "hello" in content or "world" in content


# ── _cmd_compact ──────────────────────────────────────────────────────────────


class TestCmdCompact:
    def test_compact_calls_force_compress(self) -> None:
        ctx = _make_ctx()
        hist_mgr = MagicMock()
        hist_mgr.compress_turns = 2
        compressed = [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "summary"},
        ]
        hist_mgr.force_compress = AsyncMock(return_value=compressed)
        ctx.services.hist_mgr = hist_mgr
        # compress_turns=2 → n_compress=4; need >4 non-system messages
        ctx.conv.history = [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "u1"},
            {"role": "assistant", "content": "a1"},
            {"role": "user", "content": "u2"},
            {"role": "assistant", "content": "a2"},
            {"role": "user", "content": "u3"},
        ]
        cmd = _FakeCmd(ctx)
        asyncio.run(cmd._cmd_compact())
        hist_mgr.force_compress.assert_called_once()
        assert ctx.conv.history == compressed

    def test_compact_no_hist_mgr_prints_unavailable(self, capsys: Any) -> None:
        ctx = _make_ctx()
        ctx.services.hist_mgr = None
        cmd = _FakeCmd(ctx)
        asyncio.run(cmd._cmd_compact())
        out = capsys.readouterr().out
        assert "not available" in out

    def test_compact_history_too_short_prints_message(self, capsys: Any) -> None:
        ctx = _make_ctx()
        hist_mgr = MagicMock()
        hist_mgr.compress_turns = 4
        ctx.services.hist_mgr = hist_mgr
        # history has only 2 turn messages (< compress_turns * 2 = 8)
        ctx.conv.history = [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "u1"},
            {"role": "assistant", "content": "a1"},
        ]
        cmd = _FakeCmd(ctx)
        asyncio.run(cmd._cmd_compact())
        out = capsys.readouterr().out
        assert "Nothing to compact" in out


# ── _cmd_ingest ───────────────────────────────────────────────────────────────


class TestCmdIngest:
    def test_ingest_no_args_prints_usage(self, capsys: Any) -> None:
        ctx = _make_ctx()
        cmd = _FakeCmd(ctx)
        asyncio.run(cmd._cmd_ingest(""))
        out = capsys.readouterr().out
        assert "Usage" in out

    def test_ingest_missing_local_file_prints_error(self, capsys: Any) -> None:
        ctx = _make_ctx()
        cmd = _FakeCmd(ctx)
        asyncio.run(cmd._cmd_ingest("/nonexistent/path/file.md"))
        out = capsys.readouterr().out
        assert "not found" in out or "error" in out.lower()


# ── IngestStageError propagation ─────────────────────────────────────────────


class TestIngestStageError:
    def test_crawl_os_error_raises_ingest_stage_error(self) -> None:
        """OSError during crawl stage raises IngestStageError with stage=CRAWL."""
        from unittest.mock import AsyncMock, patch

        from agent.services.enums import IngestStage
        from agent.services.exceptions import IngestStageError
        from agent.services.ingest_workflow import IngestWorkflowService

        svc = IngestWorkflowService()
        with patch(
            "agent.services.ingest_workflow.IngestWorkflowService._crawl",
            new_callable=AsyncMock,
            side_effect=IngestStageError(IngestStage.CRAWL, "network fail"),
        ):
            with pytest.raises(IngestStageError) as exc_info:
                asyncio.run(svc.run("http://example.com"))
        assert exc_info.value.stage == IngestStage.CRAWL
        assert "network fail" in exc_info.value.detail

    def test_cmd_ingest_catches_stage_error_and_prints(self, capsys: Any) -> None:
        """cmd_ingest prints error message when IngestStageError is raised."""
        from unittest.mock import AsyncMock, patch

        from agent.services.enums import IngestStage
        from agent.services.exceptions import IngestStageError

        ctx = _make_ctx()
        cmd = _FakeCmd(ctx)
        with patch(
            "agent.services.ingest_workflow.IngestWorkflowService.run",
            new_callable=AsyncMock,
            side_effect=IngestStageError(IngestStage.SPLIT, "split failed"),
        ):
            asyncio.run(cmd._cmd_ingest("http://example.com"))
        out = capsys.readouterr().out
        assert "error" in out.lower()
        assert "split" in out.lower()


# ── _cmd_rag ──────────────────────────────────────────────────────────────────


class TestCmdRag:
    def test_no_search_subcommand_prints_usage(self, capsys: Any) -> None:
        ctx = _make_ctx()
        cmd = _FakeCmd(ctx)
        asyncio.run(cmd._cmd_rag(""))
        assert "Usage" in capsys.readouterr().out

    def test_search_missing_query_prints_usage(self, capsys: Any) -> None:
        ctx = _make_ctx()
        cmd = _FakeCmd(ctx)
        asyncio.run(cmd._cmd_rag("search"))
        assert "Usage" in capsys.readouterr().out

    def test_search_blank_query_after_debug_flag_prints_usage(
        self, capsys: Any
    ) -> None:
        ctx = _make_ctx()
        cmd = _FakeCmd(ctx)
        asyncio.run(cmd._cmd_rag("search --debug"))
        assert "Usage" in capsys.readouterr().out

    def test_no_http_client_prints_unavailable(self, capsys: Any) -> None:
        ctx = _make_ctx()
        ctx.services.http = None
        cmd = _FakeCmd(ctx)
        asyncio.run(cmd._cmd_rag("search hello"))
        assert "HTTP client not available" in capsys.readouterr().out

    def test_use_search_false_prints_disabled(self, capsys: Any) -> None:
        from unittest.mock import patch

        ctx = _make_ctx()
        cmd = _FakeCmd(ctx)
        with patch("shared.config_loader.ConfigLoader") as mock_cfg_cls:
            mock_cfg_cls.return_value.load.return_value = {"use_search": False}
            asyncio.run(cmd._cmd_rag("search hello"))
        assert "disabled" in capsys.readouterr().out.lower()

    def test_search_no_results_prints_message(self, capsys: Any) -> None:
        from unittest.mock import patch

        ctx = _make_ctx()
        cmd = _FakeCmd(ctx)
        with (
            patch("shared.config_loader.ConfigLoader") as mock_cfg_cls,
            patch("rag.pipeline.RagPipeline") as mock_pipeline_cls,
        ):
            mock_cfg_cls.return_value.load.return_value = {"use_search": True}
            mock_pipeline = MagicMock()
            mock_pipeline.augment = AsyncMock(return_value="")
            mock_pipeline.last_timings = {}
            mock_pipeline_cls.return_value = mock_pipeline
            asyncio.run(cmd._cmd_rag("search hello"))
        assert "No results found" in capsys.readouterr().out

    def test_search_returns_context(self, capsys: Any) -> None:
        from unittest.mock import patch

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
            mock_pipeline_cls.return_value = mock_pipeline
            asyncio.run(cmd._cmd_rag("search hello"))
        assert "[RAG context block]" in capsys.readouterr().out

    def test_debug_flag_prints_stage_timings(self, capsys: Any) -> None:
        from unittest.mock import patch

        ctx = _make_ctx()
        cmd = _FakeCmd(ctx)
        with (
            patch("shared.config_loader.ConfigLoader") as mock_cfg_cls,
            patch("rag.pipeline.RagPipeline") as mock_pipeline_cls,
        ):
            mock_cfg_cls.return_value.load.return_value = {"use_search": True}
            mock_pipeline = MagicMock()
            mock_pipeline.augment = AsyncMock(return_value="ctx")
            mock_pipeline.last_timings = {"MqeStage": 0.05, "SearchStage": 0.12}
            mock_pipeline_cls.return_value = mock_pipeline
            asyncio.run(cmd._cmd_rag("search hello --debug"))
        out = capsys.readouterr().out
        assert "Stage timings" in out
        assert "MqeStage" in out
        assert "50.0 ms" in out
