"""scripts/mcp_servers/dispatch.py

Tool dispatch helpers extracted from mcp/server.py, so MCP servers can import
dispatch_tool without pulling in the full MCPServer base class.
"""

from __future__ import annotations

import asyncio
import json
import logging
import secrets
import sqlite3
import time
from collections import OrderedDict
from collections.abc import Awaitable, Callable, Iterable, Mapping
from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from shared.execution_snapshot import build_execution_snapshot
from shared.mcp_dedup import (
    DedupLeaseConflict,
    DedupStore,
    DedupStoreConfig,
    DedupStoreError,
    open_dedup_store,
)
from shared.tool_constants import ALL_SIDE_EFFECTING_TOOLS
from shared.tool_metadata import retry_policy_is_retryable

from mcp_servers.models import CallToolResponse

logger = logging.getLogger(__name__)

ToolArgs = dict[str, Any]

# Canonical side-effect membership (ADR-004, sideeffect001): the single source
# in shared.tool_constants, shared with the HTTP fail-closed gate, the
# tool_policy static classification, and the server.py REQ-004 boundary.
_write_tools = ALL_SIDE_EFFECTING_TOOLS


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

    ``dedup_state`` carries the durable-dedup branch taken: ``""`` (no dedup
    branch), ``duplicate_hit``, ``replayed``, ``store_error``,
    ``in_progress``, ``reconciliation_required``, ``outcome_unknown``,
    ``replay_unavailable``, ``lease_conflict``.
    """

    output: str
    is_error: bool
    error_type: str | None = None
    dedup_state: str = ""

    @property
    def outcome(self) -> str:
        """Return 'error' if is_error, otherwise 'ok'."""
        return "error" if self.is_error else "ok"


# --- Idempotency cache ---------------------------------
#
# The caller (Agent) owns key generation: one UUID per logical call, reused
# across retries of that call. A call without a key is never cached and always
# executes. The cache is keyed so that reusing a key with different content is
# rejected rather than served.

_IDEMPOTENCY_CACHE_TTL_SECONDS: float = 3600.0
_IDEMPOTENCY_CACHE_MAX_ENTRIES: int = 1024

# UNK-01 resolution: dispatch_tool() only sees the final output string, so a
# dry-run result is recognised by a conservative marker scan rather than a
# structured signal. Matching errs toward *not* caching (i.e. always execute),
# which is the safe direction under ADR-004 (never report non-execution as
# success). Extend this tuple if a service emits a different marker.
_IDEMPOTENCY_DRY_RUN_MARKERS: tuple[str, ...] = (
    '"dry_run": true',
    '"dry_run":true',
    '"dry_run": True',
    '"dry_run":True',
    "(dry_run)",
)


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


def _normalize_args_hash(args: ToolArgs) -> str:
    """Deterministic hash of arguments so logically identical arguments match
    regardless of insertion order."""
    serialized = json.dumps(args, sort_keys=True, default=str)
    return sha256(serialized.encode("utf-8")).hexdigest()


def _is_dry_run_output(output: str) -> bool:
    """UNK-01: best-effort dry-run detection on the output string."""
    return any(marker in output for marker in _IDEMPOTENCY_DRY_RUN_MARKERS)


def _idem_evict() -> None:
    """Drop expired entries, then evict oldest-first past the max entry count."""
    now = _idem_now()
    for key in [k for k, entry in _duplicate_cache.items() if entry.expires_at <= now]:
        _duplicate_cache.pop(key)
    while len(_duplicate_cache) > _IDEMPOTENCY_CACHE_MAX_ENTRIES:
        _duplicate_cache.popitem(last=False)


def _idem_store(key: str, name: str, args_hash: str, result: DispatchResult) -> None:
    """Store a successful result with TTL bookkeeping and eviction."""
    _idem_evict()
    _duplicate_cache[key] = _CacheEntry(
        tool_name=name,
        args_hash=args_hash,
        result=result,
        expires_at=_idem_now() + _IDEMPOTENCY_CACHE_TTL_SECONDS,
    )


def _is_side_effecting(tool_name: str) -> bool:
    """Check if a tool name belongs to the write/dangerous/exec sets."""
    return tool_name in _write_tools


# --- Durable dedup store -------------------------------------------
#
# Inject-only process-wide store: the server bootstrap calls configure_dedup()
# with its own `[dedup]` table before serving (REQ-001); never configured ->
# `not_configured` start state and the in-process overlay. A store refusal
# (lost / replaced / legacy_or_unverified / schema_mismatch / identity_mismatch)
# is captured as a typed start state for the audit.

_dedup_store: DedupStore | None = None
_dedup_config: DedupStoreConfig | None = None
_dedup_disabled = False
_dedup_start_state: str | None = None
_purge_done = False
_tool_retry_policies: dict[str, str] = {}


def configure_dedup(store_config: DedupStoreConfig) -> None:
    """Open the shared store once from the injected config (bootstrap seam).

    `DedupStoreError` start states propagate: a process whose validated
    `[dedup]` values disagree with the store must not start (REQ-007).
    """
    global _dedup_store, _dedup_config, _dedup_disabled, _dedup_start_state
    _dedup_store = open_dedup_store(store_config)
    _dedup_config = store_config
    _dedup_disabled = False
    _dedup_start_state = None


def configure_tool_retry_policies(entries: Iterable[Mapping[str, Any]]) -> None:
    """Inject this process's declared retry_policy metadata (bootstrap seam).

    Declared `retry_policy` is the retry authority (REQ-005); tools absent
    from the map stay non-retryable (fail-safe, no fallback constant). Entries
    without a name or retry_policy are skipped (non-production tool tables
    only; production validation rejects them).
    """
    global _tool_retry_policies
    _tool_retry_policies = {
        str(entry["name"]): str(entry["retry_policy"])
        for entry in entries
        if entry.get("name") and entry.get("retry_policy")
    }


def _retryable(name: str) -> bool:
    """Declared-policy lookup; a tool with no policy entry is non-retryable."""
    return retry_policy_is_retryable(_tool_retry_policies.get(name))


def _dedup_context() -> tuple[DedupStore | None, DedupStoreConfig | None]:
    """Return the (store, config) pair, or (None, None) when durable dedup is disabled."""
    global _dedup_disabled, _dedup_start_state
    if _dedup_store is not None and _dedup_config is not None:
        return _dedup_store, _dedup_config
    if _dedup_disabled:
        return None, None
    _dedup_disabled = True
    _dedup_start_state = "not_configured"
    logger.warning(
        "durable dedup store not configured: configure_dedup() was never called; "
        "overlay-only fallback"
    )
    return None, None


def _purge_once(store: DedupStore, config: DedupStoreConfig) -> None:
    """Run the retention sweep at most once per process."""
    global _purge_done
    if _purge_done:
        return
    _purge_done = True
    try:
        store.purge_expired(config.retention_days)
    except (sqlite3.Error, OSError) as exc:
        logger.warning("dedup retention sweep failed: %s", exc)


def _store_op(store: DedupStore, op: Callable[[], Any], label: str) -> bool:
    """Run one store mutation; a failed write degrades to the overlay, never blocks.

    A ``DedupLeaseConflict`` (zero-row owner-conditional update) means this
    call no longer owns the row: it is surfaced as a warning and the
    dispatcher never re-dispatches on it.
    """
    try:
        op()
        return True
    except DedupLeaseConflict as exc:
        logger.warning("dedup lease conflict (%s): %s", label, exc)
        return False
    except (sqlite3.Error, OSError) as exc:
        logger.warning("dedup store write failed (%s): %s", label, exc)
        return False


def _new_owner_id() -> str:
    """Per-call owner nonce; scopes every lease/ finalize write to this call."""
    return secrets.token_hex(16)


def _renew_lease_if_needed(
    store: DedupStore, key: str, owner_id: str, dispatched_at: float
) -> None:
    """Heartbeat for long handlers: renew once dispatch has consumed half the
    lease window. A lease lost during dispatch is surfaced without re-dispatch.
    """
    if time.monotonic() - dispatched_at <= store.lease_seconds / 2:
        return
    try:
        store.renew_lease(key, owner_id)
    except DedupLeaseConflict as exc:
        logger.warning(
            "dedup lease expired during dispatch (key=%s owner=%s): %s",
            key,
            owner_id,
            exc,
        )
    except (sqlite3.Error, OSError) as exc:
        logger.warning("dedup lease renewal failed (key=%s): %s", key, exc)


def _dedup_decision(
    store: DedupStore,
    config: DedupStoreConfig,
    key: str,
    name: str,
    args_hash: str,
    snapshot: dict[str, str],
    owner_id: str,
) -> tuple[DispatchResult | None, str]:
    """One typed acquisition plus start-state mapping (Plan D-5/D-7).

    Returns ``(early_result, dedup_state)``: a non-None early_result is the
    final DispatchResult (refusal or cached replay); None means "dispatch the
    handler" carrying the reported dedup_state. ``replayed`` marks the
    retryable reconciliation reacquisition; both it and a fresh acquisition are
    owner-scoped (dedup_state in _OWNED_STATES), every other branch is not.
    """
    acq = store.try_acquire_execution(key, name, args_hash, snapshot, owner_id)
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
        _idem_store(key, name, args_hash, served)
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
    retryable = _retryable(name)
    if acq.status == "reconciliation_required":
        if retryable:
            # Canonical replay for retryable tools: reconcile the expired lease
            # (pending -> interrupted + history), then one reacquisition.
            store.reconcile_execution(key)
            acq = store.try_acquire_execution(key, name, args_hash, snapshot, owner_id)
            if acq.status == "acquired":
                return None, "replayed"
        else:
            logger.warning(
                "Expired dedup lease needs reconciliation; call to tool %r refused "
                "(non-retryable): key=%s",
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
                    dedup_state="reconciliation_required",
                ),
                "reconciliation_required",
            )
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


def _to_call_tool_response(r: DispatchResult) -> CallToolResponse:
    """Convert a DispatchResult into a CallToolResponse."""
    return CallToolResponse(
        result=r.output, is_error=r.is_error, dedup_state=r.dedup_state
    )


async def dispatch_tool(
    table: Mapping[str, Callable[[ToolArgs], Awaitable[str]]],
    name: str,
    args: ToolArgs,
    idempotency_key: str | None = None,
) -> DispatchResult:
    """Route a tool call through a dispatch table.

    Returns a DispatchResult with output text and is_error flag.
    Raises for non-ValueError handler exceptions (caller is responsible for transport-level handling).
    ValueError from handlers is converted to an error result (user-input/validation errors).
    Unknown tool and empty name return error results without raising.
    If a non-empty idempotency_key is provided and name is side-effecting, the
    call is deduplicated: a matching prior call is served, a reused key with
    different content is rejected, and a keyless call always executes. Error and
    dry-run results are never cached. When the durable store is available the
    same contract holds across processes through one acquisition call
    (try_acquire_execution): completed results with a matching execution
    snapshot are replayed, a live lease refuses as in_progress, an expired
    lease replays for retryable tools only through reconcile-then-reacquire and
    is refused for non-retryable ones, terminal rows refuse replay, and the
    branch taken is reported in dedup_state.
    """
    if not isinstance(name, str) or not name.strip():
        logger.warning("dispatch_tool called with empty tool name")
        return DispatchResult(
            output="Tool name must be a non-empty string",
            is_error=True,
            error_type="invalid_tool_name",
        )

    handler = table.get(name)
    if handler is None:
        logger.warning("Unknown tool requested: %s", name)
        return DispatchResult(
            output=f"Unknown tool: {name}", is_error=True, error_type="unknown_tool"
        )

    # duplicate-check for side-effecting tools (a non-empty key is
    # required; a keyless call never touches the cache or the store and always
    # executes). The durable store is the truth; the overlay is a
    # completed-only fast path fed from it.
    key = idempotency_key
    side_effecting = _is_side_effecting(name)
    args_hash = _normalize_args_hash(args) if (key and side_effecting) else ""
    dedup_state = ""
    store: DedupStore | None = None
    store_key = ""
    owner: str | None = None
    snapshot_at_start: dict[str, str] | None = None

    if key and side_effecting:
        store_key = key
        entry = _duplicate_cache.get(key)
        if entry is not None:
            if entry.tool_name == name and entry.args_hash == args_hash:
                if entry.expires_at > _idem_now():
                    logger.info(
                        "Duplicate tool call detected: %s (key=%s)",
                        name,
                        idempotency_key,
                    )
                    return entry.result
                # Expired: drop it; the acquisition below decides.
                _duplicate_cache.pop(key, None)
            else:
                # same key reused with different content -> reject.
                logger.warning(
                    "Idempotency key reused with different content: key=%s tool=%s",
                    idempotency_key,
                    name,
                )
                return DispatchResult(
                    output=(
                        f"Idempotency key {idempotency_key!r} reused with "
                        f"different content for tool {name!r}"
                    ),
                    is_error=True,
                    error_type="idempotency_key_reused",
                )

        store, config = _dedup_context()
        if store is not None and config is not None:
            _purge_once(store, config)
            snapshot_at_start = build_execution_snapshot()
            candidate_owner = _new_owner_id()
            try:
                early, dedup_state = _dedup_decision(
                    store,
                    config,
                    key,
                    name,
                    args_hash,
                    snapshot_at_start,
                    candidate_owner,
                )
            except (sqlite3.Error, OSError, DedupStoreError) as exc:
                # Plan Risks mitigation: a store failure never blocks silently.
                # Retryable tools dispatch with an audited store_error marker;
                # non-retryable tools fail closed.
                logger.warning("dedup acquisition failed: %s", exc)
                early = None
                dedup_state = "store_error"
                if not _retryable(name):
                    early = DispatchResult(
                        output=(
                            f"Dedup store unavailable; call to tool {name!r} refused"
                        ),
                        is_error=True,
                        error_type="dedup_store_error",
                        dedup_state="store_error",
                    )
            if early is not None:
                return early
            if dedup_state in _OWNED_STATES:
                owner = candidate_owner
        else:
            # Init failure / disabled (typed start state captured in
            # _dedup_start_state): the audited asymmetry is unchanged.
            # Non-retryable tools fail closed; retryable tools
            # degrade to overlay-only store_error. No injected policy
            # entry -> non-retryable (fail closed, no fallback constant).
            is_retryable = _retryable(name)
            if not is_retryable:
                logger.warning(
                    "Durable dedup unavailable (start state=%s); call to tool %r "
                    "refused (non-retryable)",
                    _dedup_start_state or "disabled",
                    name,
                )
                return DispatchResult(
                    output=(f"Dedup store unavailable; call to tool {name!r} refused"),
                    is_error=True,
                    error_type="dedup_store_error",
                    dedup_state="store_error",
                )
            dedup_state = "store_error"

    dispatched_at = time.monotonic()
    try:
        result = await handler(args)
    except asyncio.CancelledError:
        # Owner-side voluntary interruption signal (dispatcher cancel path):
        # the owned pending row becomes 'interrupted' for the reconciliation
        # path before the cancellation propagates.
        if store is not None and owner is not None:
            _store_op(
                store,
                lambda: store.mark_interrupted(store_key, owner),
                "mark-interrupted",
            )
        raise
    except ValueError as e:
        logger.warning("Tool '%s' validation error: %s", name, e)
        # error results are never cached, but the durable row must not
        # stay pending: the owner finalizes pending -> failed.
        if store is not None and owner is not None:
            _store_op(
                store,
                lambda: store.record_failed(store_key, "validation_error", owner),
                "record-failed",
            )
        return DispatchResult(
            output=f"Validation error: {e}",
            is_error=True,
            error_type="validation_error",
            dedup_state=dedup_state,
        )
    except Exception as exc:  # noqa: BLE001 -- re-raised unchanged; the only added
        # behavior is closing the durable pending row (pending -> failed) before the
        # exception propagates to the transport-level handler.
        error_class = type(exc).__name__
        if store is not None and owner is not None:
            _store_op(
                store,
                lambda: store.record_failed(store_key, error_class, owner),
                "record-failed",
            )
        raise
    # All other exceptions (CancelledError aside, RuntimeError, IOError,
    # HTTPException, etc.) propagate to caller.

    dry_run = _is_dry_run_output(result)
    if store is not None and owner is not None and snapshot_at_start is not None:
        _renew_lease_if_needed(store, store_key, owner, dispatched_at)
        if dry_run:
            # A dry-run outcome leaves no replayable state behind.
            _store_op(store, lambda: store.clear(store_key), "clear-dry-run")
        elif not _store_op(
            store,
            lambda: store.record_completed(store_key, snapshot_at_start, result, owner),
            "record-completed",
        ):
            # The row no longer belongs to this call (or the write failed):
            # the handler already ran; surface the state, never re-dispatch.
            dedup_state = "lease_conflict"

    dispatched_result = DispatchResult(
        output=result, is_error=False, dedup_state=dedup_state
    )
    # Cache only real, successful, non-dry-run results.
    if key and side_effecting and not dry_run:
        _idem_store(key, name, args_hash, dispatched_result)
    return dispatched_result
