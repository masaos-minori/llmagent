"""tests/mcp_servers/test_mcp_dispatch_concurrency.py

Dispatcher-level concurrency and lease-protection pins for plan
plans/20261123-130937_mcpai001_atomic-dedup-state-machine.md: exactly one
handler execution per logical call under 100 concurrent callers (AC-1), and the
lease heartbeat that keeps the owner lease alive while the handler runs and
surfaces a lost lease without re-dispatch (AC-2, AC-4).
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from typing import Any

import pytest
from mcp_servers.dispatch import _duplicate_cache, dispatch_tool
from shared.mcp_dedup import DedupLeaseConflict, DedupStore, DedupStoreConfig

TOOL = "write_file"


def _wire_store(
    monkeypatch: Any,
    store: DedupStore,
    db_path: str,
    *,
    retryable: bool = False,
) -> None:
    """Inject a per-test durable store through the dispatcher seam."""
    import mcp_servers.dispatch as dispatch_mod

    _duplicate_cache.clear()
    monkeypatch.setattr(dispatch_mod, "_dedup_store", store)
    monkeypatch.setattr(dispatch_mod, "_dedup_config", _config(db_path))
    monkeypatch.setattr(dispatch_mod, "_dedup_disabled", False)
    monkeypatch.setattr(dispatch_mod, "_dedup_start_state", None)
    monkeypatch.setattr(dispatch_mod, "_purge_done", False)
    monkeypatch.setattr(
        dispatch_mod,
        "_tool_retry_policies",
        {TOOL: "same_logical_call_only"} if retryable else {},
    )


def _config(db_path: str) -> DedupStoreConfig:
    return DedupStoreConfig(
        db_path=db_path,
        retention_days=14,
        pending_timeout_minutes=10,
    )


def _handler(calls: list[int], delay: float, events: list[str] | None = None) -> Any:
    """Counting handler that stays in flight long enough to be contended.

    `events` records the handler's own end, so a test can tell a renewal that
    happened while the handler ran from one that only happened after it.
    """

    async def handler(args: dict) -> str:
        calls.append(1)
        await asyncio.sleep(delay)
        if events is not None:
            events.append("handler-end")
        return "wrote"

    return handler


class TestConcurrentDispatch:
    """One logical call, 100 gathered callers (Plan T-1).

    All contention goes through the store's owner lease, so the test measures
    the dispatcher's decision path rather than OS scheduling.
    """

    @pytest.fixture()
    def durable(self, tmp_path: Any, monkeypatch: Any) -> Iterator[DedupStore]:
        """Per-test durable store, injected the way TestDurableDedup does."""
        db_path = str(tmp_path / "mcp_dedup.sqlite")
        store = DedupStore(db_path)
        _wire_store(monkeypatch, store, db_path)
        yield store
        store.close()
        _duplicate_cache.clear()

    @pytest.mark.asyncio
    async def test_100_concurrent_callers_execute_handler_exactly_once(
        self, durable: DedupStore
    ) -> None:
        """AC-1: 100 simultaneous callers of one key execute the handler once."""
        calls: list[int] = []
        results = await asyncio.gather(
            *(
                dispatch_tool(
                    {TOOL: _handler(calls, 0.2)}, TOOL, {"p": "a"}, idempotency_key="k1"
                )
                for _ in range(100)
            )
        )
        assert len(calls) == 1
        executed = [r for r in results if r.dedup_state == "" and not r.is_error]
        assert len(executed) == 1
        assert executed[0].output == "wrote"
        for res in results:
            if res is executed[0]:
                continue
            assert res.dedup_state in {"in_progress", "duplicate_hit"}
            if res.dedup_state == "in_progress":
                assert res.error_type == "dedup_in_progress"
        assert durable.get_execution("k1") is not None


class TestLeaseHeartbeat:
    """Short-lease cases for the renewal heartbeat (Plan T-2a/T-2b)."""

    LEASE_SECONDS = 1

    @pytest.fixture()
    def short_lease(self, tmp_path: Any, monkeypatch: Any) -> dict[str, Any]:
        """Durable store with a 1 s lease and a counting renew_lease wrapper."""
        db_path = str(tmp_path / "mcp_dedup.sqlite")
        store = DedupStore(db_path, lease_seconds=self.LEASE_SECONDS)
        _wire_store(monkeypatch, store, db_path)
        stats = {"renew": 0, "events": [], "store": store, "db_path": db_path}
        real_renew = store.renew_lease

        def counting_renew(key: str, owner_id: str, **kwargs: Any) -> None:
            stats["renew"] += 1
            stats["events"].append("renew")
            real_renew(key, owner_id, **kwargs)

        monkeypatch.setattr(store, "renew_lease", counting_renew)
        yield stats
        store.close()
        _duplicate_cache.clear()

    @pytest.fixture()
    def renewal_blocked(self, tmp_path: Any, monkeypatch: Any) -> dict[str, Any]:
        """Same short-lease store with renewal refused (lost-lease simulation)."""
        db_path = str(tmp_path / "mcp_dedup.sqlite")
        store = DedupStore(db_path, lease_seconds=self.LEASE_SECONDS)
        _wire_store(monkeypatch, store, db_path)
        stats = {"renew": 0, "store": store, "db_path": db_path}

        def blocked_renew(key: str, owner_id: str, **kwargs: Any) -> None:
            stats["renew"] += 1
            raise DedupLeaseConflict("lease no longer held by this owner")

        monkeypatch.setattr(store, "renew_lease", blocked_renew)
        yield stats
        store.close()
        _duplicate_cache.clear()

    @pytest.mark.asyncio
    async def test_lease_renewed_while_the_handler_runs(
        self, short_lease: dict
    ) -> None:
        """AC-2 (T-2a): a handler longer than half the lease still finalizes."""
        calls: list[int] = []
        events = short_lease["events"]
        res = await dispatch_tool(
            {TOOL: _handler(calls, self.LEASE_SECONDS * 1.2, events)},
            TOOL,
            {"p": "a"},
            idempotency_key="k1",
        )
        assert len(calls) == 1
        assert not res.is_error
        assert res.output == "wrote"
        assert res.dedup_state == ""
        # The renewal happened while the handler was still in flight, not as a
        # post-handler rescue: the lease never expired underneath the call.
        assert "renew" in events
        assert events.index("renew") < events.index("handler-end")
        row = short_lease["store"].get_execution("k1")
        assert row is not None and row.status == "completed"

    @pytest.mark.asyncio
    async def test_lost_lease_surfaces_without_redispatch(
        self, renewal_blocked: dict
    ) -> None:
        """AC-4 (T-2b): a refused renewal reports lease_conflict, once, no write."""
        calls: list[int] = []
        res = await dispatch_tool(
            {TOOL: _handler(calls, self.LEASE_SECONDS * 1.4)},
            TOOL,
            {"p": "a"},
            idempotency_key="k1",
        )
        assert len(calls) == 1  # never re-dispatched
        assert renewal_blocked["renew"] >= 1
        assert not res.is_error
        assert res.dedup_state == "lease_conflict"
        row = renewal_blocked["store"].get_execution("k1")
        assert row is not None and row.status == "pending"  # left for reconciliation
