"""scripts/mcp_servers/audit.py

Structured audit logging helper extracted from mcp/server.py.

Emits one JSON-lines record per MCP tool execution event.

Error Type Vocabulary
---------------------
The ``error_type`` field carries a short identifier for the failure mode.
Three vocabularies currently exist:

1. ``mdq``: Python exception-class names (e.g., ``"MdqValidationError"``,
   ``"MdqAuthorizationError"``). Source: ``type(exc).__name__``.
2. ``web_search``: lowercase-snake identifiers (e.g., ``"validation_error"``,
   ``"authorization_error"``, ``"timeout"``). Preferred for new code.
3. ``cicd``: lowercase-snake identifiers in the style above, defined by
   ``CICD_ERROR_CODES`` in ``mcp_servers/cicd/cicd_models.py``:
   ``authorization_error``, ``not_found``, ``validation_error``,
   ``upstream_error``, ``conflict``, ``rate_limit``, ``unexpected_error``
   (mcpci004). ``unexpected_error`` names the audit category for a failure with no
   CI/CD exception class, so it has no entry in ``EXCEPTION_ERROR_CODES``.

Recommendation: Adopt the ``web_search`` style for new MCP servers.
Rationale: more stable across Python versions, more readable in log queries,
and consistent with RFC 7807 Problem Details conventions.

Detail Field Semantics
----------------------
The ``detail`` field (optional, ``NotRequired[str]``) contains machine-parseable
key=value pairs when present. Never emit an empty string — omit the field entirely
when there is nothing to report. Examples::

    detail="duration_ms=42 result_count=5"
    detail="latency_ms=120 query_len=12 host='example.com'"

Audit records must not contain raw query text or raw URLs: use ``hash_query_value``
for query-like values and ``redact_url`` for URLs, and emit through ``AuditEmission``
so every authenticated call produces exactly one record.
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import time
from collections.abc import Sequence
from typing import NotRequired, TypedDict
from urllib.parse import urlsplit

import orjson
from shared.logger import Logger as _SharedLogger


class AuditRecord(TypedDict):
    """Structured payload for one MCP tool execution audit record."""

    event: str
    source: str
    ts: float
    session_id: str
    request_id: str
    tool: str
    target: str
    outcome: str
    server_key: str
    error_type: str
    detail: NotRequired[str]
    pre_condition: NotRequired[dict[str, object]]
    post_condition: NotRequired[dict[str, object]]
    requested_target: NotRequired[str]
    canonical_target: NotRequired[str]


def _build_audit_record(
    session_id: str,
    request_id: str,
    action: str,
    target: str,
    outcome: str,
    detail: str = "",
    server_key: str = "",
    error_type: str = "",
    pre_condition: dict[str, object] | None = None,
    post_condition: dict[str, object] | None = None,
    requested_target: str = "",
    canonical_target: str = "",
) -> AuditRecord:
    """Build the structured record for one MCP tool execution audit event.

    Args:
        session_id: Session identifier from the request context.
        request_id: Per-call request ID from the request context.
        action: Tool name or action being audited.
        target: Canonical repository identity or resource identifier.
        outcome: One of ``"ok"``, ``"error"``, ``"rejected"``.
        detail: Optional key=value pairs (omit when empty).
        server_key: Identifying key for the MCP server emitting this record.
        error_type: Failure-mode identifier (see module docstring for vocabularies).
        pre_condition: Pre-condition state snapshot (optional).
        post_condition: Post-condition state snapshot (optional).
        requested_target: Redacted repo path before resolution (optional).
        canonical_target: Resolved repo path (optional).
    """
    record: AuditRecord = {
        "event": "mcp_tool_exec",
        "source": "mcp_server",
        "ts": time.time(),
        "session_id": session_id or "-",
        "request_id": request_id or "-",
        "tool": action,
        "target": target,
        "outcome": outcome,
        "server_key": server_key,
        "error_type": error_type,
    }
    if detail:
        record["detail"] = detail
    if pre_condition is not None:
        record["pre_condition"] = {
            k: v
            for k, v in pre_condition.items()
            if isinstance(v, (str, int, float, bool, type(None)))
        }
    if post_condition is not None:
        record["post_condition"] = {
            k: v
            for k, v in post_condition.items()
            if isinstance(v, (str, int, float, bool, type(None)))
        }
    if requested_target:
        record["requested_target"] = requested_target
    if canonical_target:
        record["canonical_target"] = canonical_target
    return record


def _audit_log(
    server_logger: logging.Logger | _SharedLogger,
    session_id: str,
    request_id: str,
    action: str,
    target: str,
    outcome: str,
    detail: str = "",
    server_key: str = "",
    error_type: str = "",
    pre_condition: dict[str, object] | None = None,
    post_condition: dict[str, object] | None = None,
    requested_target: str = "",
    canonical_target: str = "",
) -> None:
    """Emit one JSON-lines audit record for an MCP tool execution.

    Args:
        server_logger: Logger instance for the calling MCP server.
        session_id: Session identifier from the request context.
        request_id: Per-call request ID from the request context.
        action: Tool name or action being audited.
        target: Canonical repository identity or resource identifier.
        outcome: One of ``"ok"``, ``"error"``, ``"rejected"``.
        detail: Optional key=value pairs (omit when empty).
        server_key: Identifying key for the MCP server emitting this record.
        error_type: Failure-mode identifier (see module docstring for vocabularies).
        pre_condition: Pre-condition state snapshot (optional).
        post_condition: Post-condition state snapshot (optional).
        requested_target: Redacted repo path before resolution (optional).
        canonical_target: Resolved repo path (optional).
    """
    record = _build_audit_record(
        session_id=session_id,
        request_id=request_id,
        action=action,
        target=target,
        outcome=outcome,
        detail=detail,
        server_key=server_key,
        error_type=error_type,
        pre_condition=pre_condition,
        post_condition=post_condition,
        requested_target=requested_target,
        canonical_target=canonical_target,
    )
    server_logger.info(orjson.dumps(record, option=orjson.OPT_SORT_KEYS).decode())


_logger = logging.getLogger(__name__)

# URL path redaction: at most this many segments are kept; a segment is kept only
# when it is short, plain, and not token-shaped, and every other segment is "*".
_MAX_PATH_SEGMENTS = 8
_PLAIN_SEGMENT_RE = re.compile(r"^[A-Za-z0-9._~-]{1,24}$")
_HEX_TOKEN_RE = re.compile(r"^[0-9a-fA-F]{16,}$")
_ALNUM_TOKEN_RE = re.compile(r"^(?=.*\d)[A-Za-z0-9]{16,}$")
_INVALID_URL = "invalid-url"


def hash_query_value(value: str) -> str:
    """Return a short stable hash of a query-like value for audit correlation.

    The value is trimmed and lowercased first, so the same query hashes equally
    whatever its casing or surrounding whitespace. The output is the first 16 hex
    characters of its SHA-256 and does not contain the value.
    """
    return hashlib.sha256(value.strip().lower().encode()).hexdigest()[:16]


def _redact_segment(segment: str) -> str:
    """Keep a short plain path segment and replace anything else with `*`."""
    if (
        _PLAIN_SEGMENT_RE.match(segment)
        and not _HEX_TOKEN_RE.match(segment)
        and not _ALNUM_TOKEN_RE.match(segment)
    ):
        return segment
    return "*"


def redact_url(url: str) -> str:
    """Return `scheme://host` plus a redacted path, or `invalid-url`.

    The port, user information, query, and fragment are dropped. At most eight path
    segments are kept (a longer path ends in `...`), and a segment is kept only when
    it is short, made of plain characters, and not token-shaped; every other segment
    becomes `*`. A URL without a scheme or host is returned as `invalid-url`.
    """
    try:
        parts = urlsplit(url)
        host = parts.hostname
    except ValueError:
        return _INVALID_URL
    if not parts.scheme or not host:
        return _INVALID_URL
    shown_host = f"[{host}]" if ":" in host else host
    segments = [s for s in parts.path.split("/") if s]
    kept = [_redact_segment(s) for s in segments[:_MAX_PATH_SEGMENTS]]
    if len(segments) > _MAX_PATH_SEGMENTS:
        kept.append("...")
    path = "".join(f"/{s}" for s in kept)
    return f"{parts.scheme}://{shown_host}{path}"


def path_identifier(path: str, roots: Sequence[str]) -> str:
    """Return a root-relative identifier for a path inside an authorized root, else a hash.

    `roots` are the currently authorized roots supplied by the caller, so the helper reads
    no configuration and stays policy-only. The path and each root are normalized
    textually — no filesystem access — so a path that reaches an authorized root only
    through a symlink falls back to the hash branch instead of exposing a path.

    Inside a root the result is the path relative to that root; otherwise it is the same
    16 hexadecimal characters `hash_query_value()` produces, so persisted values stay
    comparable across servers without exposing an absolute path.
    """
    normalized = _normalize_path(path)
    for root in roots:
        normalized_root = _normalize_path(root)
        if normalized == normalized_root:
            return "."
        if normalized_root and normalized.startswith(normalized_root + "/"):
            return normalized.removeprefix(normalized_root + "/")
    return hash_query_value(normalized)


def _normalize_path(value: str) -> str:
    """Normalize a path textually: expand `~`, collapse `.` and `..`, drop the trailing separator."""
    normalized = os.path.normpath(os.path.expanduser(value))
    return normalized.rstrip("/") or "/"


class AuditEmission:
    """Per-call guard that lets one authenticated call write exactly one record.

    Create one at the start of a handler and emit from its single `finally` block.
    `emit()` writes through `_audit_log` the first time and returns True; a later
    call writes nothing, logs a warning, and returns False, so a `finally` block can
    never raise over an in-flight exception.
    """

    def __init__(
        self,
        server_logger: logging.Logger | _SharedLogger,
        *,
        session_id: str,
        request_id: str,
        action: str,
        server_key: str,
    ) -> None:
        self._logger = server_logger
        self._session_id = session_id
        self._request_id = request_id
        self._action = action
        self._server_key = server_key
        self._emitted = False

    @property
    def emitted(self) -> bool:
        """Whether this call's record has been written."""
        return self._emitted

    def emit(
        self,
        *,
        target: str,
        outcome: str,
        error_type: str = "",
        detail: str = "",
    ) -> bool:
        """Write the record once; return whether this call wrote it."""
        if self._emitted:
            _logger.warning(
                "second audit emission ignored: tool=%s request_id=%s",
                self._action,
                self._request_id,
            )
            return False
        self._emitted = True
        _audit_log(
            self._logger,
            session_id=self._session_id,
            request_id=self._request_id,
            action=self._action,
            target=target,
            outcome=outcome,
            detail=detail,
            server_key=self._server_key,
            error_type=error_type,
        )
        return True
