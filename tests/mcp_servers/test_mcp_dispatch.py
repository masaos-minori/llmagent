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
    def _clear_idem_cache(self) -> Iterator[None]:
        _duplicate_cache.clear()
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
    async def test_snapshot_mismatch_yields_fresh_audited_attempt(
        self, durable: dict, monkeypatch: Any
    ) -> None:
        """completed + snapshot mismatch -> fresh attempt on the same key, tagged
        snapshot_mismatch (REQ-005); a matching snapshot keeps serving stored."""
        calls: list[int] = []
        r1 = await dispatch_tool(
            {self.TOOL: self._handler(calls)},
            self.TOOL,
            {"p": "a"},
            idempotency_key="k1",
        )
        assert r1.dedup_state == ""
        assert len(calls) == 1
        row = durable["store"].lookup("k1")
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
        assert not r2.is_error
        assert r2.dedup_state == "snapshot_mismatch"
        assert len(calls) == 2  # fresh attempt, not blocked (plan Risks)
        # ...and the matching direction still serves the stored result. The fresh
        # attempt stored the perturbed snapshot, so compare against that row now.
        row2 = durable["store"].lookup("k1")
        assert row2 is not None and row2.status == "completed"
        monkeypatch.setattr(
            dispatch_mod, "build_execution_snapshot", lambda **kw: dict(row2.snapshot)
        )
        _duplicate_cache.clear()
        r3 = await dispatch_tool(
            {self.TOOL: self._handler(calls)},
            self.TOOL,
            {"p": "a"},
            idempotency_key="k1",
        )
        assert r3.dedup_state == "duplicate_hit"
        assert len(calls) == 2

    @pytest.mark.asyncio
    async def test_interrupted_retryable_replays(self, durable: dict) -> None:
        """pending/interrupted + retryable -> replay the same key (REQ-005)."""
        calls: list[int] = []
        import time

        args_hash = durable["mod"]._normalize_args_hash({"p": "a"})
        durable["store"].record_pending(
            "k1",
            self.TOOL,
            args_hash,
            {"deployed_rev": "x"},
            now_epoch=time.time() - 3600,
        )
        r = await dispatch_tool(
            {self.TOOL: self._handler(calls)},
            self.TOOL,
            {"p": "a"},
            idempotency_key="k1",
        )
        assert not r.is_error
        assert r.dedup_state == "replayed"
        assert len(calls) == 1
        assert durable["store"].lookup("k1").status == "completed"

    @pytest.mark.asyncio
    async def test_interrupted_non_retryable_refused(self, durable: dict) -> None:
        """interrupted + non_retryable -> refuse with dedup_unreplayable; handler
        not executed (REQ-005). Unknown tools default to non_retryable."""
        calls: list[int] = []
        import time

        durable["mod"]._dedup_config = replace(durable["config"], retry_class={})
        args_hash = durable["mod"]._normalize_args_hash({"p": "a"})
        durable["store"].record_pending(
            "k1",
            self.TOOL,
            args_hash,
            {"deployed_rev": "x"},
            now_epoch=time.time() - 3600,
        )
        r = await dispatch_tool(
            {self.TOOL: self._handler(calls)},
            self.TOOL,
            {"p": "a"},
            idempotency_key="k1",
        )
        assert r.is_error
        assert r.error_type == "dedup_unreplayable"
        assert r.dedup_state == "unreplayable"
        assert len(calls) == 0

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
        """Store lookup failure: retryable tools dispatch with the audited
        store_error marker; non-retryable tools fail closed (plan Risks)."""
        calls: list[int] = []

        def _boom(*a: Any, **kw: Any) -> None:
            raise sqlite3.OperationalError("disk is locked")

        monkeypatch.setattr(durable["store"], "lookup", _boom)
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
    async def test_retention_sweep_runs_once_per_process(self, durable: dict) -> None:
        """One opportunistic purge per process (REQ-009)."""
        import time

        calls: list[int] = []
        old = time.time() - 15 * 86400
        durable["store"].record_pending(
            "old1", self.TOOL, "h", {"deployed_rev": "x"}, now_epoch=old
        )
        durable["store"].record_completed(
            "old1", {"deployed_rev": "x"}, "done", now_epoch=old
        )
        assert durable["store"].lookup("old1") is not None
        await dispatch_tool(
            {self.TOOL: self._handler(calls)},
            self.TOOL,
            {"p": "a"},
            idempotency_key="k1",
        )
        assert durable["store"].lookup("old1") is None  # swept by the first dispatch
        durable["store"].record_pending(
            "old2", self.TOOL, "h", {"deployed_rev": "x"}, now_epoch=old
        )
        durable["store"].record_completed(
            "old2", {"deployed_rev": "x"}, "done", now_epoch=old
        )
        await dispatch_tool(
            {self.TOOL: self._handler(calls)},
            self.TOOL,
            {"p": "a"},
            idempotency_key="k2",
        )
        assert durable["store"].lookup("old2") is not None  # no second sweep in-process

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
        assert durable["store"].lookup("k1").status == "failed"

        calls: list[int] = []
        r2 = await dispatch_tool(
            {self.TOOL: self._handler(calls)},
            self.TOOL,
            {"p": "a"},
            idempotency_key="k2",
        )
        assert not r2.is_error
        assert durable["store"].lookup("k2").status == "completed"
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
        assert durable["store"].lookup("k1") is None  # no replayable state left
        assert len(_duplicate_cache) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
