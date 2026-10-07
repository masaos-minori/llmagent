"""scripts/mcp_servers/dispatch.py

Tool dispatch helpers extracted from mcp/server.py.
Kept separate so MCP servers can import dispatch_tool without pulling in the
full MCPServer base class.
"""

from __future__ import annotations

import json
import logging
import time
from collections import OrderedDict
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from hashlib import sha256
from typing import Any

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
    """Typed result from MCPServer.dispatch() and dispatch_tool()."""

    output: str
    is_error: bool

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


def _to_call_tool_response(r: DispatchResult) -> CallToolResponse:
    """Convert a DispatchResult into a CallToolResponse."""
    return CallToolResponse(result=r.output, is_error=r.is_error)


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
    dry-run results are never cached.
    """
    if not isinstance(name, str) or not name.strip():
        logger.warning("dispatch_tool called with empty tool name")
        return DispatchResult(
            output="Tool name must be a non-empty string", is_error=True
        )

    handler = table.get(name)
    if handler is None:
        logger.warning("Unknown tool requested: %s", name)
        return DispatchResult(output=f"Unknown tool: {name}", is_error=True)

    # duplicate-check for side-effecting tools (REQ-001: a non-empty key is
    # required; a keyless call never touches the cache and always executes)
    key = idempotency_key
    side_effecting = _is_side_effecting(name)
    args_hash = _normalize_args_hash(args) if (key and side_effecting) else ""
    if key and side_effecting:
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
                # Expired: drop it and fall through to a fresh execution.
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
                )

    try:
        result = await handler(args)
        dispatched_result = DispatchResult(output=result, is_error=False)
        # Cache only real, successful, non-dry-run results (REQ-004).
        if key and side_effecting and not dispatched_result.is_error:
            if not _is_dry_run_output(result):
                _idem_store(key, name, args_hash, dispatched_result)
        return dispatched_result
    except ValueError as e:
        logger.warning("Tool '%s' validation error: %s", name, e)
        # REQ-004: error results are never cached.
        return DispatchResult(output=f"Validation error: {e}", is_error=True)
    # All other exceptions (RuntimeError, IOError, HTTPException, etc.) propagate to caller.
