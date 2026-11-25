"""scripts/mcp_servers/dedup_gate.py — durable-dedup gate of the MCP dispatcher.

Split from mcp_servers.dispatch under plan
plans/20261123-130937_mcpai001_atomic-dedup-state-machine.md (REQ-008): the
typed-acquisition branch mapping, the refusal constructors, the degraded-mode
overlay cache, and the owner-nonce helper live here so the dispatcher and this
module both stay under the 24576 B size gate. The module imports only shared/
and the standard library and never imports mcp_servers.dispatch; the dispatcher
re-exports these names and passes its already-resolved retry permission and its
monotonic clock reading as explicit arguments, keeping the gate policy-agnostic
like the store (Plan D-4).
"""

from __future__ import annotations

import asyncio
import logging
import secrets
import sqlite3
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any

from shared.mcp_dedup import DedupLeaseConflict, DedupStore, DedupStoreConfig

logger = logging.getLogger(__name__)

ToolArgs = dict[str, Any]


@dataclass(frozen=True)
class DispatchResult:
    """Typed result from MCPServer.dispatch() and dispatch_tool.

    Error classification taxonomy (when is_error=True):
    - ``validation_error``: input validation failure (ValueError from handler)
    - ``unknown_tool``: tool name not found in dispatch table
    - ``invalid_tool_name``: tool name is empty or not a string
    - ``idempotency_key_reused``: same key reused with different content
    - ``dedup_in_progress``: a live owner lease already holds this key
    - ``dedup_unreplayable``: terminal/uncertain durable outcome refused
      (reconciliation_required, outcome_unknown, replay_unavailable)
    - ``dedup_store_error``: durable dedup store unavailable for a non-retryable tool
    - ``dispatch_error``: generic dispatch failure (no specific category)
    - ``idempotency_key_required``: side-effecting call without an idempotency key

    ``dedup_state`` carries the durable-dedup branch taken: ``""`` (no dedup
    branch), ``duplicate_hit``, ``replayed``, ``store_error``,
    ``in_progress``, ``reconciliation_required``, ``interrupted``,
    ``outcome_unknown``, ``replay_unavailable``, ``lease_conflict``.

    ``execution_mode`` carries what the call actually did: ``preview`` (the
    handler ran as a preview), ``applied`` (the handler ran for real), ``no_op``
    (the handler did not run: replay, refusal, key rejection, unknown tool), or
    ``""`` when no dispatcher outcome was attached. ``side_effect_applied`` is
    True only for an applied success on a side-effecting tool. Both are written
    by the dispatcher, not derived from ``error_type`` or ``dedup_state``.
    """

    output: str
    is_error: bool
    error_type: str | None = None
    dedup_state: str = ""
    execution_mode: str = ""
    side_effect_applied: bool = False

    @property
    def outcome(self) -> str:
        """Return 'error' if is_error, otherwise 'ok'."""
        return "error" if self.is_error else "ok"


# --- Idempotency overlay cache ---------------------------------
#
# The caller (Agent) owns key generation: one UUID per logical call, reused
# across retries of that call. A call without a key is never cached and always
# executes. The cache is keyed so that reusing a key with different content is
# rejected rather than served. Every read and write takes the caller's clock
# reading so the dispatcher's `_idem_now` test seam governs both sides.

_IDEMPOTENCY_CACHE_TTL_SECONDS: float = 3600.0
_IDEMPOTENCY_CACHE_MAX_ENTRIES: int = 1024


@dataclass(frozen=True)
class _CacheEntry:
    tool_name: str
    args_hash: str
    result: DispatchResult
    expires_at: float


_duplicate_cache: OrderedDict[str, _CacheEntry] = OrderedDict()


def _idem_now() -> float:
    """Monotonic time source for TTL. Overridable in tests."""
    return time.monotonic()


def _idem_evict(now: float) -> None:
    """Drop expired entries, then evict oldest-first past the max entry count."""
    for key in [k for k, entry in _duplicate_cache.items() if entry.expires_at <= now]:
        _duplicate_cache.pop(key)
    while len(_duplicate_cache) > _IDEMPOTENCY_CACHE_MAX_ENTRIES:
        _duplicate_cache.popitem(last=False)


