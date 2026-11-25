"""tests/mcp_servers/test_dry_run_contract.py — Cross-family preview contract.

A preview runs the handler and writes nothing: no ledger row, no owner lease, no
in-process overlay entry, so the same logical key can still execute for real
afterwards. The contract is wording-independent — servers express dry-run output
in three different styles — so it is parametrized over tool family and wording
(mcpai005 REQ-004/REQ-010).
"""

from __future__ import annotations

import sqlite3
from collections.abc import Awaitable, Callable, Iterator
from typing import Any

import pytest
from mcp_servers.dispatch import _duplicate_cache, dispatch_tool
from mcp_servers.execution_context import ExecutionContext
from shared.execution_mode import ExecutionMode
from shared.mcp_dedup import DedupRow, DedupStore
from shared.tool_constants import GITHUB_WRITE_TOOLS

# One entry per tool family and dry-run wording style.
FAMILIES: tuple[tuple[str, str], ...] = (
    ("git_commit", "bracket"),
    ("write_file", "prefix"),
    (sorted(GITHUB_WRITE_TOOLS)[0], "json"),
)

WORDINGS: dict[str, str] = {
    "bracket": "[DRY RUN] {tool}: no change",
    "prefix": "Dry-run: {tool} [no change]",
    "json": '{"dry_run": true, "tool": "{{tool}}"}',
}

# A read-only tool for the keyless half of the contract.
READ_TOOL = "read_text_file"

Handler = Callable[[dict[str, Any]], Awaitable[str]]


def _stub(output: list[str], calls: list[str]) -> Handler:
    """Handler stub whose wording the test can change without changing behavior."""

    async def handler(args: dict[str, Any]) -> str:
        calls.append(str(args.get("tool", "")))
        return output[0]

    return handler


def _wording(style: str, tool: str) -> str:
    """Render one wording style for a tool. The JSON style carries literal braces,
    so the placeholder is substituted by replacement rather than format-field
    interpolation."""
    return WORDINGS[style].replace("{tool}", tool)


def _context(tool: str, key: str, mode: ExecutionMode) -> ExecutionContext:
    return ExecutionContext(
        request_id="req-1",
        session_id="sess-1",
        idempotency_key=key,
        execution_mode=mode,
    )


def _ledger_history(store: DedupStore) -> list[tuple[int, str]]:
    """(attempt_number, outcome) rows written for this store: the ledger-side evidence."""
    conn = sqlite3.connect(store.db_path)
    try:
        return [
            (int(row[0]), str(row[1]))
            for row in conn.execute(
                "SELECT attempt_number, outcome FROM call_attempt_history"
            )
        ]
    finally:
        conn.close()


