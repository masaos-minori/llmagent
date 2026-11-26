"""tests/test_mcp_dispatch.py
Unit tests for mcp/dispatch.py — dispatch_tool.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from dataclasses import replace
from typing import Any

import pytest
from mcp_servers.dispatch import (
    _IDEMPOTENCY_CACHE_MAX_ENTRIES,
    _IDEMPOTENCY_CACHE_TTL_SECONDS,
    _duplicate_cache,
    _is_side_effecting,
    dispatch_tool,
)
from mcp_servers.execution_context import ExecutionContext
from shared.execution_mode import ExecutionMode
from shared.mcp_dedup import DedupStoreError
from shared.tool_constants import ALL_SIDE_EFFECTING_TOOLS


def _ctx(key: str = "", mode: ExecutionMode = "applied") -> ExecutionContext:
    """The context a call site passes to dispatch_tool: the key and the mode.

    One helper keeps the mechanical rename from `idempotency_key=` to the context
    a single expression, so the mode is visible at every call site.
    """
    return ExecutionContext(
        request_id="",
        session_id="",
        idempotency_key=key,
        execution_mode=mode,
    )


def _attempt_history(store: Any) -> list[tuple[int, str, str | None]]:
    """(attempt_number, outcome, detail) rows from `call_attempt_history`: the
    ledger-side evidence the recovery gating must not fabricate (AC-3)."""
    conn = sqlite3.connect(store.db_path)
    try:
        return [
            (int(r[0]), str(r[1]), None if r[2] is None else str(r[2]))
            for r in conn.execute(
                "SELECT attempt_number, outcome, detail FROM call_attempt_history"
                " ORDER BY recorded_epoch, rowid"
            )
        ]
    finally:
        conn.close()


class TestDispatchTool:
    @pytest.mark.asyncio
    async def test_dispatches_to_handler(self) -> None:
        """Dispatch calls the correct handler."""

        async def handler(args: dict) -> str:
            return f"result:{args.get('x')}"

        res = await dispatch_tool({"my_tool": handler}, "my_tool", {"x": 123})
        assert not res.is_error
        assert res.output == "result:123"

    @pytest.mark.asyncio
    async def test_empty_tool_name_returns_error(self) -> None:
        """Empty tool name returns error."""
        res = await dispatch_tool({}, "", {})
        assert res.is_error
        assert "non-empty" in res.output

    @pytest.mark.asyncio
    async def test_non_string_tool_name_returns_error(self) -> None:
        """Non-string tool name returns error."""
        res = await dispatch_tool({}, 123, {})  # type: ignore[arg-type]
        assert res.is_error
        assert "non-empty" in res.output

    @pytest.mark.asyncio
    async def test_whitespace_tool_name_returns_error(self) -> None:
        """Whitespace-only tool name returns error."""
        res = await dispatch_tool({}, "   ", {})
        assert res.is_error
        assert "non-empty" in res.output

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error(self) -> None:
        """Unknown tool returns error."""

        async def known(a: dict) -> str:
            return ""

        res = await dispatch_tool({"known": known}, "unknown", {})
        assert res.is_error
        assert "Unknown tool" in res.output

    @pytest.mark.asyncio
    async def test_value_error_from_handler_returns_validation_error(self) -> None:
        """ValueError from handler returns validation error result."""

        async def handler(args: dict) -> str:
            raise ValueError("bad input")

        res = await dispatch_tool({"tool": handler}, "tool", {})
        assert res.is_error
        assert "Validation error" in res.output

    @pytest.mark.asyncio
    async def test_non_value_error_propagates(self) -> None:
        """Non-ValueError exceptions (runtime errors) propagate to the caller."""

        async def handler(args: dict) -> str:
            raise RuntimeError("internal failure")

        with pytest.raises(RuntimeError, match="internal failure"):
            await dispatch_tool({"tool": handler}, "tool", {})

    @pytest.mark.asyncio
    async def test_http_exception_propagates(self) -> None:
        """HTTP exceptions propagate to the caller (not swallowed)."""

        class FakeHTTPException(Exception):
            status_code = 403
            detail = "Forbidden"

        async def handler(args: dict) -> str:
            raise FakeHTTPException()

        with pytest.raises(FakeHTTPException):
            await dispatch_tool({"tool": handler}, "tool", {})


class TestDispatchIdempotencyCache:
    """Cache behavior of dispatch_tool() (REQ-001..REQ-004).

    Exercises the dedup path by dispatching a genuine side-effecting tool
    (``write_file``) with explicit ``idempotency_key`` values. Clears the
    module-level ``_duplicate_cache`` around each case to isolate them.
    """

    @pytest.fixture(autouse=True)
    def _clear_idem_cache(self, monkeypatch: Any) -> Iterator[None]:
        # Overlay-only isolation: the durable store is never opened in-process
        # here, which would turn these fixed-key cases into store hits. Disable
        # it explicitly, and inject the declared retry_policy these tools carry
        # so the degraded overlay path mirrors a configured bootstrap process.
        import mcp_servers.dispatch as dispatch_mod

        _duplicate_cache.clear()
        monkeypatch.setattr(dispatch_mod, "_dedup_store", None)
        monkeypatch.setattr(dispatch_mod, "_dedup_config", None)
        monkeypatch.setattr(dispatch_mod, "_dedup_disabled", True)
        monkeypatch.setattr(
            dispatch_mod,
            "_tool_retry_policies",
            {
                "write_file": "same_logical_call_only",
                "index_paths": "same_logical_call_only",
                "refresh_index": "same_logical_call_only",
            },
        )
        yield
        _duplicate_cache.clear()

    @staticmethod
    def _side_effecting_tool() -> str:
        name = "write_file"
        assert _is_side_effecting(name)
        return name

    @pytest.mark.asyncio
    async def test_keyless_side_effecting_call_is_rejected(self) -> None:
        """A side-effecting call without a key is refused before the handler runs
        and reports no_op (REQ-006)."""

        calls: list[int] = []

        async def handler(args: dict) -> str:
            calls.append(1)
            return "wrote"

        tool = self._side_effecting_tool()
        r = await dispatch_tool({tool: handler}, tool, {"p": "a"}, context=_ctx())
        assert r.is_error
        assert r.error_type == "idempotency_key_required"
        assert r.execution_mode == "no_op"
        assert r.side_effect_applied is False
        assert calls == []
        assert len(_duplicate_cache) == 0

    @pytest.mark.asyncio
    async def test_keyless_read_only_call_executes(self) -> None:
        """The key requirement is scoped to side-effecting tools: a keyless read-only
        call runs and writes no cache entry (REQ-006)."""

        calls: list[int] = []

        async def handler(args: dict) -> str:
            calls.append(1)
            return "contents"

        tool = "read_text_file"
        assert not _is_side_effecting(tool)
        r = await dispatch_tool({tool: handler}, tool, {"p": "a"}, context=_ctx())
        assert not r.is_error
        assert r.execution_mode == "applied"
        assert len(calls) == 1
        assert len(_duplicate_cache) == 0

    @pytest.mark.asyncio
    async def test_same_key_served_from_cache(self) -> None:
        """Same key + same tool + same args: handler runs once, second is cached (REQ-002)."""

        calls: list[int] = []

        async def handler(args: dict) -> str:
            calls.append(1)
            return "wrote"

        tool = self._side_effecting_tool()
        key = "same-key"
        r1 = await dispatch_tool({tool: handler}, tool, {"p": "a"}, context=_ctx(key))
        r2 = await dispatch_tool({tool: handler}, tool, {"p": "a"}, context=_ctx(key))
        assert not r1.is_error and not r2.is_error
        assert r1.output == r2.output == "wrote"
        assert len(calls) == 1  # executed once
        assert len(_duplicate_cache) == 1

    @pytest.mark.asyncio
    async def test_keyed_mdq_duplicate_is_deduplicated(self) -> None:
        """MDQ index_paths/refresh_index dedup via the canonical set (REQ-002)."""

        calls: list[int] = []

        async def handler(args: dict) -> str:
            calls.append(1)
            return "indexed"

        for tool in ("index_paths", "refresh_index"):
            assert _is_side_effecting(tool)
            key = f"mdq-key-{tool}"
            r1 = await dispatch_tool(
                {tool: handler}, tool, {"p": "a"}, context=_ctx(key)
            )
            r2 = await dispatch_tool(
                {tool: handler}, tool, {"p": "a"}, context=_ctx(key)
            )
            assert not r1.is_error and not r2.is_error
            assert r1.output == r2.output == "indexed"
        assert len(calls) == 2  # once per tool; both keyed duplicates served
        assert len(_duplicate_cache) == 2

    @pytest.mark.asyncio
    async def test_same_key_different_tool_rejected(self) -> None:
        """Same key reused for a different tool is rejected without a second execution (REQ-002)."""

        calls: list[int] = []

        async def handler(args: dict) -> str:
            calls.append(1)
            return "wrote"

        table = {"write_file": handler, "shell_run": handler}
        r1 = await dispatch_tool(table, "write_file", {"p": "a"}, context=_ctx("k"))
        r2 = await dispatch_tool(table, "shell_run", {"p": "a"}, context=_ctx("k"))
        assert not r1.is_error
        assert r2.is_error
        assert "reused with different content" in r2.output
        assert len(calls) == 1  # second did not execute

    @pytest.mark.asyncio
    async def test_same_key_different_args_rejected(self) -> None:
        """Same key reused with different arguments is rejected without a second execution (REQ-002)."""

        calls: list[int] = []

        async def handler(args: dict) -> str:
            calls.append(1)
            return "wrote"

        tool = self._side_effecting_tool()
        r1 = await dispatch_tool({tool: handler}, tool, {"p": "a"}, context=_ctx("k"))
        r2 = await dispatch_tool({tool: handler}, tool, {"p": "b"}, context=_ctx("k"))
        assert not r1.is_error
        assert r2.is_error
        assert "reused with different content" in r2.output
        assert len(calls) == 1

    @pytest.mark.asyncio
    async def test_ttl_expiry_reexecutes(self, monkeypatch: Any) -> None:
        """After the TTL elapses a repeat call re-executes instead of serving stale (REQ-003)."""

        calls: list[int] = []

        async def handler(args: dict) -> str:
            calls.append(1)
            return "wrote"

        clock: dict[str, float] = {"t": 1000.0}
        monkeypatch.setattr("mcp_servers.dispatch._idem_now", lambda: clock["t"])
        tool = self._side_effecting_tool()
        key = "ttl-key"
        await dispatch_tool({tool: handler}, tool, {"p": "a"}, context=_ctx(key))
        clock["t"] = 1000.0 + _IDEMPOTENCY_CACHE_TTL_SECONDS // 2  # within TTL
        await dispatch_tool({tool: handler}, tool, {"p": "a"}, context=_ctx(key))
        assert len(calls) == 1  # served from cache
        clock["t"] = 1000.0 + _IDEMPOTENCY_CACHE_TTL_SECONDS + 1.0  # past TTL
        r3 = await dispatch_tool({tool: handler}, tool, {"p": "a"}, context=_ctx(key))
        assert not r3.is_error
        assert len(calls) == 2  # expired, re-executed

    @pytest.mark.asyncio
    async def test_eviction_reexecutes_oldest(self) -> None:
        """Exceeding the max entry count evicts the oldest; an evicted key re-executes (REQ-003)."""

        calls: list[int] = []

        async def handler(args: dict) -> str:
            calls.append(1)
            return "wrote"

        tool = self._side_effecting_tool()
        table = {tool: handler}
        for i in range(_IDEMPOTENCY_CACHE_MAX_ENTRIES + 5):
            await dispatch_tool(table, tool, {"i": i}, context=_ctx(f"k{i}"))
        # Oldest keys were evicted -> a repeat re-executes.
        before = len(calls)
        r0 = await dispatch_tool(table, tool, {"i": 0}, context=_ctx("k0"))
        assert not r0.is_error
        assert len(calls) == before + 1
        # A still-present middle key is served from cache (no re-execution).
        mid_before = len(calls)
        await dispatch_tool(table, tool, {"i": 100}, context=_ctx("k100"))
        assert len(calls) == mid_before

    @pytest.mark.asyncio
    async def test_error_result_not_cached(self) -> None:
        """A ValueError result is never cached; a repeat identical call re-executes (REQ-004)."""

        calls: list[int] = []

        async def handler(args: dict) -> str:
            calls.append(1)
            raise ValueError("bad input")

        tool = self._side_effecting_tool()
        r1 = await dispatch_tool({tool: handler}, tool, {"p": "a"}, context=_ctx("k"))
        assert r1.is_error
        assert "Validation error" in r1.output
        assert len(_duplicate_cache) == 0
        calls.clear()
        r2 = await dispatch_tool({tool: handler}, tool, {"p": "a"}, context=_ctx("k"))
        assert r2.is_error
        assert len(calls) == 1  # re-executed, not served

    @pytest.mark.asyncio
    async def test_preview_result_is_not_cached(self) -> None:
        """A preview never acquires, so nothing is cached and a repeat preview
        re-executes the handler (REQ-004)."""

        calls: list[int] = []

        async def handler(args: dict) -> str:
            calls.append(1)
            return "would write"

        tool = self._side_effecting_tool()
        r1 = await dispatch_tool(
            {tool: handler}, tool, {"p": "a"}, context=_ctx("k", "preview")
        )
        assert not r1.is_error
        assert r1.execution_mode == "preview"
        assert r1.side_effect_applied is False
        assert len(_duplicate_cache) == 0
        calls.clear()
        r2 = await dispatch_tool(
            {tool: handler}, tool, {"p": "a"}, context=_ctx("k", "preview")
        )
        assert not r2.is_error
        assert len(calls) == 1  # re-executed, not served

    @pytest.mark.asyncio
    async def test_replay_reports_no_op_and_applied_success_reports_the_flag(
        self,
    ) -> None:
        """The mode on the result is what happened, not what was claimed: a served
        replay is no_op, an applied success on a side-effecting tool sets the flag."""

        calls: list[int] = []

        async def handler(args: dict) -> str:
            calls.append(1)
            return "wrote"

        tool = self._side_effecting_tool()
        first = await dispatch_tool(
            {tool: handler}, tool, {"p": "a"}, context=_ctx("k", "applied")
        )
        replay = await dispatch_tool(
            {tool: handler}, tool, {"p": "a"}, context=_ctx("k", "applied")
        )
        assert first.execution_mode == "applied"
        assert first.side_effect_applied is True
        assert replay.execution_mode == "no_op"
        assert replay.side_effect_applied is False
        assert len(calls) == 1


class TestDurableDedup:
    """Durable-store integration of dispatch_tool (REQ-003/REQ-005/REQ-009).

    Wiring note (2026-10-31 fix against the row 19 procedure): the shared
    ``TestDispatchIdempotencyCache`` fixture stays overlay-only. Plan Risks
    ("same-process same-turn behavior stays as today") locks its TTL-expiry and
    eviction re-execution assertions; wiring the tmp store there would turn
    those cases into store hits. This class carries its own per-test store
    fixture instead.
    """

    TOOL = "write_file"

    @pytest.fixture()
    def durable(self, tmp_path: Any, monkeypatch: Any) -> Iterator[dict[str, Any]]:
        import mcp_servers.dispatch as dispatch_mod
        from shared.mcp_dedup import DedupStore, DedupStoreConfig

        db_path = str(tmp_path / "mcp_dedup.sqlite")
        store = DedupStore(db_path)
        config = DedupStoreConfig(
            db_path=db_path,
            retention_days=14,
            pending_timeout_minutes=10,
        )
        _duplicate_cache.clear()
        monkeypatch.setattr(dispatch_mod, "_dedup_store", store)
        monkeypatch.setattr(dispatch_mod, "_dedup_config", config)
        monkeypatch.setattr(dispatch_mod, "_dedup_disabled", False)
        monkeypatch.setattr(dispatch_mod, "_purge_done", False)
        monkeypatch.setattr(
            dispatch_mod,
            "_tool_retry_policies",
            {self.TOOL: "same_logical_call_only"},
        )
        state = {
            "store": store,
            "config": config,
            "db_path": db_path,
            "mod": dispatch_mod,
        }
        yield state
        store.close()
        _duplicate_cache.clear()

    @staticmethod
    def _handler(calls: list[int]) -> Any:
        async def handler(args: dict) -> str:
            calls.append(1)
            return "wrote"

        return handler

    @pytest.fixture()
    def short_lease(self, tmp_path: Any, monkeypatch: Any) -> Iterator[dict[str, Any]]:
        """Same wiring as `durable` with a 1 s lease, for the expiry-boundary pair."""
        import mcp_servers.dispatch as dispatch_mod
        from shared.mcp_dedup import DedupStore, DedupStoreConfig

        db_path = str(tmp_path / "mcp_dedup.sqlite")
        store = DedupStore(db_path, lease_seconds=1)
        config = DedupStoreConfig(db_path=db_path)
        _duplicate_cache.clear()
        monkeypatch.setattr(dispatch_mod, "_dedup_store", store)
        monkeypatch.setattr(dispatch_mod, "_dedup_config", config)
        monkeypatch.setattr(dispatch_mod, "_dedup_disabled", False)
        monkeypatch.setattr(dispatch_mod, "_purge_done", False)
        monkeypatch.setattr(
            dispatch_mod,
            "_tool_retry_policies",
            {self.TOOL: "same_logical_call_only"},
        )
        yield {
            "store": store,
            "config": config,
            "db_path": db_path,
            "mod": dispatch_mod,
        }
        store.close()
        _duplicate_cache.clear()

    @pytest.mark.asyncio
    async def test_completed_hit_after_reopen_without_reexecution(
        self, durable: dict
    ) -> None:
        """After a simulated reopen the completed row is served from the store with
        zero additional handler invocations (row 04 completion criterion)."""
        calls: list[int] = []
        from shared.mcp_dedup import DedupStore

        r1 = await dispatch_tool(
            {self.TOOL: self._handler(calls)},
            self.TOOL,
            {"p": "a"},
            context=_ctx("k1"),
        )
        assert not r1.is_error and len(calls) == 1
        durable["store"].close()
        # Simulated reopen: fresh store handle, empty overlay.
        durable["mod"]._dedup_store = DedupStore(durable["db_path"])
        _duplicate_cache.clear()
        r2 = await dispatch_tool(
            {self.TOOL: self._handler(calls)},
            self.TOOL,
            {"p": "a"},
            context=_ctx("k1"),
        )
        assert not r2.is_error
        assert r2.output == "wrote"
        assert r2.dedup_state == "duplicate_hit"
        assert len(calls) == 1  # zero handler invocations on the second call

    @pytest.mark.asyncio
    async def test_completed_replay_served_from_store_without_overlay(
        self, durable: dict
    ) -> None:
        """T-6: the durable path has one decision point. The second call is served
        from the completed row (`duplicate_hit`) and the in-process overlay stays
        empty (REQ-001)."""
        calls: list[int] = []
        handler = self._handler(calls)
        r1 = await dispatch_tool(
            {self.TOOL: handler}, self.TOOL, {"p": "a"}, context=_ctx("k1")
        )
        r2 = await dispatch_tool(
            {self.TOOL: handler}, self.TOOL, {"p": "a"}, context=_ctx("k1")
        )
        assert not r1.is_error and not r2.is_error
        assert r1.dedup_state == ""  # fresh acquisition
        assert r2.dedup_state == "duplicate_hit"  # served from the store row
        assert r2.output == "wrote"
        assert len(calls) == 1
        assert len(_duplicate_cache) == 0  # the durable path never populates it

    @pytest.mark.asyncio
    async def test_completed_snapshot_mismatch_refused_replay(
        self, durable: dict, monkeypatch: Any
    ) -> None:
        """completed + snapshot mismatch -> refusal (replay_unavailable); the old
        force-reset fresh-attempt path is gone (mcpdl002 D-5). A matching
        snapshot keeps serving stored."""
        calls: list[int] = []
        r1 = await dispatch_tool(
            {self.TOOL: self._handler(calls)},
            self.TOOL,
            {"p": "a"},
            context=_ctx("k1"),
        )
        assert r1.dedup_state == ""
        assert len(calls) == 1
        row = durable["store"].get_execution("k1")
        assert row is not None and row.status == "completed"

        import mcp_servers.dispatch as dispatch_mod

        perturbed = dict(row.snapshot)
        perturbed["config_hash"] = "perturbed"
        monkeypatch.setattr(
            dispatch_mod, "build_execution_snapshot", lambda **kw: perturbed
        )
        _duplicate_cache.clear()
        r2 = await dispatch_tool(
            {self.TOOL: self._handler(calls)},
            self.TOOL,
            {"p": "a"},
            context=_ctx("k1"),
        )
        assert r2.is_error
        assert r2.error_type == "dedup_unreplayable"
        assert r2.dedup_state == "replay_unavailable"
        assert len(calls) == 1  # refused; no fresh attempt
        row2 = durable["store"].get_execution("k1")
        assert row2 is not None and row2.status == "completed"  # terminal row immutable
        # ...and the matching direction still serves the stored result.
        monkeypatch.setattr(
            dispatch_mod, "build_execution_snapshot", lambda **kw: dict(row.snapshot)
        )
        _duplicate_cache.clear()
        r3 = await dispatch_tool(
            {self.TOOL: self._handler(calls)},
            self.TOOL,
            {"p": "a"},
            context=_ctx("k1"),
        )
        assert r3.dedup_state == "duplicate_hit"
        assert len(calls) == 1

    @pytest.mark.asyncio
    async def test_expired_lease_retryable_replays_via_reconcile(
        self, durable: dict
    ) -> None:
        """pending with an expired lease + retryable -> reconcile_execution then
        one reacquisition, tagged replayed (REQ-005/AC-3)."""
        calls: list[int] = []
        import time

        args_hash = durable["mod"]._normalize_args_hash({"p": "a"})
        acq = durable["store"].try_acquire_execution(
            "k1",
            self.TOOL,
            args_hash,
            {"deployed_rev": "x"},
            "seed-owner",
            now_epoch=time.time() - 3600,
        )
        assert acq.status == "acquired"
        r = await dispatch_tool(
            {self.TOOL: self._handler(calls)},
            self.TOOL,
            {"p": "a"},
            context=_ctx("k1"),
        )
        assert not r.is_error
        assert r.dedup_state == "replayed"
        assert len(calls) == 1
        row = durable["store"].get_execution("k1")
        assert row is not None and row.status == "completed"
        assert row.attempt_number == 2  # reconcile + reacquisition advanced the ledger

    @pytest.mark.asyncio
    async def test_live_lease_other_owner_refused_in_progress(
        self, durable: dict
    ) -> None:
        """A live pending row owned by another caller refuses as in_progress;
        handler not executed (AC-2)."""
        calls: list[int] = []
        args_hash = durable["mod"]._normalize_args_hash({"p": "a"})
        acq = durable["store"].try_acquire_execution(
            "k1", self.TOOL, args_hash, {"deployed_rev": "x"}, "other-owner"
        )
        assert acq.status == "acquired"
        r = await dispatch_tool(
            {self.TOOL: self._handler(calls)},
            self.TOOL,
            {"p": "a"},
            context=_ctx("k1"),
        )
        assert r.is_error
        assert r.error_type == "dedup_in_progress"
        assert r.dedup_state == "in_progress"
        assert len(calls) == 0
        row = durable["store"].get_execution("k1")
        assert row is not None and row.status == "pending"
        assert row.owner_id == "other-owner"

    @pytest.mark.asyncio
    async def test_expired_pending_non_retryable_refused(self, durable: dict) -> None:
        """expired pending + non_retryable -> refuse with dedup_unreplayable /
        reconciliation_required; handler not executed (REQ-003/AC-3). Unknown
        tools default to non_retryable. The seeded state is an expired pending
        row, which is what the tag distinguishes from a real interrupted row."""
        calls: list[int] = []
        import time

        durable["mod"]._tool_retry_policies = {}
        args_hash = durable["mod"]._normalize_args_hash({"p": "a"})
        acq = durable["store"].try_acquire_execution(
            "k1",
            self.TOOL,
            args_hash,
            {"deployed_rev": "x"},
            "seed-owner",
            now_epoch=time.time() - 3600,
        )
        assert acq.status == "acquired"
        r = await dispatch_tool(
            {self.TOOL: self._handler(calls)},
            self.TOOL,
            {"p": "a"},
            context=_ctx("k1"),
        )
        assert r.is_error
        assert r.error_type == "dedup_unreplayable"
        assert r.dedup_state == "reconciliation_required"
        assert len(calls) == 0
        row = durable["store"].get_execution("k1")
        assert (
            row is not None and row.status == "pending"
        )  # refusal never mutates the row

    def _seed_interrupted(self, durable: dict, key: str = "k1") -> int:
        """Seed a genuinely `interrupted` row through the public store API the
        dispatcher's cancel path uses: acquire, then mark_interrupted. Returns the
        stored attempt_number (Plan T-4)."""
        import time

        args_hash = durable["mod"]._normalize_args_hash({"p": "a"})
        acq = durable["store"].try_acquire_execution(
            key,
            self.TOOL,
            args_hash,
            {"deployed_rev": "x"},
            "seed-owner",
            now_epoch=time.time() - 3600,
        )
        assert acq.status == "acquired"
        durable["store"].mark_interrupted(key, "seed-owner")
        row = durable["store"].get_execution(key)
        assert row is not None and row.status == "interrupted"
        return int(row.attempt_number)

    @pytest.mark.asyncio
    async def test_interrupted_row_non_retryable_refused(self, durable: dict) -> None:
        """T-4 (a): an interrupted row + no declared retry policy refuses with the
        `interrupted` tag, and the recovery path is never taken: handler not
        executed, row, attempt number and history untouched (REQ-004, AC-3)."""
        durable["mod"]._tool_retry_policies = {}
        attempts = self._seed_interrupted(durable)
        calls: list[int] = []
        r = await dispatch_tool(
            {self.TOOL: self._handler(calls)},
            self.TOOL,
            {"p": "a"},
            context=_ctx("k1"),
        )
        assert r.is_error
        assert r.error_type == "dedup_unreplayable"
        assert r.dedup_state == "interrupted"
        assert len(calls) == 0
        row = durable["store"].get_execution("k1")
        assert row is not None and row.status == "interrupted"
        assert row.attempt_number == attempts  # never re-attempted
        details = {detail for _, _, detail in _attempt_history(durable["store"])}
        assert "post-recovery" not in details  # no recovery evidence written

    @pytest.mark.asyncio
    async def test_interrupted_row_retryable_recovers_once(self, durable: dict) -> None:
        """T-4 (b): an interrupted row + declared retry policy reopens through the
        acquisition: the handler runs exactly once and the row ends completed with
        the recovery history entry (REQ-004/AC-3)."""
        attempts = self._seed_interrupted(durable)  # fixture policy: retryable
        calls: list[int] = []
        r = await dispatch_tool(
            {self.TOOL: self._handler(calls)},
            self.TOOL,
            {"p": "a"},
            context=_ctx("k1"),
        )
        assert not r.is_error
        assert r.dedup_state == ""  # one acquisition, directly reopened
        assert len(calls) == 1  # exactly one execution
        row = durable["store"].get_execution("k1")
        assert row is not None and row.status == "completed"
        assert row.attempt_number == attempts + 1
        assert any(
            detail == "post-recovery"
            for _, _, detail in _attempt_history(durable["store"])
        )

    @pytest.mark.asyncio
    async def test_failed_row_never_reattempted(self, durable: dict) -> None:
        """T-4 (c): a terminal `failed' row refuses replay in every retry class and is
        never re-attempted (REQ-003/REQ-004)."""
        args_hash = durable["mod"]._normalize_args_hash({"p": "a"})
        acq = durable["store"].try_acquire_execution(
            "k1", self.TOOL, args_hash, {"deployed_rev": "x"}, "seed-owner"
        )
        assert acq.status == "acquired"
        durable["store"].record_failed("k1", "handler_error", "seed-owner")
        calls: list[int] = []
        r = await dispatch_tool(
            {self.TOOL: self._handler(calls)},
            self.TOOL,
            {"p": "a"},
            context=_ctx("k1"),
        )
        assert r.is_error
        assert r.error_type == "dedup_unreplayable"
        assert r.dedup_state == "replay_unavailable"
        assert len(calls) == 0
        row = durable["store"].get_execution("k1")
        assert row is not None and row.status == "failed"  # terminal evidence kept
        assert row.attempt_number == 1

    @pytest.mark.asyncio
    async def test_truncated_completed_result_refuses_replay(
        self, durable: dict
    ) -> None:
        """T-5: a completed row whose stored payload is the truncated sentinel is not
        replayable: refusal, handler never executed again, terminal row preserved."""
        calls: list[int] = []

        async def long_handler(args: dict) -> str:
            calls.append(1)
            return "x" * 9000  # above RESULT_MAX_CHARS: stored as a truncated preview

        r1 = await dispatch_tool(
            {self.TOOL: long_handler}, self.TOOL, {"p": "a"}, context=_ctx("k1")
        )
        assert not r1.is_error
        row = durable["store"].get_execution("k1")
        assert row is not None and row.status == "completed"
        assert isinstance(row.result, dict) and row.result.get("truncated") is True
        assert len(calls) == 1

        r2 = await dispatch_tool(
            {self.TOOL: self._handler(calls)},
            self.TOOL,
            {"p": "a"},
            context=_ctx("k1"),
        )
        assert r2.is_error
        assert r2.error_type == "dedup_unreplayable"
        assert r2.dedup_state == "replay_unavailable"
        assert len(calls) == 1  # refused without re-executing the handler
        row2 = durable["store"].get_execution("k1")
        assert row2 is not None and row2.status == "completed"
        assert len(_duplicate_cache) == 0

    @pytest.mark.asyncio
    async def test_lease_expiry_boundary_pair(self, short_lease: dict) -> None:
        """T-5: the acquisition decision on either side of `lease_expires_epoch`
        (1 s lease, non-retryable tool): a call while the lease is live refuses
        in_progress, a call after it expired refuses reconciliation_required; the
        handler never runs and neither row is mutated (REQ-005/AC-2)."""
        import time

        short_lease["mod"]._tool_retry_policies = {}
        store = short_lease["store"]
        args_hash = short_lease["mod"]._normalize_args_hash({"p": "a"})
        calls: list[int] = []

        # Just before the boundary: the lease still has 0.8 s left.
        acq = store.try_acquire_execution(
            "before",
            self.TOOL,
            args_hash,
            {"deployed_rev": "x"},
            "seed-owner",
            now_epoch=time.time() - 0.2,
        )
        assert acq.status == "acquired"
        r1 = await dispatch_tool(
            {self.TOOL: self._handler(calls)},
            self.TOOL,
            {"p": "a"},
            context=_ctx("before"),
        )
        assert r1.is_error
        assert r1.error_type == "dedup_in_progress"
        assert r1.dedup_state == "in_progress"

        # Just after it: the same shape with a lease that expired 0.2 s ago.
        acq2 = store.try_acquire_execution(
            "after",
            self.TOOL,
            args_hash,
            {"deployed_rev": "x"},
            "seed-owner",
            now_epoch=time.time() - 1.2,
        )
        assert acq2.status == "acquired"
        r2 = await dispatch_tool(
            {self.TOOL: self._handler(calls)},
            self.TOOL,
            {"p": "a"},
            context=_ctx("after"),
        )
        assert r2.is_error
        assert r2.error_type == "dedup_unreplayable"
        assert r2.dedup_state == "reconciliation_required"
        assert len(calls) == 0  # neither side of the boundary dispatches the handler
        for key in ("before", "after"):
            row = store.get_execution(key)
            assert row is not None and row.status == "pending"
            assert row.owner_id == "seed-owner"

    @pytest.mark.asyncio
    async def test_attempt_cap_outcome_unknown_matrix(
        self, tmp_path: Any, monkeypatch: Any
    ) -> None:
        """attempt_number >= max_attempts -> outcome_unknown: non-retryable
        refuses, retryable dispatches degraded with the audited store_error
        marker (REQ-003)."""
        import time

        import mcp_servers.dispatch as dispatch_mod
        from shared.mcp_dedup import DedupStore, DedupStoreConfig

        db_path = str(tmp_path / "cap_dedup.sqlite")
        store = DedupStore(db_path, max_attempts=1)
        config = DedupStoreConfig(db_path=db_path)
        _duplicate_cache.clear()
        monkeypatch.setattr(dispatch_mod, "_dedup_store", store)
        monkeypatch.setattr(dispatch_mod, "_dedup_config", config)
        monkeypatch.setattr(dispatch_mod, "_dedup_disabled", False)
        monkeypatch.setattr(dispatch_mod, "_purge_done", False)
        monkeypatch.setattr(dispatch_mod, "_tool_retry_policies", {})
        try:
            args_hash = dispatch_mod._normalize_args_hash({"p": "a"})
            store.try_acquire_execution(
                "k1",
                self.TOOL,
                args_hash,
                {"deployed_rev": "x"},
                "seed-owner",
                now_epoch=time.time() - 3600,
            )
            calls: list[int] = []
            r = await dispatch_tool(
                {self.TOOL: self._handler(calls)},
                self.TOOL,
                {"p": "a"},
                context=_ctx("k1"),
            )
            assert r.is_error
            assert r.error_type == "dedup_unreplayable"
            assert r.dedup_state == "outcome_unknown"
            assert len(calls) == 0

            # Retryable classification: audited degraded dispatch, no ownership.
            dispatch_mod._tool_retry_policies = {self.TOOL: "same_logical_call_only"}
            _duplicate_cache.clear()
            calls2: list[int] = []
            r2 = await dispatch_tool(
                {self.TOOL: self._handler(calls2)},
                self.TOOL,
                {"p": "a"},
                context=_ctx("k1"),
            )
            assert not r2.is_error
            assert r2.dedup_state == "store_error"
            assert len(calls2) == 1
            row = store.get_execution("k1")
            assert (
                row is not None and row.status == "pending"
            )  # degraded path owns nothing
            assert row.attempt_number == 1
        finally:
            store.close()
            _duplicate_cache.clear()

    @pytest.mark.asyncio
    async def test_durable_args_hash_mismatch_rejected(self, durable: dict) -> None:
        """Same key, different args in a durable row keeps the REQ-002 rejection shape."""
        calls: list[int] = []
        r1 = await dispatch_tool(
            {self.TOOL: self._handler(calls)},
            self.TOOL,
            {"p": "a"},
            context=_ctx("k1"),
        )
        assert not r1.is_error
        durable["mod"]._dedup_store.close()
        from shared.mcp_dedup import DedupStore

        durable["mod"]._dedup_store = DedupStore(durable["db_path"])
        _duplicate_cache.clear()
        r2 = await dispatch_tool(
            {self.TOOL: self._handler(calls)},
            self.TOOL,
            {"p": "b"},
            context=_ctx("k1"),
        )
        assert r2.is_error
        assert r2.error_type == "idempotency_key_reused"
        assert len(calls) == 1
        # The rejection comes from the acquisition's contract_mismatch, not from
        # an overlay comparison (REQ-001).
        assert len(_duplicate_cache) == 0

    @pytest.mark.asyncio
    async def test_store_error_retryable_proceeds_non_retryable_fails_closed(
        self, durable: dict, monkeypatch: Any
    ) -> None:
        """Store acquisition failure: retryable tools dispatch with the audited
        store_error marker; non-retryable tools fail closed (plan Risks)."""
        calls: list[int] = []

        def _boom(*a: Any, **kw: Any) -> None:
            raise sqlite3.OperationalError("disk is locked")

        monkeypatch.setattr(durable["store"], "try_acquire_execution", _boom)
        r = await dispatch_tool(
            {self.TOOL: self._handler(calls)},
            self.TOOL,
            {"p": "a"},
            context=_ctx("k1"),
        )
        assert not r.is_error
        assert r.dedup_state == "store_error"
        assert len(calls) == 1

        calls2: list[int] = []
        durable["mod"]._tool_retry_policies = {}
        r2 = await dispatch_tool(
            {self.TOOL: self._handler(calls2)},
            self.TOOL,
            {"p": "b"},
            context=_ctx("k2"),
        )
        assert r2.is_error
        assert r2.error_type == "dedup_store_error"
        assert len(calls2) == 0

    @pytest.mark.asyncio
    async def test_not_configured_fails_closed_and_degrades(
        self, durable: dict, monkeypatch: Any
    ) -> None:
        """A dispatcher whose bootstrap never ran (store never injected): non-
        retryable tools fail closed with dedup_store_error; retryable tools
        degrade to store_error and proceed overlay-only (REQ-001/REQ-002)."""
        mod = durable["mod"]
        mod._dedup_store = None
        mod._dedup_config = None
        mod._dedup_disabled = False
        mod._dedup_start_state = None

        # Retryable tool: degrade to store_error and proceed overlay-only (REQ-002).
        mod._tool_retry_policies = {self.TOOL: "same_logical_call_only"}
        calls: list[int] = []
        r = await dispatch_tool(
            {self.TOOL: self._handler(calls)},
            self.TOOL,
            {"p": "a"},
            context=_ctx("k1"),
        )
        assert not r.is_error
        assert r.dedup_state == "store_error"
        assert mod._dedup_start_state == "not_configured"
        assert len(calls) == 1

        # Non-retryable tool: fail closed (REQ-001).
        mod._tool_retry_policies = {}
        calls2: list[int] = []
        r2 = await dispatch_tool(
            {self.TOOL: self._handler(calls2)},
            self.TOOL,
            {"p": "b"},
            context=_ctx("k2"),
        )
        assert r2.is_error
        assert r2.error_type == "dedup_store_error"
        assert len(calls2) == 0

    @pytest.mark.asyncio
    async def test_lost_store_refuses_bootstrap_open(
        self, durable: dict, monkeypatch: Any
    ) -> None:
        """A lost store (file gone while the installation marker remains) refuses
        the injected bootstrap open with the typed 'lost' start state: the MCP
        process must not start (REQ-006/REQ-007)."""
        import os

        mod = durable["mod"]
        # Simulate a lost store: delete the DB file, leave .mcp_dedup_installed.
        durable["store"].close()
        os.remove(durable["db_path"])
        with pytest.raises(DedupStoreError) as excinfo:
            mod.configure_dedup(durable["config"])
        assert excinfo.value.state == "lost"

    @pytest.mark.asyncio
    async def test_replaced_store_refuses_bootstrap_open(self, durable: dict) -> None:
        """A store file whose store_meta uuid contradicts the installation marker
        is classified 'replaced' and refuses the bootstrap open (REQ-006)."""
        mod = durable["mod"]
        durable["store"].close()
        raw = sqlite3.connect(durable["db_path"])
        raw.execute("UPDATE store_meta SET store_uuid = 'foreign-uuid-0000'")
        raw.commit()
        raw.close()
        with pytest.raises(DedupStoreError) as excinfo:
            mod.configure_dedup(durable["config"])
        assert excinfo.value.state == "replaced"

    @pytest.mark.asyncio
    async def test_drifted_config_refuses_bootstrap_open(self, durable: dict) -> None:
        """Reopening the shared store under a [dedup] table whose values drifted
        from the first-initialization fingerprint refuses with 'identity_mismatch'
        (REQ-007 reopen gate)."""
        mod = durable["mod"]
        durable["store"].close()
        from shared.mcp_dedup import DedupStore as _Store

        first = _Store(durable["db_path"], config=durable["config"])
        first.close()
        drifted = replace(durable["config"], lease_seconds=45)
        with pytest.raises(DedupStoreError) as excinfo:
            mod.configure_dedup(drifted)
        assert excinfo.value.state == "identity_mismatch"

    @pytest.mark.asyncio
    async def test_legacy_store_refuses_bootstrap_open(self, durable: dict) -> None:
        """A pre-change store shape (no store_meta identity row) is classified
        'legacy_or_unverified' and refuses the bootstrap open, never first-
        initialization (REQ-006)."""
        import os

        mod = durable["mod"]
        durable["store"].close()
        os.remove(durable["db_path"])
        marker = os.path.join(
            os.path.dirname(durable["db_path"]), ".mcp_dedup_installed"
        )
        if os.path.exists(marker):
            os.remove(marker)
        raw = sqlite3.connect(durable["db_path"])
        raw.execute("CREATE TABLE dedup_call_state (key TEXT PRIMARY KEY, status TEXT)")
        raw.commit()
        raw.close()
        with pytest.raises(DedupStoreError) as excinfo:
            mod.configure_dedup(durable["config"])
        assert excinfo.value.state == "legacy_or_unverified"

    @pytest.mark.asyncio
    async def test_first_ever_key_executes_once_on_fresh_store(
        self, durable: dict
    ) -> None:
        """A genuinely fresh store (no installation marker) classifies as
        first_initialization and executes a never-seen key once (REQ-006)."""
        assert durable["store"].start_state == "first_initialization"
        durable["mod"]._tool_retry_policies = {}
        calls: list[int] = []
        r = await dispatch_tool(
            {self.TOOL: self._handler(calls)},
            self.TOOL,
            {"p": "a"},
            context=_ctx("fresh-1"),
        )
        assert not r.is_error
        assert len(calls) == 1
        assert (
            len(_duplicate_cache) == 0
        )  # a full acquire/complete cycle leaves no overlay

    @pytest.mark.asyncio
    async def test_post_open_write_failure_fails_closed_non_retryable(
        self, durable: dict, monkeypatch: Any
    ) -> None:
        """A failed acquisition write leaves no proof of completion: a
        non-retryable tool fails closed (REQ-002)."""

        def _boom(*a: Any, **kw: Any) -> None:
            raise sqlite3.OperationalError("disk I/O error")

        monkeypatch.setattr(durable["store"], "try_acquire_execution", _boom)
        durable["mod"]._tool_retry_policies = {}
        calls: list[int] = []
        r = await dispatch_tool(
            {self.TOOL: self._handler(calls)},
            self.TOOL,
            {"p": "a"},
            context=_ctx("k1"),
        )
        assert r.is_error
        assert r.error_type == "dedup_store_error"
        assert len(calls) == 0

    @pytest.mark.asyncio
    async def test_post_open_write_failure_warning_only_retryable(
        self, durable: dict, monkeypatch: Any
    ) -> None:
        """A failed acquisition write degrades to the overlay for a retryable
        tool (warning only); the call still executes (REQ-002)."""

        def _boom(*a: Any, **kw: Any) -> None:
            raise sqlite3.OperationalError("disk I/O error")

        monkeypatch.setattr(durable["store"], "try_acquire_execution", _boom)
        calls: list[int] = []
        r = await dispatch_tool(
            {self.TOOL: self._handler(calls)},
            self.TOOL,
            {"p": "a"},
            context=_ctx("k1"),
        )
        assert not r.is_error
        assert len(calls) == 1

    @pytest.mark.asyncio
    async def test_retention_sweep_runs_once_per_process(self, durable: dict) -> None:
        """One opportunistic purge per process (REQ-009)."""
        import time

        calls: list[int] = []
        old = time.time() - 15 * 86400
        snap = {"deployed_rev": "x"}
        durable["store"].try_acquire_execution(
            "old1", self.TOOL, "h", snap, "seed-owner", now_epoch=old
        )
        durable["store"].record_completed(
            "old1", snap, "done", "seed-owner", now_epoch=old
        )
        assert durable["store"].get_execution("old1") is not None
        await dispatch_tool(
            {self.TOOL: self._handler(calls)},
            self.TOOL,
            {"p": "a"},
            context=_ctx("k1"),
        )
        assert (
            durable["store"].get_execution("old1") is None
        )  # swept by the first dispatch
        durable["store"].try_acquire_execution(
            "old2", self.TOOL, "h", snap, "seed-owner", now_epoch=old
        )
        durable["store"].record_completed(
            "old2", snap, "done", "seed-owner", now_epoch=old
        )
        await dispatch_tool(
            {self.TOOL: self._handler(calls)},
            self.TOOL,
            {"p": "a"},
            context=_ctx("k2"),
        )
        assert (
            durable["store"].get_execution("old2") is not None
        )  # no second sweep in-process

    @pytest.mark.asyncio
    async def test_error_and_preview_do_not_leave_replayable_state(
        self, durable: dict
    ) -> None:
        """A validation failure lands on 'failed'; a preview leaves nothing behind:
        no cached result and no durable row, so the key is still free for a real call."""

        async def bad(args: dict) -> str:
            raise ValueError("bad input")

        r1 = await dispatch_tool(
            {self.TOOL: bad}, self.TOOL, {"p": "a"}, context=_ctx("k1")
        )
        assert r1.is_error
        assert durable["store"].get_execution("k1").status == "failed"

        calls: list[int] = []
        r2 = await dispatch_tool(
            {self.TOOL: self._handler(calls)},
            self.TOOL,
            {"p": "a"},
            context=_ctx("k2", "preview"),
        )
        assert not r2.is_error
        assert r2.execution_mode == "preview"
        assert durable["store"].get_execution("k2") is None  # no replayable state
        assert len(_duplicate_cache) == 0

        r3 = await dispatch_tool(
            {self.TOOL: self._handler(calls)},
            self.TOOL,
            {"p": "a"},
            context=_ctx("k2"),
        )
        assert not r3.is_error
        assert r3.execution_mode == "applied"
        assert r3.side_effect_applied is True
        assert durable["store"].get_execution("k2").status == "completed"
        assert len(calls) == 2  # the preview ran, the applied call ran again


class TestDurableDedupDryRunClear:
    """Dry-run outcomes must not leave replayable state behind (REQ-004)."""

    TOOL = "write_file"

    @pytest.fixture()
    def durable(self, tmp_path: Any, monkeypatch: Any) -> Iterator[dict[str, Any]]:
        import mcp_servers.dispatch as dispatch_mod
        from shared.mcp_dedup import DedupStore, DedupStoreConfig

        db_path = str(tmp_path / "mcp_dedup.sqlite")
        store = DedupStore(db_path)
        config = DedupStoreConfig(db_path=db_path)
        _duplicate_cache.clear()
        monkeypatch.setattr(dispatch_mod, "_dedup_store", store)
        monkeypatch.setattr(dispatch_mod, "_dedup_config", config)
        monkeypatch.setattr(dispatch_mod, "_dedup_disabled", False)
        monkeypatch.setattr(dispatch_mod, "_purge_done", False)
        monkeypatch.setattr(
            dispatch_mod,
            "_tool_retry_policies",
            {self.TOOL: "same_logical_call_only"},
        )
        yield {"store": store, "mod": dispatch_mod}
        store.close()
        _duplicate_cache.clear()

    @pytest.mark.asyncio
    async def test_preview_leaves_no_row(self, durable: dict) -> None:
        async def dry(args: dict) -> str:
            return "would write"

        r = await dispatch_tool(
            {self.TOOL: dry}, self.TOOL, {"p": "a"}, context=_ctx("k1", "preview")
        )
        assert not r.is_error
        assert r.execution_mode == "preview"
        assert durable["store"].get_execution("k1") is None  # no replayable state left
        assert len(_duplicate_cache) == 0

    @pytest.mark.asyncio
    async def test_finalize_lease_conflict_surfaces_without_redispatch(
        self, durable: dict, monkeypatch: Any
    ) -> None:
        """A lost lease at finalization is surfaced as lease_conflict: the
        handler ran once and is never re-dispatched (REQ-002)."""
        from shared.mcp_dedup import DedupLeaseConflict

        def _conflict(*a: Any, **kw: Any) -> None:
            raise DedupLeaseConflict("record_completed updated 0 rows")

        monkeypatch.setattr(durable["store"], "record_completed", _conflict)
        calls: list[int] = []

        async def handler(args: dict) -> str:
            calls.append(1)
            return "wrote"

        r = await dispatch_tool(
            {self.TOOL: handler}, self.TOOL, {"p": "a"}, context=_ctx("k1")
        )
        assert not r.is_error  # the handler already ran; the outcome is surfaced
        assert r.dedup_state == "lease_conflict"
        assert len(calls) == 1
        row = durable["store"].get_execution("k1")
        assert (
            row is not None and row.status == "pending"
        )  # the row stays for reconciliation


class TestKeylessRejectionOverRealSideEffectingSet:
    """Every tool of the real ALL_SIDE_EFFECTING_TOOLS is refused without a key.

    The tools come from the live set, so a tool added to it is covered without
    editing this class.
    """

    @pytest.fixture(autouse=True)
    def _isolated_cache(self) -> Iterator[None]:
        _duplicate_cache.clear()
        yield
        _duplicate_cache.clear()

    def test_the_real_set_is_not_empty(self) -> None:
        assert ALL_SIDE_EFFECTING_TOOLS

    @pytest.mark.asyncio
    @pytest.mark.parametrize("tool", sorted(ALL_SIDE_EFFECTING_TOOLS))
    @pytest.mark.parametrize("key", ["", "   ", "\t\n"])
    async def test_missing_empty_or_whitespace_key_is_refused(
        self, tool: str, key: str
    ) -> None:
        calls: list[int] = []

        async def handler(args: dict) -> str:
            calls.append(1)
            return "ran"

        r = await dispatch_tool({tool: handler}, tool, {"p": "a"}, context=_ctx(key))

        assert r.is_error
        assert r.error_type == "idempotency_key_required"
        assert r.execution_mode == "no_op"
        assert r.side_effect_applied is False
        assert calls == []
        assert len(_duplicate_cache) == 0

    @pytest.mark.asyncio
    @pytest.mark.parametrize("tool", sorted(ALL_SIDE_EFFECTING_TOOLS))
    async def test_programmatic_call_without_a_context_is_refused(
        self, tool: str
    ) -> None:
        calls: list[int] = []

        async def handler(args: dict) -> str:
            calls.append(1)
            return "ran"

        r = await dispatch_tool({tool: handler}, tool, {"p": "a"})

        assert r.is_error
        assert r.error_type == "idempotency_key_required"
        assert calls == []

    @pytest.mark.asyncio
    @pytest.mark.parametrize("tool", sorted(ALL_SIDE_EFFECTING_TOOLS))
    async def test_a_valid_key_reaches_the_handler(
        self, tool: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Control: the same call with a key runs, so the sweep above proves the
        key requirement and not a handler that never runs."""
        import mcp_servers.dispatch as dispatch_mod

        monkeypatch.setattr(dispatch_mod, "_dedup_store", None)
        monkeypatch.setattr(dispatch_mod, "_dedup_config", None)
        monkeypatch.setattr(dispatch_mod, "_dedup_disabled", True)
        monkeypatch.setattr(
            dispatch_mod,
            "_tool_retry_policies",
            dict.fromkeys(ALL_SIDE_EFFECTING_TOOLS, "same_logical_call_only"),
        )
        calls: list[int] = []

        async def handler(args: dict) -> str:
            calls.append(1)
            return "ran"

        r = await dispatch_tool(
            {tool: handler}, tool, {"p": "a"}, context=_ctx("k-control")
        )

        assert not r.is_error
        assert calls == [1]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
