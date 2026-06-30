"""tests/test_cmd_mdq.py
Unit tests for agent.commands.cmd_mdq._MdqMixin command handlers.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from agent.commands.cmd_mdq import _MdqMixin
from mcp.dispatch import DispatchResult


class _Ctx:
    """Minimal stub for AgentContext with services.tools."""

    services: Any

    def __init__(self, *, tools_available: bool = True) -> None:
        if tools_available:
            self.services = MagicMock()
            self.services.tools = MagicMock()
            self.services.tools.execute = AsyncMock(
                return_value=DispatchResult(is_error=False, output="ok")
            )
        else:
            self.services = None


class _Mdq(_MdqMixin):
    def __init__(self, ctx: _Ctx) -> None:
        self._ctx = ctx


def _ctx_with_result(output: str, is_error: bool = False) -> _Ctx:
    ctx = _Ctx()
    ctx.services.tools.execute = AsyncMock(
        return_value=DispatchResult(is_error=is_error, output=output)
    )
    return ctx


# ── /mdq status ───────────────────────────────────────────────────────────────


class TestMdqStatusCommand:
    @pytest.mark.asyncio
    async def test_calls_stats_tool(self, capsys: pytest.CaptureFixture) -> None:
        ctx = _ctx_with_result("chunks: 42")
        mdq = _Mdq(ctx)
        await mdq._cmd_mdq_status()
        ctx.services.tools.execute.assert_called_once_with("stats", {})

    @pytest.mark.asyncio
    async def test_output_contains_result(self, capsys: pytest.CaptureFixture) -> None:
        ctx = _ctx_with_result("chunks: 42")
        mdq = _Mdq(ctx)
        await mdq._cmd_mdq_status()
        out = capsys.readouterr().out
        assert "chunks: 42" in out

    @pytest.mark.asyncio
    async def test_no_services_shows_error(self, capsys: pytest.CaptureFixture) -> None:
        ctx = _Ctx(tools_available=False)
        mdq = _Mdq(ctx)
        await mdq._cmd_mdq_status()
        out = capsys.readouterr().out
        assert "not available" in out


# ── /mdq index ────────────────────────────────────────────────────────────────


class TestMdqIndexCommand:
    @pytest.mark.asyncio
    async def test_calls_index_paths(self, capsys: pytest.CaptureFixture) -> None:
        ctx = _ctx_with_result("indexed 3 files")
        mdq = _Mdq(ctx)
        await mdq._cmd_mdq_index("/docs")
        ctx.services.tools.execute.assert_called_once_with(
            "index_paths", {"paths": ["/docs"]}
        )

    @pytest.mark.asyncio
    async def test_force_flag_passed(self) -> None:
        ctx = _ctx_with_result("indexed 3 files")
        mdq = _Mdq(ctx)
        await mdq._cmd_mdq_index("/docs --force")
        ctx.services.tools.execute.assert_called_once_with(
            "index_paths", {"paths": ["/docs"], "force": True}
        )

    @pytest.mark.asyncio
    async def test_empty_args_shows_usage(self, capsys: pytest.CaptureFixture) -> None:
        ctx = _ctx_with_result("")
        mdq = _Mdq(ctx)
        await mdq._cmd_mdq_index("")
        out = capsys.readouterr().out
        assert "Usage" in out
        ctx.services.tools.execute.assert_not_called()


# ── /mdq refresh ──────────────────────────────────────────────────────────────


class TestMdqRefreshCommand:
    @pytest.mark.asyncio
    async def test_calls_refresh_index(self) -> None:
        ctx = _ctx_with_result("refreshed")
        mdq = _Mdq(ctx)
        await mdq._cmd_mdq_refresh("/docs")
        ctx.services.tools.execute.assert_called_once_with(
            "refresh_index", {"paths": ["/docs"]}
        )

    @pytest.mark.asyncio
    async def test_force_flag_passed(self) -> None:
        ctx = _ctx_with_result("refreshed")
        mdq = _Mdq(ctx)
        await mdq._cmd_mdq_refresh("/docs --force")
        ctx.services.tools.execute.assert_called_once_with(
            "refresh_index", {"paths": ["/docs"], "force": True}
        )

    @pytest.mark.asyncio
    async def test_empty_args_shows_usage(self, capsys: pytest.CaptureFixture) -> None:
        ctx = _ctx_with_result("")
        mdq = _Mdq(ctx)
        await mdq._cmd_mdq_refresh("")
        out = capsys.readouterr().out
        assert "Usage" in out
        ctx.services.tools.execute.assert_not_called()


# ── /mdq search ───────────────────────────────────────────────────────────────


class TestMdqSearchCommand:
    @pytest.mark.asyncio
    async def test_calls_search_docs(self) -> None:
        ctx = _ctx_with_result("1 result")
        mdq = _Mdq(ctx)
        await mdq._cmd_mdq_search("myquery")
        ctx.services.tools.execute.assert_called_once_with(
            "search_docs", {"query": "myquery"}
        )

    @pytest.mark.asyncio
    async def test_limit_flag_passed(self) -> None:
        ctx = _ctx_with_result("results")
        mdq = _Mdq(ctx)
        await mdq._cmd_mdq_search("myquery --limit=5")
        call_args = ctx.services.tools.execute.call_args
        assert call_args[0][0] == "search_docs"
        assert call_args[0][1]["limit"] == 5

    @pytest.mark.asyncio
    async def test_empty_args_shows_usage(self, capsys: pytest.CaptureFixture) -> None:
        ctx = _ctx_with_result("")
        mdq = _Mdq(ctx)
        await mdq._cmd_mdq_search("")
        out = capsys.readouterr().out
        assert "Usage" in out
        ctx.services.tools.execute.assert_not_called()


# ── /mdq outline ──────────────────────────────────────────────────────────────


class TestMdqOutlineCommand:
    @pytest.mark.asyncio
    async def test_calls_outline(self) -> None:
        ctx = _ctx_with_result("# Section\n## Sub")
        mdq = _Mdq(ctx)
        await mdq._cmd_mdq_outline("/docs/file.md")
        ctx.services.tools.execute.assert_called_once_with(
            "outline", {"path": "/docs/file.md"}
        )

    @pytest.mark.asyncio
    async def test_output_contains_result(self, capsys: pytest.CaptureFixture) -> None:
        ctx = _ctx_with_result("# Section\n## Sub")
        mdq = _Mdq(ctx)
        await mdq._cmd_mdq_outline("/docs/file.md")
        out = capsys.readouterr().out
        assert "# Section" in out

    @pytest.mark.asyncio
    async def test_empty_args_shows_usage(self, capsys: pytest.CaptureFixture) -> None:
        ctx = _ctx_with_result("")
        mdq = _Mdq(ctx)
        await mdq._cmd_mdq_outline("")
        out = capsys.readouterr().out
        assert "Usage" in out
        ctx.services.tools.execute.assert_not_called()


# ── /mdq get ──────────────────────────────────────────────────────────────────


class TestMdqGetCommand:
    @pytest.mark.asyncio
    async def test_calls_get_chunk(self) -> None:
        ctx = _ctx_with_result("chunk content")
        mdq = _Mdq(ctx)
        await mdq._cmd_mdq_get("chunk123")
        ctx.services.tools.execute.assert_called_once_with(
            "get_chunk", {"chunk_id": "chunk123"}
        )

    @pytest.mark.asyncio
    async def test_with_neighbors_flag(self) -> None:
        ctx = _ctx_with_result("chunk content with neighbors")
        mdq = _Mdq(ctx)
        await mdq._cmd_mdq_get("chunk123 --with-neighbors")
        ctx.services.tools.execute.assert_called_once_with(
            "get_chunk", {"chunk_id": "chunk123", "with_neighbors": True}
        )

    @pytest.mark.asyncio
    async def test_empty_args_shows_usage(self, capsys: pytest.CaptureFixture) -> None:
        ctx = _ctx_with_result("")
        mdq = _Mdq(ctx)
        await mdq._cmd_mdq_get("")
        out = capsys.readouterr().out
        assert "Usage" in out
        ctx.services.tools.execute.assert_not_called()


# ── /mdq grep ─────────────────────────────────────────────────────────────────


class TestMdqGrepCommand:
    @pytest.mark.asyncio
    async def test_calls_grep_docs(self) -> None:
        ctx = _ctx_with_result("2 matches")
        mdq = _Mdq(ctx)
        await mdq._cmd_mdq_grep("def foo")
        ctx.services.tools.execute.assert_called_once_with(
            "grep_docs", {"pattern": "def"}
        )

    @pytest.mark.asyncio
    async def test_path_flag_passed(self) -> None:
        ctx = _ctx_with_result("matches")
        mdq = _Mdq(ctx)
        await mdq._cmd_mdq_grep("pattern --path=/docs")
        call_args = ctx.services.tools.execute.call_args
        assert call_args[0][0] == "grep_docs"
        assert call_args[0][1]["paths"] == ["/docs"]

    @pytest.mark.asyncio
    async def test_empty_args_shows_usage(self, capsys: pytest.CaptureFixture) -> None:
        ctx = _ctx_with_result("")
        mdq = _Mdq(ctx)
        await mdq._cmd_mdq_grep("")
        out = capsys.readouterr().out
        assert "Usage" in out
        ctx.services.tools.execute.assert_not_called()


# ── Error handling ────────────────────────────────────────────────────────────


class TestMdqErrorHandling:
    @pytest.mark.asyncio
    async def test_is_error_true_shows_error(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        ctx = _ctx_with_result("index not found", is_error=True)
        mdq = _Mdq(ctx)
        await mdq._cmd_mdq_status()
        out = capsys.readouterr().out
        assert "error" in out
        assert "index not found" in out

    @pytest.mark.asyncio
    async def test_no_services_shows_not_available(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        ctx = _Ctx(tools_available=False)
        mdq = _Mdq(ctx)
        await mdq._cmd_mdq_search("query")
        out = capsys.readouterr().out
        assert "not available" in out

    @pytest.mark.asyncio
    async def test_index_error_shows_error(self, capsys: pytest.CaptureFixture) -> None:
        ctx = _ctx_with_result("permission denied", is_error=True)
        mdq = _Mdq(ctx)
        await mdq._cmd_mdq_index("/restricted")
        out = capsys.readouterr().out
        assert "error" in out
        assert "permission denied" in out
