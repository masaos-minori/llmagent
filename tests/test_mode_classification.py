"""tests/test_mode_classification.py

Unit tests for agent.mode_classification.classify_and_inject_mode().
"""

from __future__ import annotations

from unittest.mock import MagicMock

from agent.mode_classification import classify_and_inject_mode
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
    ctx.conv.history = []
    return ctx


def _ephemeral_msgs(ctx: MagicMock) -> list[dict]:
    return [m for m in ctx.conv.history if m.get("_ephemeral")]


class TestClassifyAndInjectMode:
    def test_mdq_query_with_tools_available_injects_mdq_hint(self) -> None:
        ctx = _make_ctx(mdq_rag_mode="mdq", mdq_tool_names=["search_docs"])
        classify_and_inject_mode("show me the headings", ctx)

        hints = _ephemeral_msgs(ctx)
        assert len(hints) == 1
        assert hints[0]["role"] == "system"
        assert "MDQ tools" in hints[0]["content"]

    def test_mdq_query_without_tools_available_falls_back_to_rag_hint(self) -> None:
        ctx = _make_ctx(mdq_rag_mode="mdq", mdq_tool_names=None)
        classify_and_inject_mode("show me the headings", ctx)

        hints = _ephemeral_msgs(ctx)
        assert len(hints) == 1
        assert "RAG tools" in hints[0]["content"]

    def test_rag_mode_injects_rag_hint(self) -> None:
        ctx = _make_ctx(mdq_rag_mode="rag")
        classify_and_inject_mode("what is the capital of France?", ctx)

        hints = _ephemeral_msgs(ctx)
        assert len(hints) == 1
        assert "RAG tools" in hints[0]["content"]

    def test_config_override_takes_precedence_over_query_content(self) -> None:
        """A query with MDQ-style keywords still gets the RAG hint when
        mdq_rag_mode is explicitly configured to "rag"."""
        ctx = _make_ctx(mdq_rag_mode="rag", mdq_tool_names=["search_docs"])
        classify_and_inject_mode("show me the table of contents", ctx)

        hints = _ephemeral_msgs(ctx)
        assert len(hints) == 1
        assert "RAG tools" in hints[0]["content"]

    def test_injected_hint_is_marked_ephemeral_not_persisted(self) -> None:
        ctx = _make_ctx(mdq_rag_mode="rag")
        classify_and_inject_mode("hello", ctx)

        assert len(ctx.conv.history) == 1
        assert ctx.conv.history[0]["_ephemeral"] is True

    def test_repeated_calls_without_clearing_accumulate(self) -> None:
        """classify_and_inject_mode() itself has no dedup memory -- calling it
        twice without an intervening clear (the orchestrator's
        _clear_previous_turn_ephemeral_messages(), tested in
        tests/test_orchestrator.py::TestEphemeralMessageLifecycle) appends a
        second hint. The no-duplication guarantee is an orchestrator-level
        invariant, not a property of this function in isolation.
        """
        ctx = _make_ctx(mdq_rag_mode="rag")
        classify_and_inject_mode("first turn", ctx)
        classify_and_inject_mode("second turn", ctx)

        assert len(_ephemeral_msgs(ctx)) == 2
