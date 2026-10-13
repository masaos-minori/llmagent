#!/usr/bin/env python3
"""scripts/shared/tool_executor_helpers.py — Tool executor helper functions."""

import hashlib
from typing import Any

from shared.json_utils import dumps as _json_dumps
from shared.transport_dto import TransportErrorInfo


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


def tool_hash_key(name: str, args: dict[str, Any]) -> str:
    """Return a stable MD5 hash for a (tool name, args) pair; used for failed-call tracking (NOT for cache keys). Cache keys use plain string concatenation: f'{name}:{json_dumps(args)}'."""
    return hashlib.md5(  # nosec B324 — non-security hash for dedup key identity
        f"{name}:{_json_dumps(args)}".encode(),
        usedforsecurity=False,
    ).hexdigest()
