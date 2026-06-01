"""tests/test_cmd_rag.py
Unit tests for _RagMixin slash commands — specifically /rag mcp and /rag status display.
"""

from __future__ import annotations

import io
from contextlib import redirect_stdout
from unittest.mock import MagicMock

import pytest
from agent.commands.cmd_rag import _RagMixin


def _make_mixin(
    *,
    use_rag_mcp: bool = False,
    use_search: bool = True,
    use_mqe: bool = True,
    use_rrf: bool = True,
    use_rerank: bool = True,
) -> _RagMixin:
    mixin = _RagMixin()
    cfg = MagicMock()
    cfg.use_rag_mcp = use_rag_mcp
    cfg.use_search = use_search
    cfg.use_mqe = use_mqe
    cfg.use_rrf = use_rrf
    cfg.use_rerank = use_rerank
    ctx = MagicMock()
    ctx.cfg = cfg
    mixin._ctx = ctx
    return mixin


class TestRagMcpToggle:
    @pytest.mark.asyncio
    async def test_rag_mcp_on_sets_flag(self) -> None:
        mixin = _make_mixin(use_rag_mcp=False)
        await mixin._cmd_rag("mcp on")
        assert mixin._ctx.cfg.use_rag_mcp is True

    @pytest.mark.asyncio
    async def test_rag_mcp_off_clears_flag(self) -> None:
        mixin = _make_mixin(use_rag_mcp=True)
        await mixin._cmd_rag("mcp off")
        assert mixin._ctx.cfg.use_rag_mcp is False

    @pytest.mark.asyncio
    async def test_rag_mcp_missing_value_prints_usage(self) -> None:
        mixin = _make_mixin()
        buf = io.StringIO()
        with redirect_stdout(buf):
            await mixin._cmd_rag("mcp")
        assert "Usage" in buf.getvalue()


class TestRagStatusDisplay:
    @pytest.mark.asyncio
    async def test_status_shows_mcp_label_when_enabled(self) -> None:
        mixin = _make_mixin(use_rag_mcp=True)
        buf = io.StringIO()
        with redirect_stdout(buf):
            await mixin._cmd_rag("")
        output = buf.getvalue()
        assert "(MCP)" in output
        assert "use_rag_mcp" in output

    @pytest.mark.asyncio
    async def test_status_shows_in_process_label_when_disabled(self) -> None:
        mixin = _make_mixin(use_rag_mcp=False)
        buf = io.StringIO()
        with redirect_stdout(buf):
            await mixin._cmd_rag("")
        output = buf.getvalue()
        assert "(in-process)" in output
