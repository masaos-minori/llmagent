#!/usr/bin/env python3
"""shared/tool_executor_helpers.py — Tool executor helper functions."""

import hashlib

from shared.json_utils import dumps as _json_dumps
from shared.tool_constants import (
    CICD_WRITE_TOOLS,
    DELETE_TOOLS,
    GIT_WRITE_TOOLS,
    GITHUB_DANGEROUS_TOOLS,
    GITHUB_WRITE_TOOLS,
    MDQ_WRITE_TOOLS,
    RAG_WRITE_TOOLS,
    WRITE_TOOLS,
)
from shared.transport_dto import TransportErrorInfo

# Tools with side effects: writes, deletes, shell, or git/GitHub mutations.
# Used to auto-downgrade parallel execution to serial in execute_all_tool_calls().
#
# NOTE — two distinct, intentionally-separate serialization mechanisms exist in
# this codebase:
#   1. is_side_effect() (this module): a batch-level downgrade. When any tool
#      call in a batch has a side effect, execute_all_tool_calls() falls back
#      to serial execution for that whole batch instead of running calls
#      concurrently.
#   2. ToolSpec.requires_serial (agent/tool_scheduler.py): a per-tool flag
#      consumed by build_execution_groups() to force a single tool into its
#      own serial barrier group, independent of batch-wide side-effect state.
# They are not unified today, and whether they should be is an open follow-up
# design question — not resolved as part of this change. Do not conflate them
# when reasoning about tool-call concurrency.
_SIDE_EFFECT_TOOLS: frozenset[str] = (
    WRITE_TOOLS
    | DELETE_TOOLS
    | frozenset({"shell_run"})
    | GIT_WRITE_TOOLS
    | GITHUB_WRITE_TOOLS
    | GITHUB_DANGEROUS_TOOLS
    | CICD_WRITE_TOOLS
    | RAG_WRITE_TOOLS
    | MDQ_WRITE_TOOLS
)


def is_side_effect(tool_name: str) -> bool:
    """Return True when the tool modifies state: file write/delete, shell,

    Git write operations, or GitHub write/dangerous operations."""
    return tool_name in _SIDE_EFFECT_TOOLS


def format_transport_error(
    *,
    source: str,
    phase: str,
    kind: str,
    url: str,
    status_code: int | None,
    retryable: bool,
    partial: bool,
) -> TransportErrorInfo:
    """Return TransportErrorInfo for LLM/tool transport failures; summary is one-line user-facing; detail is JSON for audit logs."""
    detail = _json_dumps(
        {
            "source": source,
            "phase": phase,
            "kind": kind,
            "status_code": status_code,
            "url": url,
            "retryable": retryable,
            "partial": partial,
        },
    )
    summary = (
        f"[{source.upper()} {kind}] {phase} failure "
        f"(status_code={status_code}, retryable={retryable}, partial={partial})"
    )
    return TransportErrorInfo(summary=summary, detail=detail)


def tool_hash_key(name: str, args: dict[str, object]) -> str:
    """Return a stable MD5 hash for a (tool name, args) pair; used for failed-call tracking (NOT for cache keys). Cache keys use plain string concatenation: f'{name}:{json_dumps(args)}'."""
    return hashlib.md5(  # nosec B324 — non-security hash for dedup key identity
        f"{name}:{_json_dumps(args)}".encode(),
        usedforsecurity=False,
    ).hexdigest()
