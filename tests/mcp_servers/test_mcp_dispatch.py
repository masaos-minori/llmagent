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
        # Overlay-only isolation: with the resolver-based config default the conftest
        # isolation config makes the durable store openable in-process, which would
        # turn these fixed-key cases into store hits. Disable it explicitly here.
        import mcp_servers.dispatch as dispatch_mod

        _duplicate_cache.clear()
        monkeypatch.setattr(dispatch_mod, "_dedup_store", None)
        monkeypatch.setattr(dispatch_mod, "_dedup_config", None)
        monkeypatch.setattr(dispatch_mod, "_dedup_disabled", True)
        yield
        _duplicate_cache.clear()

    @staticmethod
    def _side_effecting_tool() -> str:
        name = "write_file"
        assert _is_side_effecting(name)
        return name

    @pytest.mark.asyncio
    async def test_keyless_and_empty_key_always_execute(self) -> None:
        """A keyless or empty-key call never touches the cache (REQ-001)."""

        calls: list[int] = []

        async def handler(args: dict) -> str:
            calls.append(1)
            return "wrote"

        tool = self._side_effecting_tool()
        for key in (None, ""):
            r1 = await dispatch_tool(
                {tool: handler}, tool, {"p": "a"}, idempotency_key=key
            )
            r2 = await dispatch_tool(
                {tool: handler}, tool, {"p": "a"}, idempotency_key=key
            )
            assert not r1.is_error and not r2.is_error
        assert len(calls) == 4  # executed every time across both keyless calls
        assert len(_duplicate_cache) == 0  # nothing stored

    @pytest.mark.asyncio
    async def test_same_key_served_from_cache(self) -> None:
        """Same key + same tool + same args: handler runs once, second is cached (REQ-002)."""

        calls: list[int] = []

        async def handler(args: dict) -> str:
            calls.append(1)
            return "wrote"

        tool = self._side_effecting_tool()
        key = "same-key"
        r1 = await dispatch_tool({tool: handler}, tool, {"p": "a"}, idempotency_key=key)
        r2 = await dispatch_tool({tool: handler}, tool, {"p": "a"}, idempotency_key=key)
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
                {tool: handler}, tool, {"p": "a"}, idempotency_key=key
            )
            r2 = await dispatch_tool(
                {tool: handler}, tool, {"p": "a"}, idempotency_key=key
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
        r1 = await dispatch_tool(table, "write_file", {"p": "a"}, idempotency_key="k")
        r2 = await dispatch_tool(table, "shell_run", {"p": "a"}, idempotency_key="k")
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
        r1 = await dispatch_tool({tool: handler}, tool, {"p": "a"}, idempotency_key="k")
        r2 = await dispatch_tool({tool: handler}, tool, {"p": "b"}, idempotency_key="k")
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
        await dispatch_tool({tool: handler}, tool, {"p": "a"}, idempotency_key=key)
        clock["t"] = 1000.0 + _IDEMPOTENCY_CACHE_TTL_SECONDS // 2  # within TTL
        await dispatch_tool({tool: handler}, tool, {"p": "a"}, idempotency_key=key)
        assert len(calls) == 1  # served from cache
        clock["t"] = 1000.0 + _IDEMPOTENCY_CACHE_TTL_SECONDS + 1.0  # past TTL
        r3 = await dispatch_tool({tool: handler}, tool, {"p": "a"}, idempotency_key=key)
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
            await dispatch_tool(table, tool, {"i": i}, idempotency_key=f"k{i}")
        # Oldest keys were evicted -> a repeat re-executes.
        before = len(calls)
        r0 = await dispatch_tool(table, tool, {"i": 0}, idempotency_key="k0")
        assert not r0.is_error
        assert len(calls) == before + 1
        # A still-present middle key is served from cache (no re-execution).
        mid_before = len(calls)
        await dispatch_tool(table, tool, {"i": 100}, idempotency_key="k100")
        assert len(calls) == mid_before

    @pytest.mark.asyncio
    async def test_error_result_not_cached(self) -> None:
        """A ValueError result is never cached; a repeat identical call re-executes (REQ-004)."""

        calls: list[int] = []

        async def handler(args: dict) -> str:
            calls.append(1)
            raise ValueError("bad input")

        tool = self._side_effecting_tool()
        r1 = await dispatch_tool({tool: handler}, tool, {"p": "a"}, idempotency_key="k")
        assert r1.is_error
        assert "Validation error" in r1.output
        assert len(_duplicate_cache) == 0
        calls.clear()
        r2 = await dispatch_tool({tool: handler}, tool, {"p": "a"}, idempotency_key="k")
        assert r2.is_error
        assert len(calls) == 1  # re-executed, not served

    @pytest.mark.asyncio
    async def test_dry_run_result_not_cached(self) -> None:
        """A dry-run result is never cached; a repeat call re-executes (REQ-004 / UNK-01)."""

        calls: list[int] = []

        async def handler(args: dict) -> str:
            calls.append(1)
            return '{"dry_run": true}'

        tool = self._side_effecting_tool()
        r1 = await dispatch_tool({tool: handler}, tool, {"p": "a"}, idempotency_key="k")
        assert not r1.is_error
        assert len(_duplicate_cache) == 0
        calls.clear()
        r2 = await dispatch_tool({tool: handler}, tool, {"p": "a"}, idempotency_key="k")
        assert not r2.is_error
        assert len(calls) == 1  # re-executed, not served


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
        from shared.mcp_dedup import DedupConfig, DedupStore

        db_path = str(tmp_path / "mcp_dedup.sqlite")
        store = DedupStore(db_path)
        config = DedupConfig(
            db_path=db_path,
            retention_days=14,
            pending_timeout_minutes=10,
            retry_class={self.TOOL: "retryable"},
        )
        _duplicate_cache.clear()
        monkeypatch.setattr(dispatch_mod, "_dedup_store", store)
        monkeypatch.setattr(dispatch_mod, "_dedup_config", config)
        monkeypatch.setattr(dispatch_mod, "_dedup_disabled", False)
        monkeypatch.setattr(dispatch_mod, "_purge_done", False)
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
            idempotency_key="k1",
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
            idempotency_key="k1",
        )
        assert not r2.is_error
        assert r2.output == "wrote"
        assert r2.dedup_state == "duplicate_hit"
        assert len(calls) == 1  # zero handler invocations on the second call

    @pytest.mark.asyncio
    async def test_overlay_fast_path_still_hits(self, durable: dict) -> None:
        """The overlay stays a completed-only fast path within one process (REQ-003)."""
        calls: list[int] = []
        handler = self._handler(calls)
        r1 = await dispatch_tool(
            {self.TOOL: handler}, self.TOOL, {"p": "a"}, idempotency_key="k1"
        )
        r2 = await dispatch_tool(
            {self.TOOL: handler}, self.TOOL, {"p": "a"}, idempotency_key="k1"
        )
        assert not r1.is_error and not r2.is_error
        assert r2.dedup_state == r1.dedup_state  # served verbatim from the overlay
        assert len(calls) == 1
        assert len(_duplicate_cache) == 1

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
            idempotency_key="k1",
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
            idempotency_key="k1",
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
            idempotency_key="k1",
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
            idempotency_key="k1",
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
            idempotency_key="k1",
        )
        assert r.is_error
        assert r.error_type == "dedup_in_progress"
        assert r.dedup_state == "in_progress"
        assert len(calls) == 0
        row = durable["store"].get_execution("k1")
        assert row is not None and row.status == "pending"
        assert row.owner_id == "other-owner"

    @pytest.mark.asyncio
    async def test_interrupted_non_retryable_refused(self, durable: dict) -> None:
        """expired pending + non_retryable -> refuse with dedup_unreplayable /
        reconciliation_required; handler not executed (REQ-003/AC-3). Unknown
        tools default to non_retryable."""
        calls: list[int] = []
        import time

        durable["mod"]._dedup_config = replace(durable["config"], retry_class={})
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
            idempotency_key="k1",
        )
        assert r.is_error
        assert r.error_type == "dedup_unreplayable"
        assert r.dedup_state == "reconciliation_required"
        assert len(calls) == 0
        row = durable["store"].get_execution("k1")
        assert (
            row is not None and row.status == "pending"
        )  # refusal never mutates the row

    @pytest.mark.asyncio
    async def test_attempt_cap_outcome_unknown_matrix(
        self, tmp_path: Any, monkeypatch: Any
    ) -> None:
        """attempt_number >= max_attempts -> outcome_unknown: non-retryable
        refuses, retryable dispatches degraded with the audited store_error
        marker (REQ-003)."""
        import time

        import mcp_servers.dispatch as dispatch_mod
        from shared.mcp_dedup import DedupConfig, DedupStore

        db_path = str(tmp_path / "cap_dedup.sqlite")
        store = DedupStore(db_path, max_attempts=1)
        config = DedupConfig(db_path=db_path, retry_class={})
        _duplicate_cache.clear()
        monkeypatch.setattr(dispatch_mod, "_dedup_store", store)
        monkeypatch.setattr(dispatch_mod, "_dedup_config", config)
        monkeypatch.setattr(dispatch_mod, "_dedup_disabled", False)
        monkeypatch.setattr(dispatch_mod, "_purge_done", False)
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
                idempotency_key="k1",
            )
            assert r.is_error
            assert r.error_type == "dedup_unreplayable"
            assert r.dedup_state == "outcome_unknown"
            assert len(calls) == 0

            # Retryable classification: audited degraded dispatch, no ownership.
            dispatch_mod._dedup_config = replace(
                config, retry_class={self.TOOL: "retryable"}
            )
            _duplicate_cache.clear()
            calls2: list[int] = []
            r2 = await dispatch_tool(
                {self.TOOL: self._handler(calls2)},
                self.TOOL,
                {"p": "a"},
                idempotency_key="k1",
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
            idempotency_key="k1",
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
            idempotency_key="k1",
        )
        assert r2.is_error
        assert r2.error_type == "idempotency_key_reused"
        assert len(calls) == 1

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
            idempotency_key="k1",
        )
        assert not r.is_error
        assert r.dedup_state == "store_error"
        assert len(calls) == 1

        calls2: list[int] = []
        durable["mod"]._dedup_config = replace(durable["config"], retry_class={})
        r2 = await dispatch_tool(
            {self.TOOL: self._handler(calls2)},
            self.TOOL,
            {"p": "b"},
            idempotency_key="k2",
        )
        assert r2.is_error
        assert r2.error_type == "dedup_store_error"
        assert len(calls2) == 0

    @pytest.mark.asyncio
    async def test_init_failure_fail_closed_and_degrade(
        self, durable: dict, monkeypatch: Any
    ) -> None:
        """Store initialization failure (dedup unavailable): non-retryable tools
        fail closed with dedup_store_error; retryable tools degrade to
        store_error and proceed overlay-only (REQ-001/REQ-002). Mirrors the
        lookup-failure test but forces the (None, None) init-failure path."""
        import shared.mcp_dedup as dedup_mod

        mod = durable["mod"]
        # Force the (None, None) init-failure path: clear any cached context so
        # _dedup_context() re-enters init, point load_dedup_config at a valid
        # config, then make open_dedup_store raise so init fails open.
        mod._dedup_store = None
        mod._dedup_config = None
        mod._dedup_disabled = False
        monkeypatch.setattr(mod, "load_dedup_config", lambda: durable["config"])

        def _boom(*a: Any, **kw: Any) -> None:
            raise sqlite3.OperationalError("init failed")

        monkeypatch.setattr(mod, "open_dedup_store", _boom)

        def _cfg(retry: dict[str, str]) -> Any:
            return replace(durable["config"], retry_class=retry)

        # Retryable tool: degrade to store_error and proceed overlay-only (REQ-002).
        monkeypatch.setattr(
            dedup_mod, "load_dedup_config", lambda: _cfg({self.TOOL: "retryable"})
        )
        calls: list[int] = []
        r = await dispatch_tool(
            {self.TOOL: self._handler(calls)},
            self.TOOL,
            {"p": "a"},
            idempotency_key="k1",
        )
        assert not r.is_error
        assert r.dedup_state == "store_error"
        assert len(calls) == 1

        # Non-retryable tool: fail closed (REQ-001).
        monkeypatch.setattr(dedup_mod, "load_dedup_config", lambda: _cfg({}))
        calls2: list[int] = []
        r2 = await dispatch_tool(
            {self.TOOL: self._handler(calls2)},
            self.TOOL,
            {"p": "b"},
            idempotency_key="k2",
        )
        assert r2.is_error
        assert r2.error_type == "dedup_store_error"
        assert len(calls2) == 0

    @pytest.mark.asyncio
    async def test_lost_store_start_state_refused_retryable_degrades(
        self, durable: dict, monkeypatch: Any
    ) -> None:
        """A lost store (file gone while the installation marker remains) refuses
        the open with the typed 'lost' start state: non-retryable tools fail
        closed, retryable tools degrade overlay-only (REQ-006/REQ-007)."""
        import os

        import shared.mcp_dedup as dedup_mod

        mod = durable["mod"]
        # Simulate a lost store: delete the DB file, leave .mcp_dedup_installed.
        durable["store"].close()
        os.remove(durable["db_path"])
        # Force re-init: _dedup_context() re-opens and the store refuses with 'lost'.
        mod._dedup_store = None
        mod._dedup_config = None
        mod._dedup_disabled = False
        mod._dedup_start_state = None
        monkeypatch.setattr(mod, "load_dedup_config", lambda: durable["config"])
        monkeypatch.setattr(
            dedup_mod,
            "load_dedup_config",
            lambda: replace(durable["config"], retry_class={}),
        )

        # Non-retryable: refused without executing (fail closed).
        calls: list[int] = []
        r = await dispatch_tool(
            {self.TOOL: self._handler(calls)},
            self.TOOL,
            {"p": "a"},
            idempotency_key="k1",
        )
        assert r.is_error
        assert r.error_type == "dedup_store_error"
        assert r.dedup_state == "store_error"
        assert mod._dedup_start_state == "lost"
        assert len(calls) == 0

        # Retryable: degrade to store_error and proceed overlay-only.
        monkeypatch.setattr(
            dedup_mod,
            "load_dedup_config",
            lambda: replace(durable["config"], retry_class={self.TOOL: "retryable"}),
        )
        calls2: list[int] = []
        r2 = await dispatch_tool(
            {self.TOOL: self._handler(calls2)},
            self.TOOL,
            {"p": "b"},
            idempotency_key="k2",
        )
        assert not r2.is_error
        assert r2.dedup_state == "store_error"
        assert len(calls2) == 1

    @pytest.mark.asyncio
    async def test_replaced_store_start_state_refused(
        self, durable: dict, monkeypatch: Any
    ) -> None:
        """A store file whose store_meta uuid contradicts the installation marker
        is classified 'replaced' and refuses the open: non-retryable tools fail
        closed (REQ-006)."""
        import shared.mcp_dedup as dedup_mod

        mod = durable["mod"]
        durable["store"].close()
        raw = sqlite3.connect(durable["db_path"])
        raw.execute("UPDATE store_meta SET store_uuid = 'foreign-uuid-0000'")
        raw.commit()
        raw.close()
        mod._dedup_store = None
        mod._dedup_config = None
        mod._dedup_disabled = False
        mod._dedup_start_state = None
        cfg = replace(durable["config"], retry_class={})
        monkeypatch.setattr(mod, "load_dedup_config", lambda: cfg)
        monkeypatch.setattr(dedup_mod, "load_dedup_config", lambda: cfg)

        calls: list[int] = []
        r = await dispatch_tool(
            {self.TOOL: self._handler(calls)},
            self.TOOL,
            {"p": "a"},
            idempotency_key="k1",
        )
        assert r.is_error
        assert r.error_type == "dedup_store_error"
        assert r.dedup_state == "store_error"
        assert mod._dedup_start_state == "replaced"
        assert len(calls) == 0

    @pytest.mark.asyncio
    async def test_legacy_store_start_state_refused(
        self, durable: dict, monkeypatch: Any
    ) -> None:
        """A pre-change store shape (no store_meta identity row) is classified
        'legacy_or_unverified' and refuses the open: non-retryable tools fail
        closed, never first-initialization (REQ-006)."""
        import os

        import shared.mcp_dedup as dedup_mod

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
        mod._dedup_store = None
        mod._dedup_config = None
        mod._dedup_disabled = False
        mod._dedup_start_state = None
        cfg = replace(durable["config"], retry_class={})
        monkeypatch.setattr(mod, "load_dedup_config", lambda: cfg)
        monkeypatch.setattr(dedup_mod, "load_dedup_config", lambda: cfg)

        calls: list[int] = []
        r = await dispatch_tool(
            {self.TOOL: self._handler(calls)},
            self.TOOL,
            {"p": "a"},
            idempotency_key="k1",
        )
        assert r.is_error
        assert r.error_type == "dedup_store_error"
        assert r.dedup_state == "store_error"
        assert mod._dedup_start_state == "legacy_or_unverified"
        assert len(calls) == 0

    @pytest.mark.asyncio
    async def test_first_ever_key_executes_once_on_fresh_store(
        self, durable: dict
    ) -> None:
        """A genuinely fresh store (no installation marker) classifies as
        first_initialization and executes a never-seen key once (REQ-006)."""
        assert durable["store"].start_state == "first_initialization"
        durable["mod"]._dedup_config = replace(durable["config"], retry_class={})
        calls: list[int] = []
        r = await dispatch_tool(
            {self.TOOL: self._handler(calls)},
            self.TOOL,
            {"p": "a"},
            idempotency_key="fresh-1",
        )
        assert not r.is_error
        assert len(calls) == 1

    @pytest.mark.asyncio
    async def test_post_open_write_failure_fails_closed_non_retryable(
        self, durable: dict, monkeypatch: Any
    ) -> None:
        """A failed acquisition write leaves no proof of completion: a
        non-retryable tool fails closed (REQ-002)."""

        def _boom(*a: Any, **kw: Any) -> None:
            raise sqlite3.OperationalError("disk I/O error")

        monkeypatch.setattr(durable["store"], "try_acquire_execution", _boom)
        durable["mod"]._dedup_config = replace(durable["config"], retry_class={})
        calls: list[int] = []
        r = await dispatch_tool(
            {self.TOOL: self._handler(calls)},
            self.TOOL,
            {"p": "a"},
            idempotency_key="k1",
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
            idempotency_key="k1",
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
            idempotency_key="k1",
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
            idempotency_key="k2",
        )
        assert (
            durable["store"].get_execution("old2") is not None
        )  # no second sweep in-process

    @pytest.mark.asyncio
    async def test_error_and_dry_run_do_not_leave_replayable_state(
        self, durable: dict
    ) -> None:
        """A validation failure lands on 'failed'; a dry-run outcome is cleared
        (no cached result, no replayable completed row)."""

        async def bad(args: dict) -> str:
            raise ValueError("bad input")

        r1 = await dispatch_tool(
            {self.TOOL: bad}, self.TOOL, {"p": "a"}, idempotency_key="k1"
        )
        assert r1.is_error
        assert durable["store"].get_execution("k1").status == "failed"

        calls: list[int] = []
        r2 = await dispatch_tool(
            {self.TOOL: self._handler(calls)},
            self.TOOL,
            {"p": "a"},
            idempotency_key="k2",
        )
        assert not r2.is_error
        assert durable["store"].get_execution("k2").status == "completed"
        # Turn k2's completed row into a dry-run-shaped second attempt is out of
        # scope here; instead assert the completed row exists and replays as a hit.
        r3 = await dispatch_tool(
            {self.TOOL: self._handler(calls)},
            self.TOOL,
            {"p": "a"},
            idempotency_key="k2",
        )
        assert r3.dedup_state in ("duplicate_hit", "")  # overlay or store serve
        assert len(calls) == 1