def _idem_store(
    key: str, name: str, args_hash: str, result: DispatchResult, now: float
) -> None:
    """Store a successful result with TTL bookkeeping and eviction."""
    _idem_evict(now)
    _duplicate_cache[key] = _CacheEntry(
        tool_name=name,
        args_hash=args_hash,
        result=result,
        expires_at=now + _IDEMPOTENCY_CACHE_TTL_SECONDS,
    )


def _new_owner_id() -> str:
    """Per-call owner nonce; scopes every lease/ finalize write to this call."""
    return secrets.token_hex(16)


def _refusal_interrupted(
    store: DedupStore,
    key: str,
    name: str,
) -> tuple[DispatchResult, str]:
    """Refusal for a `reconciliation_required` row the caller may not reopen.

    The acquisition result carries no row status and `lease_expires_epoch` is
    `None` for every refusal, so the status is read once here through the
    public read-only `get_execution()`: an `interrupted` row is a cancelled side
    effect refused for replay (tag `interrupted`), an expired `pending` row
    keeps today's `reconciliation_required` tag. The read mutates nothing, so
    the row and its history stay exactly as stored (AC-3).
    """
    row = store.get_execution(key)
    state = (
        "interrupted"
        if row is not None and row.status == "interrupted"
        else "reconciliation_required"
    )
    logger.warning(
        "Dedup row (%s) needs reconciliation; call to tool %r refused (recovery "
        "outside the declared retry policy): key=%s",
        state,
        name,
        key,
    )
    return (
        DispatchResult(
            output=(
                f"Interrupted call for idempotency key {key!r} needs "
                f"reconciliation before retry for tool {name!r} "
                "(non-retryable)"
            ),
            is_error=True,
            error_type="dedup_unreplayable",
            dedup_state=state,
        ),
        state,
    )


def _dedup_decision(
    store: DedupStore,
    config: DedupStoreConfig,
    key: str,
    name: str,
    args_hash: str,
    snapshot: dict[str, str],
    owner_id: str,
    *,
    retryable: bool,
) -> tuple[DispatchResult | None, str]:
    """One typed acquisition plus start-state mapping (Plan D-5/D-7).

    Returns ``(early_result, dedup_state)``: a non-None early_result is the
    final DispatchResult (refusal or cached replay); None means "dispatch the
    handler" carrying the reported dedup_state. ``replayed`` marks the
    retryable reconciliation reacquisition; both it and a fresh acquisition are
    owner-scoped (dedup_state in _OWNED_STATES), every other branch is not.
    ``retryable`` is the dispatcher's already-resolved declared policy: the gate
    never reads the tool-policy map (D-4).
    """
    acq = store.try_acquire_execution(
        key,
        name,
        args_hash,
        snapshot,
        owner_id,
        allow_interrupted_recovery=retryable,
    )
    if acq.status == "acquired":
        return None, ""
    if acq.status == "contract_mismatch":
        # durable rows honor the same reuse rejection.
        logger.warning(
            "Idempotency key reused with different content: key=%s tool=%s",
            key,
            name,
        )
        return (
            DispatchResult(
                output=(
                    f"Idempotency key {key!r} reused with "
                    f"different content for tool {name!r}"
                ),
                is_error=True,
                error_type="idempotency_key_reused",
            ),
            "",
        )
    if acq.status == "replay_completed":
        served = DispatchResult(
            output=str(acq.result), is_error=False, dedup_state="duplicate_hit"
        )
        logger.info(
            "Duplicate tool call served from durable store: %s (key=%s)", name, key
        )
        return served, "duplicate_hit"
    if acq.status == "in_progress":
        logger.warning(
            "Tool call already in progress for idempotency key: key=%s tool=%s",
            key,
            name,
        )
        return (
            DispatchResult(
                output=(
                    f"Call for idempotency key {key!r} is already in progress "
                    f"for tool {name!r}"
                ),
                is_error=True,
                error_type="dedup_in_progress",
                dedup_state="in_progress",
            ),
            "in_progress",
        )
    if acq.status == "reconciliation_required":
        if retryable:
            # Canonical replay for retryable tools: reconcile the expired lease
            # (pending -> interrupted + history), then one reacquisition.
            store.reconcile_execution(key)
            acq = store.try_acquire_execution(
                key,
                name,
                args_hash,
                snapshot,
                owner_id,
                allow_interrupted_recovery=True,
            )
            if acq.status == "acquired":
                return None, "replayed"
        else:
            return _refusal_interrupted(store, key, name)
    if acq.status == "outcome_unknown":
        if retryable:
            # Attempt cap reached: audited degraded dispatch (overlay-only marker).
            logger.warning(
                "dedup outcome unknown (attempt %d of %d); tool %r dispatches "
                "degraded for key=%s",
                acq.attempt_number,
                store.max_attempts,
                name,
                key,
            )
            return None, "store_error"
        logger.warning(
            "Dedup outcome unknown (attempt cap reached); call to tool %r refused "
            "(non-retryable): key=%s",
            name,
            key,
        )
        return (
            DispatchResult(
                output=(
                    f"Outcome unknown for idempotency key {key!r} (attempt cap "
                    f"reached); call to tool {name!r} refused (non-retryable)"
                ),
                is_error=True,
                error_type="dedup_unreplayable",
                dedup_state="outcome_unknown",
            ),
            "outcome_unknown",
        )
    # replay_unavailable: terminal evidence (completed with a snapshot
    # mismatch or a truncated payload, or failed). Refused in every retry
    # class; the force-reset path is gone (mcpdl002 D-5).
    logger.warning(
        "Terminal dedup row refuses replay: key=%s tool=%s attempt=%d",
        key,
        name,
        acq.attempt_number,
    )
    return (
        DispatchResult(
            output=(
                f"Prior call for idempotency key {key!r} is terminal (completed "
                f"with a different execution snapshot, or failed); replay refused "
                f"for tool {name!r}"
            ),
            is_error=True,
            error_type="dedup_unreplayable",
            dedup_state="replay_unavailable",
        ),
        "replay_unavailable",
    )


