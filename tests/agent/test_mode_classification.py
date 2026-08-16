"""tests/test_mode_classification.py

Unit tests for agent.mode_classification.classify_and_inject_mode().
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from agent.context import ConversationState
from agent.mdq_rag_classifier import MdqRagMode
from agent.mode_classification import _mode_hint, classify_and_inject_mode
from shared.mcp_config import McpServerConfig, StartupMode, TransportType


def _make_ctx(
    *, mdq_rag_mode: str | None = None, mdq_tool_names: list[str] | None = None
) -> MagicMock:
    ctx = MagicMock()
    ctx.cfg.mdq_rag_mode = mdq_rag_mode
    server_cfg = McpServerConfig(
        transport=TransportType.HTTP,
        url="http://127.0.0.1:19200",
        tool_names=mdq_tool_names or [],
        startup_mode=StartupMode.PERSISTENT,
    )
    ctx.cfg.mcp.mcp_servers = {"mdq": server_cfg} if mdq_tool_names else {}
    ctx.conv = ConversationState()
    return ctx


def _ephemeral_msgs(ctx: MagicMock) -> list[dict]:
    return [m for m in ctx.conv.history if m.get("_ephemeral")]


class TestClassifyAndInjectMode:
    @pytest.mark.asyncio
    async def test_mdq_query_with_tools_available_injects_mdq_hint(self) -> None:
        ctx = _make_ctx(mdq_rag_mode="mdq", mdq_tool_names=["search_docs"])
        await classify_and_inject_mode("show me the structure", ctx)

        hints = _ephemeral_msgs(ctx)
        assert len(hints) == 1
        assert hints[0]["role"] == "system"
        assert "MDQ tools" in hints[0]["content"]

    @pytest.mark.asyncio
    async def test_mdq_query_without_tools_available_falls_back_to_rag_hint(
        self,
    ) -> None:
        ctx = _make_ctx(mdq_rag_mode="mdq", mdq_tool_names=None)
        await classify_and_inject_mode("show me the headings", ctx)

        hints = _ephemeral_msgs(ctx)
        assert len(hints) == 1
        assert "RAG tools" in hints[0]["content"]

    @pytest.mark.asyncio
    async def test_rag_mode_injects_rag_hint(self) -> None:
        ctx = _make_ctx(mdq_rag_mode="rag")
        await classify_and_inject_mode("what is the capital of France?", ctx)

        hints = _ephemeral_msgs(ctx)
        assert len(hints) == 1
        assert "RAG tools" in hints[0]["content"]

    @pytest.mark.asyncio
    async def test_config_override_takes_precedence_over_query_content(self) -> None:
        """A query with MDQ-style keywords still gets the RAG hint when
        mdq_rag_mode is explicitly configured to "rag"."""
        ctx = _make_ctx(mdq_rag_mode="rag", mdq_tool_names=["search_docs"])
        await classify_and_inject_mode("show me the table of contents", ctx)

        hints = _ephemeral_msgs(ctx)
        assert len(hints) == 1
        assert "RAG tools" in hints[0]["content"]

    @pytest.mark.asyncio
    async def test_injected_hint_is_marked_ephemeral_not_persisted(self) -> None:
        ctx = _make_ctx(mdq_rag_mode="rag")
        await classify_and_inject_mode("hello", ctx)

        assert len(ctx.conv.history) == 1
        assert ctx.conv.history[0]["_ephemeral"] is True

    @pytest.mark.asyncio
    async def test_hint_routed_through_append_message_source_not_persisted(
        self,
    ) -> None:
        """Regression: classify_and_inject_mode() routes its ephemeral hint
        through ConversationState.append_message(source="cmd_handler"), which
        authorizes "_ephemeral" for this message. The stored message must
        keep "_ephemeral" intact (not sanitized away) and must never carry a
        "source" key (validation-only metadata, never persisted)."""
        ctx = _make_ctx(mdq_rag_mode="rag")
        await classify_and_inject_mode("hello", ctx)

        assert ctx.conv.history == [
            {
                "role": "system",
                "content": _mode_hint(MdqRagMode.RAG),
                "_ephemeral": True,
            }
        ]
        assert "source" not in ctx.conv.history[0]

    @pytest.mark.asyncio
    async def test_repeated_calls_without_clearing_accumulate(self) -> None:
        """classify_and_inject_mode() itself has no dedup memory -- calling it
        twice without an intervening clear (the orchestrator's
        _clear_previous_turn_ephemeral_messages(), tested in
        tests/test_orchestrator.py::TestEphemeralMessageLifecycle) appends a
        second hint. The no-duplication guarantee is an orchestrator-level
        invariant, not a property of this function in isolation.
        """
        ctx = _make_ctx(mdq_rag_mode="rag")
        await classify_and_inject_mode("first turn", ctx)
        await classify_and_inject_mode("second turn", ctx)

        assert len(_ephemeral_msgs(ctx)) == 2