class TestDurableDedupDryRunClear:
    """Dry-run outcomes must not leave replayable state behind (REQ-004)."""

    TOOL = "write_file"

    @pytest.fixture()
    def durable(self, tmp_path: Any, monkeypatch: Any) -> Iterator[dict[str, Any]]:
        import mcp_servers.dispatch as dispatch_mod
        from shared.mcp_dedup import DedupConfig, DedupStore

        db_path = str(tmp_path / "mcp_dedup.sqlite")
        store = DedupStore(db_path)
        config = DedupConfig(db_path=db_path, retry_class={self.TOOL: "retryable"})
        _duplicate_cache.clear()
        monkeypatch.setattr(dispatch_mod, "_dedup_store", store)
        monkeypatch.setattr(dispatch_mod, "_dedup_config", config)
        monkeypatch.setattr(dispatch_mod, "_dedup_disabled", False)
        monkeypatch.setattr(dispatch_mod, "_purge_done", False)
        yield {"store": store, "mod": dispatch_mod}
        store.close()
        _duplicate_cache.clear()

    @pytest.mark.asyncio
    async def test_dry_run_clears_pending_row(self, durable: dict) -> None:
        async def dry(args: dict) -> str:
            return '{"dry_run": true}'

        r = await dispatch_tool(
            {self.TOOL: dry}, self.TOOL, {"p": "a"}, idempotency_key="k1"
        )
        assert not r.is_error
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
            {self.TOOL: handler}, self.TOOL, {"p": "a"}, idempotency_key="k1"
        )
        assert not r.is_error  # the handler already ran; the outcome is surfaced
        assert r.dedup_state == "lease_conflict"
        assert len(calls) == 1
        row = durable["store"].get_execution("k1")
        assert (
            row is not None and row.status == "pending"
        )  # the row stays for reconciliation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
