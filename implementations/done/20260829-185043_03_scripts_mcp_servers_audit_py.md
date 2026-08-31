# Implementation Procedure: NC-020 Row 3 — Add `error_type` vocabulary documentation to `audit.py`

## Goal

Document the two existing `error_type` vocabularies in use across MCP servers (`mdq`'s Python exception-class names vs `web_search`'s lowercase-snake strings), establish Git MCP's deliberate vocabulary choice, and provide usage guidance for the `detail` field on non-error paths. This is a documentation-only change — no code modification required.

## Scope

Only `scripts/mcp_servers/audit.py`: add docstring-level documentation describing the `error_type` vocabulary conventions and `detail` field semantics. No code changes.

## Assumptions

- Git MCP will adopt one of the two existing vocabulary styles rather than introducing a third — this decision must be explicit and documented.
- The `detail` field is optional (`NotRequired[str]`) and should contain machine-parseable key=value pairs when present, not free-form prose.
- The vocabulary choice affects downstream log querying and alerting; consistency within a category (e.g., all security-related errors) is preferred over strict uniformity across categories.

## Design decisions

- **Vocabulary recommendation**: Recommend `web_search`'s lowercase-snake style (`"validation_error"`, `"authorization_error"`, etc.) because:
  - It is more stable across Python version changes (exception-class names can change between versions).
  - It is more readable in log queries without requiring knowledge of Python's type system.
  - It aligns with common API error classification patterns (RFC 7807 Problem Details).
- **Documentation approach**: Add a module-level docstring section documenting both vocabularies and the recommendation, plus inline comments in `_audit_log()` for the `detail` field semantics.
- **No enforcement mechanism**: This is advisory documentation only. Enforcement would require lint rules or CI checks, which are out of scope for this issue.

## Alternatives considered

1. **Enforce vocabulary via lint rule**: Would prevent future drift but adds CI complexity and requires consensus across all MCP servers — too broad for this issue's scope.
2. **Introduce `error_type` enum**: Would provide compile-time safety but requires changing every call site across all MCP servers — too invasive for a documentation-only row.
3. **Leave undocumented**: Current state — inconsistent usage without any reference guide. This is the status quo that the Acceptance Criteria explicitly rejects.

## Implementation

### Target file

`scripts/mcp_servers/audit.py`

### Procedure

1. Add a module-level docstring section after the existing header that documents:
   - `error_type` vocabulary conventions (two existing styles + recommended choice)
   - `detail` field semantics (key=value format, optional, never empty string)
2. Add inline docstring annotations to `_audit_log()` parameters for `error_type` and `detail`.

### Method

Docstring additions only. No code logic changes.

### Details

```python
"""scripts/mcp_servers/audit.py

Structured audit logging helper extracted from mcp/server.py.

Emits one JSON-lines record per MCP tool execution event.

Error Type Vocabulary
---------------------
The ``error_type`` field carries a short identifier for the failure mode.
Two vocabularies currently exist:

1. ``mdq``: Python exception-class names (e.g., ``"MdqValidationError"``,
   ``"MdqAuthorizationError"``). Source: ``type(exc).__name__``.
2. ``web_search``: lowercase-snake identifiers (e.g., ``"validation_error"``,
   ``"authorization_error"``, ``"timeout"``). Preferred for new code.

Recommendation: Adopt the ``web_search`` style for new MCP servers.
Rationale: more stable across Python versions, more readable in log queries,
and consistent with RFC 7807 Problem Details conventions.

Detail Field Semantics
----------------------
The ``detail`` field (optional, ``NotRequired[str]``) contains machine-parseable
key=value pairs when present. Never emit an empty string — omit the field entirely
when there is nothing to report. Examples::

    detail="duration_ms=42 result_count=5"
    detail="latency_ms=120 query_preview='search term'"
"""

from __future__ import annotations

import logging
import time
from typing import NotRequired, TypedDict

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


def _build_audit_record(
    session_id: str,
    request_id: str,
    action: str,
    target: str,
    outcome: str,
    detail: str = "",
    server_key: str = "",
    error_type: str = "",
) -> AuditRecord:
    """Build the structured record for one MCP tool execution audit event."""
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
    )
    server_logger.info(orjson.dumps(record, option=orjson.OPT_SORT_KEYS).decode())
```

## Compatibility considerations

- **No breaking changes**: Adding docstrings does not modify runtime behavior.
- **Cross-server inconsistency persists**: This document recommends the `web_search` style but cannot enforce it. Other MCP servers may continue using their own vocabularies independently.
- **Downstream consumers**: Log aggregation systems that parse `error_type` values will see mixed formats until all servers converge — this is acceptable during the transition period.

## Security considerations

- **No code changes**: This is documentation-only; no new attack surface is introduced.
- **Vocabulary stability**: The `web_search` style is more stable across Python versions, reducing the risk of misclassification due to exception-class name changes.

## Rollback considerations

- Revert the added docstrings to the original text.
- Remove the inline parameter annotations from `_audit_log()`.
- No data loss or behavioral regression possible since no code was changed.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|--------|------------------|----------------|------------------|
| Docstring content | Manual review against design rationale | N/A (human inspection) | Documentation covers both vocabularies, states recommendation, explains rationale |
| Inline annotations | Verify `_audit_log()` signature unchanged | `uv run mypy scripts/mcp_servers/audit.py` | No type errors introduced |
| Module docstring | Verify module loads without side effects | `python -c "import mcp_servers.audit"` | Import succeeds, no exceptions |

## Completion criteria

- [ ] Module-level docstring documents both `error_type` vocabularies
- [ ] Recommendation for `web_search` style stated with rationale
- [ ] `detail` field semantics documented (key=value format, optional)
- [ ] `_audit_log()` parameter annotations updated
- [ ] No type-checking regressions introduced

## Out of scope

- Enforcing the recommended vocabulary via lint rules or CI
- Changing any MCP server's actual `error_type` values
- Modifying the `AuditRecord` TypedDict structure
- Adding new fields to the audit schema
- Cross-server coordination meetings or consensus processes

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add module-level docstring documenting vocabularies and recommendations | Completed | 2026-08-31 | 2026-08-31 | |
| 2 | Update `_build_audit_record()` parameter annotations | Completed | 2026-08-31 | 2026-08-31 | |
| 3 | Update `_audit_log()` parameter annotations | Completed | 2026-08-31 | 2026-08-31 | |
| 4 | Run type checker to verify no regressions | Completed | 2026-08-31 | 2026-08-31 | mypy clean; ruff clean; import OK |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-006, REQ-008
- **Source issue**: issues/20260828-160910_nc020_git_mcp_audit_target_resolution.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260829-115719_nc020_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260829-185043
- **Related target files**: scripts/mcp_servers/audit.py
