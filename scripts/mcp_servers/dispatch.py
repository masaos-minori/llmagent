"""scripts/mcp_servers/dispatch.py

Tool dispatch helpers extracted from mcp/server.py.
Kept separate so MCP servers can import dispatch_tool without pulling in the
full MCPServer base class.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from collections import OrderedDict
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from shared.execution_snapshot import build_execution_snapshot, snapshots_equal
from shared.mcp_dedup import (
    DedupConfig,
    DedupStore,
    load_dedup_config,
    open_dedup_store,
    retry_class,
)
from shared.tool_constants import (
    CICD_WRITE_TOOLS,
    DELETE_TOOLS,
    GIT_WRITE_TOOLS,
    GITHUB_DANGEROUS_TOOLS,
    GITHUB_WRITE_TOOLS,
    RAG_WRITE_TOOLS,
    SHELL_TOOLS,
    WRITE_TOOLS,
)

from mcp_servers.models import CallToolResponse

logger = logging.getLogger(__name__)

ToolArgs = dict[str, Any]

_write_tools = (
    set(WRITE_TOOLS)
    | set(DELETE_TOOLS)
    | set(GIT_WRITE_TOOLS)
    | set(RAG_WRITE_TOOLS)
    | set(CICD_WRITE_TOOLS)
    | set(GITHUB_WRITE_TOOLS)
    | set(GITHUB_DANGEROUS_TOOLS)
    | set(SHELL_TOOLS)
)


@dataclass(frozen=True)
class DispatchResult:
    """Typed result from MCPServer.dispatch() and dispatch_tool().

    Error classification taxonomy (when is_error=True):
    - ``validation_error``: input validation failure (ValueError from handler)
    - ``unknown_tool``: tool name not found in dispatch table
    - ``invalid_tool_name``: tool name is empty or not a string
    - ``idempotency_key_reused``: same key reused with different content
    - ``dedup_unreplayable``: interrupted call refused auto-replay (non-retryable tool)
    - ``dedup_store_error``: durable dedup store unavailable for a non-retryable tool
    - ``dispatch_error``: generic dispatch failure (no specific category)

    ``dedup_state`` carries the durable-dedup branch taken (REQ-005): ``""`` (no dedup
    branch), ``duplicate_hit``, ``snapshot_mismatch``, ``replayed``, ``result_truncated``,
    ``unreplayable``, ``store_error``.
    """

    output: str
    is_error: bool
    error_type: str | None = None
    dedup_state: str = ""

    @property
    def outcome(self) -> str:
        """Return 'error' if is_error, otherwise 'ok'."""
        return "error" if self.is_error else "ok"


# --- Idempotency cache (REQ-001..REQ-004) ---------------------------------
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
    """Store a successful result with TTL bookkeeping and eviction (REQ-003)."""
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


# --- Durable dedup store (REQ-003) -------------------------------------------
#
# Lazily opened process-wide singleton. If the config or store cannot be
# opened, durable dedup is disabled and behavior falls back to the in-process
# overlay (the pre-REQ-003 shape). Tests replace the three globals below.

_dedup_store: DedupStore | None = None
_dedup_config: DedupConfig | None = None
_dedup_disabled = False
_purge_done = False


def _dedup_context() -> tuple[DedupStore | None, DedupConfig | None]:
    """Return the (store, config) pair, or (None, None) when durable dedup is disabled."""
    global _dedup_store, _dedup_config, _dedup_disabled
    if _dedup_store is not None and _dedup_config is not None:
        return _dedup_store, _dedup_config
    if _dedup_disabled:
        return None, None
    try:
        config = load_dedup_config()
        _dedup_store = open_dedup_store(config)
        _dedup_config = config
    except Exception as exc:  # noqa: BLE001 -- fail-open by design (plan Risks: a dedup
        # store failure must not stall tool calls); overlay-only behavior is the audited
        # fallback and is asserted by tests/mcp_servers/test_mcp_dispatch.py.
        _dedup_disabled = True
        logger.warning(
            "durable dedup store unavailable: %s; overlay-only fallback", exc
        )
        return None, None
    return _dedup_store, _dedup_config


def _purge_once(store: DedupStore, config: DedupConfig) -> None:
    """Run the retention sweep at most once per process (REQ-009)."""
    global _purge_done
    if _purge_done:
        return
    _purge_done = True
    try:
        store.purge_expired(config.retention_days)
    except (sqlite3.Error, OSError) as exc:
        logger.warning("dedup retention sweep failed: %s", exc)


def _store_op(store: DedupStore, op: Callable[[], Any], label: str) -> bool:
    """Run one store mutation; a failed write degrades to the overlay, never blocks."""
    try:
        op()
        return True
    except (sqlite3.Error, OSError) as exc:
        logger.warning("dedup store write failed (%s): %s", label, exc)
        return False


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
    same contract holds across processes (REQ-003): completed results with a
    matching execution snapshot are served from the store, pending/interrupted
    rows replay for retryable tools and are refused as dedup_unreplayable for
    non-retryable ones, and the branch taken is reported in dedup_state.
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

    # duplicate-check for side-effecting tools (REQ-001: a non-empty key is
    # required; a keyless call never touches the cache or the store and always
    # executes). The durable store is the truth (REQ-003); the overlay is a
    # completed-only fast path fed from it.
    key = idempotency_key
    side_effecting = _is_side_effecting(name)
    args_hash = _normalize_args_hash(args) if (key and side_effecting) else ""
    dedup_state = ""
    store: DedupStore | None = None
    store_key = ""
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
                # Expired: drop it; the store lookup below decides (REQ-003).
                _duplicate_cache.pop(key, None)
            else:
                # REQ-002: same key reused with different content -> reject.
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
            try:
                row = store.lookup(key)
            except (sqlite3.Error, OSError) as exc:
                # Plan Risks mitigation: a store failure never blocks silently.
                # Retryable tools dispatch with an audited store_error marker;
                # non-retryable tools fail closed.
                logger.warning("dedup store lookup failed: %s", exc)
                if retry_class(name, config) == "retryable":
                    row = None
                    dedup_state = "store_error"
                else:
                    return DispatchResult(
                        output=f"Dedup store unavailable; call to tool {name!r} refused",
                        is_error=True,
                        error_type="dedup_store_error",
                        dedup_state="store_error",
                    )

            if row is not None and (
                row.args_hash != args_hash or row.tool_name != name
            ):
                # REQ-002/REQ-010: durable rows honor the same reuse rejection.
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

            snapshot_at_start = build_execution_snapshot()
            if row is not None:
                if row.status == "completed":
                    truncated = isinstance(row.result, dict) and bool(
                        row.result.get("truncated")
                    )
                    if (
                        row.result is not None
                        and not truncated
                        and snapshots_equal(row.snapshot, snapshot_at_start)
                    ):
                        served = DispatchResult(
                            output=str(row.result),
                            is_error=False,
                            dedup_state="duplicate_hit",
                        )
                        _idem_store(key, name, args_hash, served)
                        logger.info(
                            "Duplicate tool call served from durable store: %s (key=%s)",
                            name,
                            idempotency_key,
                        )
                        return served
                    # completed + snapshot mismatch (or a truncated stored payload):
                    # fresh audited attempt under the same key (REQ-005).
                    dedup_state = (
                        "result_truncated" if truncated else "snapshot_mismatch"
                    )
                    _store_op(
                        store,
                        lambda: store.record_pending(
                            key, name, args_hash, snapshot_at_start, force=True
                        ),
                        "reset-completed-for-fresh-attempt",
                    )
                elif retry_class(name, config) == "retryable":
                    # pending/failed rows replay the same key (interrupted past the
                    # timeout is the canonical case; fresh pending rows replay per
                    # the row 04 replay policy).
                    dedup_state = "replayed"
                    _store_op(
                        store,
                        lambda: store.record_pending(
                            key, name, args_hash, snapshot_at_start
                        ),
                        "refresh-pending",
                    )
                else:
                    logger.warning(
                        "Interrupted call refused auto-replay: key=%s tool=%s",
                        idempotency_key,
                        name,
                    )
                    return DispatchResult(
                        output=(
                            f"Interrupted call for idempotency key {idempotency_key!r} "
                            f"is not replayable for tool {name!r} (non-retryable)"
                        ),
                        is_error=True,
                        error_type="dedup_unreplayable",
                        dedup_state="unreplayable",
                    )
            else:
                _store_op(
                    store,
                    lambda: store.record_pending(
                        key, name, args_hash, snapshot_at_start
                    ),
                    "record-pending",
                )

    try:
        result = await handler(args)
        dispatched_result = DispatchResult(
            output=result, is_error=False, dedup_state=dedup_state
        )
        # Cache only real, successful, non-dry-run results (REQ-004).
        if key and side_effecting and not dispatched_result.is_error:
            if _is_dry_run_output(result):
                # A dry-run outcome leaves no replayable state behind.
                if store is not None:
                    _store_op(store, lambda: store.clear(key), "clear-dry-run")
            else:
                if store is not None and snapshot_at_start is not None:
                    _store_op(
                        store,
                        lambda: store.record_completed(key, snapshot_at_start, result),
                        "record-completed",
                    )
                _idem_store(key, name, args_hash, dispatched_result)
        return dispatched_result
    except ValueError as e:
        logger.warning("Tool '%s' validation error: %s", name, e)
        # REQ-004: error results are never cached, but the durable row must not
        # stay pending: pending -> failed.
        if store is not None:
            _store_op(
                store,
                lambda: store.record_failed(store_key, "validation_error"),
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
        if store is not None:
            _store_op(
                store,
                lambda: store.record_failed(store_key, error_class),
                "record-failed",
            )
        raise
    # All other exceptions (RuntimeError, IOError, HTTPException, etc.) propagate to caller.