# dedup_state values whose dispatch is owner-scoped (the row was acquired by
# this call's owner_id and must be finalized by it).
_OWNED_STATES: frozenset[str] = frozenset({"", "replayed"})


class _LeaseHeartbeat:
    """Keeps the owner lease alive while the handler runs (Plan D-3, REQ-003).

    An asyncio task renews every ``store.lease_seconds / 2`` through the store's
    owner-conditional ``renew_lease()``: a renewal attempt only succeeds while
    this call still owns the row, so a lost lease surfaces as
    ``DedupLeaseConflict`` instead of silently handing the key to another
    caller. Either renewal failure sets ``renewal_lost`` and stops the loop; the
    dispatcher reads the flag at finalization and never re-dispatches (AC-4).
    Store writes stay inside the event loop, as short ``BEGIN IMMEDIATE``
    transactions under the store's own lock.
    """

    def __init__(self, store: DedupStore, key: str, owner_id: str) -> None:
        self._store = store
        self._key = key
        self._owner_id = owner_id
        self.renewal_lost = False
        self._task: asyncio.Task[None] | None = None

    def start(self) -> None:
        """Schedule the renewal loop. Idempotent."""
        if self._task is not None:
            return
        self._task = asyncio.create_task(self._renew_during_dispatch())

    async def stop(self) -> None:
        """Cancel the loop and await it so no renewal races finalization."""
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None

    async def _renew_during_dispatch(self) -> None:
        interval = self._store.lease_seconds / 2
        while True:
            await asyncio.sleep(interval)
            try:
                self._store.renew_lease(self._key, self._owner_id)
            except DedupLeaseConflict as exc:
                logger.warning(
                    "dedup lease expired during dispatch (key=%s owner=%s): %s",
                    self._key,
                    self._owner_id,
                    exc,
                )
                self.renewal_lost = True
                return
            except (sqlite3.Error, OSError) as exc:
                logger.warning(
                    "dedup lease renewal failed (key=%s): %s", self._key, exc
                )
                self.renewal_lost = True
                return
