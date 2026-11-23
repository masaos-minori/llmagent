"""scripts/mcp_servers/dispatch.py

Tool dispatch helpers extracted from mcp/server.py, so MCP servers can import
dispatch_tool without pulling in the full MCPServer base class.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
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

from mcp_servers.dedup_gate import (
    _IDEMPOTENCY_CACHE_MAX_ENTRIES as _IDEMPOTENCY_CACHE_MAX_ENTRIES,
)
from mcp_servers.dedup_gate import (
    _IDEMPOTENCY_CACHE_TTL_SECONDS as _IDEMPOTENCY_CACHE_TTL_SECONDS,
)
from mcp_servers.dedup_gate import (
    _OWNED_STATES,
    DispatchResult,
    ToolArgs,
    _dedup_decision,
    _duplicate_cache,
    _idem_now,
    _idem_store,
    _LeaseHeartbeat,
    _new_owner_id,
)
from mcp_servers.models import CallToolResponse

logger = logging.getLogger(__name__)

# The durable-dedup decision machinery (DispatchResult, ToolArgs, the overlay
# cache, the owner nonce, the acquisition-branch mapping, the owned-state set)
# lives in mcp_servers.dedup_gate and is re-exported here: every consumer keeps
# importing it from mcp_servers.dispatch, and the re-exported `_duplicate_cache`
# is the same object the gate module reads and writes.

# Canonical side-effect membership (ADR-004, sideeffect001): the single source
# in shared.tool_constants, shared with the HTTP fail-closed gate, the
# tool_policy static classification, and the server.py REQ-004 boundary.
_write_tools = ALL_SIDE_EFFECTING_TOOLS


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


def _normalize_args_hash(args: ToolArgs) -> str:
    """Deterministic hash of arguments so logically identical arguments match
    regardless of insertion order."""
    serialized = json.dumps(args, sort_keys=True, default=str)
    return sha256(serialized.encode("utf-8")).hexdigest()


def _is_dry_run_output(output: str) -> bool:
    """UNK-01: best-effort dry-run detection on the output string."""
    return any(marker in output for marker in _IDEMPOTENCY_DRY_RUN_MARKERS)


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


def _overlay_lookup(
    key: str,
    name: str,
    args_hash: str,
) -> DispatchResult | None:
    """Degraded-mode overlay read: a live hit, a reuse rejection, or ``None``.

    Without a durable store the overlay is the only record, so the reused-key
    rejection lives here on that path; on the durable path the same rejection
    comes from the acquisition's ``contract_mismatch`` (REQ-001, REQ-007).
    """
    entry = _duplicate_cache.get(key)
    if entry is None:
        return None
    if entry.tool_name == name and entry.args_hash == args_hash:
        if entry.expires_at > _idem_now():
            logger.info(
                "Duplicate tool call detected: %s (key=%s)",
                name,
                key,
            )
            return entry.result
        # Expired: drop it; the degraded decision below reports it.
        _duplicate_cache.pop(key, None)
        return None
    # same key reused with different content -> reject.
    logger.warning(
        "Idempotency key reused with different content: key=%s tool=%s",
        key,
        name,
    )
    return DispatchResult(
        output=(
            f"Idempotency key {key!r} reused with different content for tool {name!r}"
        ),
        is_error=True,
        error_type="idempotency_key_reused",
    )


async def _dispatch_with_heartbeat(
    handler: Callable[[ToolArgs], Awaitable[str]],
    args: ToolArgs,
    heartbeat: _LeaseHeartbeat | None,
) -> str:
    """Run the handler under the lease heartbeat, then stop it.

    The heartbeat is stopped before this call returns or raises, so no renewal
    transaction races the dispatcher's owner-conditional finalization.
    """
    if heartbeat is None:
        return await handler(args)
    heartbeat.start()
    try:
        return await handler(args)
    finally:
        await heartbeat.stop()


def _to_call_tool_response(r: DispatchResult) -> CallToolResponse:
    """Convert a DispatchResult into a CallToolResponse."""
    return CallToolResponse(
        result=r.output, is_error=r.is_error, dedup_state=r.dedup_state
    )


@dataclass(frozen=True)
class _DedupDecision:
    """Outcome of the single pre-dispatch dedup decision for one call."""

    early: DispatchResult | None
    dedup_state: str
    store: DedupStore | None = None
    owner: str | None = None
    snapshot: dict[str, str] | None = None


_NO_DEDUP = _DedupDecision(None, "")


def _degraded_decision(key: str, name: str, args_hash: str) -> _DedupDecision:
    """Degraded (storeless) decision: the overlay is the only record, and the
    audited asymmetry decides the rest (REQ-007).

    Non-retryable tools fail closed; retryable tools proceed with the audited
    ``store_error`` marker. The typed start state is captured in
    ``_dedup_start_state`` by ``_dedup_context()``. No injected policy entry ->
    non-retryable (fail closed, no fallback constant).
    """
    overlay = _overlay_lookup(key, name, args_hash)
    if overlay is not None:
        return _DedupDecision(overlay, "")
    if not _retryable(name):
        logger.warning(
            "Durable dedup unavailable (start state=%s); call to tool %r refused "
            "(non-retryable)",
            _dedup_start_state or "disabled",
            name,
        )
        return _DedupDecision(
            DispatchResult(
                output=(f"Dedup store unavailable; call to tool {name!r} refused"),
                is_error=True,
                error_type="dedup_store_error",
                dedup_state="store_error",
            ),
            "store_error",
        )
    return _DedupDecision(None, "store_error")


def _acquire_dedup(key: str, name: str, args_hash: str) -> _DedupDecision:
    """Run the one dedup decision a keyed side-effecting call is allowed (REQ-001).

    With a durable store this is the single ``try_acquire_execution`` call through
    ``_dedup_decision``; without one it is the degraded overlay decision. A store
    failure never blocks silently: retryable tools dispatch with the audited
    ``store_error`` marker, non-retryable tools fail closed (Plan Risks).
    """
    store, config = _dedup_context()
    if store is None or config is None:
        return _degraded_decision(key, name, args_hash)
    _purge_once(store, config)
    snapshot = build_execution_snapshot()
    candidate_owner = _new_owner_id()
    retryable = _retryable(name)
    try:
        early, dedup_state = _dedup_decision(
            store,
            config,
            key,
            name,
            args_hash,
            snapshot,
            candidate_owner,
            retryable=retryable,
        )
    except (sqlite3.Error, OSError, DedupStoreError) as exc:
        logger.warning("dedup acquisition failed: %s", exc)
        early = None
        dedup_state = "store_error"
        if not retryable:
            early = DispatchResult(
                output=(f"Dedup store unavailable; call to tool {name!r} refused"),
                is_error=True,
                error_type="dedup_store_error",
                dedup_state="store_error",
            )
    if early is not None:
        return _DedupDecision(early, dedup_state)
    # Only a fresh acquisition or a recovery reacquisition is owner-scoped; the
    # dispatcher finalizes the row it owns and nothing else.
    owner = candidate_owner if dedup_state in _OWNED_STATES else None
    return _DedupDecision(None, dedup_state, store, owner, snapshot)


def _finalize_dedup(
    store: DedupStore | None,
    key: str,
    owner: str | None,
    snapshot: dict[str, str] | None,
    heartbeat: _LeaseHeartbeat | None,
    dry_run: bool,
    result: str,
    dedup_state: str,
) -> str:
    """Close the ledger row this call owns after the handler returned.

    Returns the dedup_state to report: a lost lease (renewal failed during the
    handler, or a finalization write that matched zero rows) is surfaced as
    ``lease_conflict`` and never re-dispatches the handler (AC-4); a dry-run
    outcome leaves no replayable state behind.
    """
    if store is None or owner is None or snapshot is None:
        return dedup_state
    if heartbeat is not None and heartbeat.renewal_lost:
        return "lease_conflict"
    if dry_run:
        _store_op(store, lambda: store.clear(key), "clear-dry-run")
        return dedup_state
    if not _store_op(
        store,
        lambda: store.record_completed(key, snapshot, result, owner),
        "record-completed",
    ):
        return "lease_conflict"
    return dedup_state


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
    (try_acquire_execution) in mcp_servers.dedup_gate: completed results with a
    matching execution snapshot are replayed, a live lease refuses as
    in_progress, an expired lease replays for retryable tools only through
    reconcile-then-reacquire and is refused for non-retryable ones, terminal
    rows refuse replay, and the branch taken is reported in dedup_state. The
    owner lease is renewed while the handler runs, and a lease lost during
    dispatch is reported as lease_conflict without re-dispatching the handler.
    The in-process overlay cache is read and written only on the degraded path
    where no durable store is available.
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
    # executes). With a durable store the one acquisition is the only decision
    # point and the in-process overlay is neither read nor written; the overlay
    # serves the degraded (storeless) path only (REQ-001, REQ-007).
    key = idempotency_key
    side_effecting = _is_side_effecting(name)
    args_hash = _normalize_args_hash(args) if (key and side_effecting) else ""
    store_key = key if key else ""
    decision = (
        _acquire_dedup(key, name, args_hash) if (key and side_effecting) else _NO_DEDUP
    )
    if decision.early is not None:
        return decision.early
    store = decision.store
    owner = decision.owner
    snapshot_at_start = decision.snapshot
    dedup_state = decision.dedup_state

    heartbeat = (
        _LeaseHeartbeat(store, store_key, owner)
        if store is not None and owner is not None
        else None
    )
    try:
        result = await _dispatch_with_heartbeat(handler, args, heartbeat)
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
    dedup_state = _finalize_dedup(
        store,
        store_key,
        owner,
        snapshot_at_start,
        heartbeat,
        dry_run,
        result,
        dedup_state,
    )
    dispatched_result = DispatchResult(
        output=result, is_error=False, dedup_state=dedup_state
    )
    # Cache only real, successful, non-dry-run results, and only on the degraded
    # path: on the durable path the store is the record and a replay is served
    # from it, so the overlay stays empty (REQ-001, T-6).
    if key and side_effecting and store is None and not dry_run:
        _idem_store(key, name, args_hash, dispatched_result, _idem_now())
    return dispatched_result