class TestDryRunContract:
    """The preview outcome is the same for every tool family and every wording style."""

    @pytest.fixture()
    def store(self, tmp_path: Any, monkeypatch: Any) -> Iterator[dict[str, Any]]:
        """Durable store over a per-test database, closed in teardown."""
        import mcp_servers.dispatch as dispatch_mod
        from shared.mcp_dedup import DedupStoreConfig as _Config

        db_path = str(tmp_path / "mcp_dedup.sqlite")
        opened = DedupStore(db_path)
        config = _Config(db_path=db_path)
        _duplicate_cache.clear()
        monkeypatch.setattr(dispatch_mod, "_dedup_store", opened)
        monkeypatch.setattr(dispatch_mod, "_dedup_config", config)
        monkeypatch.setattr(dispatch_mod, "_dedup_disabled", False)
        monkeypatch.setattr(dispatch_mod, "_purge_done", False)
        monkeypatch.setattr(
            dispatch_mod,
            "_tool_retry_policies",
            {tool: "same_logical_call_only" for tool, _ in FAMILIES},
        )
        state: dict[str, Any] = {"store": opened, "db_path": db_path}
        yield state
        opened.close()
        _duplicate_cache.clear()

    @pytest.mark.parametrize(("tool", "wording"), FAMILIES)
    @pytest.mark.asyncio
    async def test_preview_runs_the_handler_and_writes_no_state(
        self, store: dict[str, Any], tool: str, wording: str
    ) -> None:
        """AC-4: a preview is reported as a preview and leaves the ledger and the
        overlay cache empty."""
        calls: list[str] = []
        output = [_wording(wording, tool)]
        res = await dispatch_tool(
            {tool: _stub(output, calls)},
            tool,
            {"tool": tool},
            context=_context(tool, "key-1", "preview"),
        )

        assert not res.is_error
        assert res.output == output[0]
        assert res.execution_mode == "preview"
        assert res.side_effect_applied is False
        assert res.dedup_state == ""
        assert len(calls) == 1
        assert len(_duplicate_cache) == 0
        assert _ledger_history(store["store"]) == []
        assert store["store"].get_execution("key-1") is None

    @pytest.mark.parametrize(("tool", "wording"), FAMILIES)
    @pytest.mark.asyncio
    async def test_preview_then_real_execution_with_the_same_key(
        self, store: dict[str, Any], tool: str, wording: str
    ) -> None:
        """The preview does not consume the key: the applied call runs and the row
        reaches the terminal `completed` state."""
        calls: list[str] = []
        output = [_wording(wording, tool)]
        table = {tool: _stub(output, calls)}

        preview = await dispatch_tool(
            table, tool, {"tool": tool}, context=_context(tool, "key-1", "preview")
        )
        applied = await dispatch_tool(
            table, tool, {"tool": tool}, context=_context(tool, "key-1", "applied")
        )

        assert preview.execution_mode == "preview"
        assert applied.execution_mode == "applied"
        assert applied.side_effect_applied is True
        assert not applied.is_error
        assert len(calls) == 2
        row = store["store"].get_execution("key-1")
        assert isinstance(row, DedupRow)
        assert row.status == "completed"
        assert _ledger_history(store["store"]) == [(1, "attempt"), (1, "completed")]

    @pytest.mark.parametrize(("tool", "wording"), FAMILIES)
    @pytest.mark.asyncio
    async def test_wording_does_not_change_the_outcome(
        self, store: dict[str, Any], tool: str, wording: str
    ) -> None:
        """Wording regression: the same contract holds when the stub's output text
        is replaced by another style, so no server depends on parsing it."""
        calls: list[str] = []
        output = [_wording(wording, tool)]
        table = {tool: _stub(output, calls)}

        first = await dispatch_tool(
            table, tool, {"tool": tool}, context=_context(tool, "key-1", "preview")
        )
        output[0] = (
            _wording("json", tool) if wording != "json" else _wording("bracket", tool)
        )
        second = await dispatch_tool(
            table, tool, {"tool": tool}, context=_context(tool, "key-2", "preview")
        )

        for res in (first, second):
            assert not res.is_error
            assert res.execution_mode == "preview"
            assert res.side_effect_applied is False
        assert len(calls) == 2
        assert len(_duplicate_cache) == 0
        assert _ledger_history(store["store"]) == []

    @pytest.mark.asyncio
    async def test_keyless_side_effecting_call_is_rejected(
        self, store: dict[str, Any]
    ) -> None:
        """A side-effecting call without a key is refused before the handler runs,
        and the refusal is reported as no_op."""
        calls: list[str] = []
        res = await dispatch_tool(
            {"write_file": _stub(["written"], calls)},
            "write_file",
            {"tool": "write_file"},
            context=_context("write_file", "", "applied"),
        )

        assert res.is_error
        assert res.error_type == "idempotency_key_required"
        assert res.execution_mode == "no_op"
        assert res.side_effect_applied is False
        assert calls == []
        assert _ledger_history(store["store"]) == []

    @pytest.mark.asyncio
    async def test_read_only_keyless_call_executes(self, store: dict[str, Any]) -> None:
        """The key requirement is scoped to side-effecting tools: a read-only call
        runs without one and still writes no state."""
        calls: list[str] = []
        res = await dispatch_tool(
            {READ_TOOL: _stub(["contents"], calls)},
            READ_TOOL,
            {"tool": READ_TOOL},
            context=_context(READ_TOOL, "", "applied"),
        )

        assert not res.is_error
        assert res.execution_mode == "applied"
        assert res.side_effect_applied is False
        assert len(calls) == 1
        assert _ledger_history(store["store"]) == []

    @pytest.mark.asyncio
    async def test_replay_returns_no_op(self, store: dict[str, Any]) -> None:
        """A completed call served from the durable store does not run the handler
        again: the replay is reported as no_op with the served outcome."""
        calls: list[str] = []
        table = {"write_file": _stub(["written"], calls)}

        first = await dispatch_tool(
            table,
            "write_file",
            {"tool": "write_file"},
            context=_context("write_file", "key-1", "applied"),
        )
        replay = await dispatch_tool(
            table,
            "write_file",
            {"tool": "write_file"},
            context=_context("write_file", "key-1", "applied"),
        )

        assert first.execution_mode == "applied"
        assert replay.execution_mode == "no_op"
        assert replay.side_effect_applied is False
        assert replay.dedup_state == "duplicate_hit"
        assert replay.output == first.output
        assert len(calls) == 1
