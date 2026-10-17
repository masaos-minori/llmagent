# Implementation Procedure — MCP-006 Phase 1: Audit Layer Foundation

## Goal

Give `file-write-mcp` and `file-delete-mcp` a shared `mcp_tool_exec` audit record emitted
from `POST /v1/call_tool`, and make the shared audit schema carry the caller-supplied
`requested_target` so requested-vs-canonical correlation becomes possible. This is Phase 1 of
the seven-phase MCP-006 plan; it closes REQ-001, REQ-002, and REQ-003 only.

## Scope

Modify only the four files below. Do not touch any other source, test, or doc:

- `scripts/mcp_servers/audit.py` (REQ-003)
- `scripts/mcp_servers/file/write_server.py` (REQ-001)
- `scripts/mcp_servers/file/delete_server.py` (REQ-002)
- `tests/mcp_servers/file/test_file_server_audit_records.py` (new; REQ-001, REQ-002)
- `tests/agent/test_audit_log_format.py` (extended; REQ-003)

No postcondition verification, byte-limit, atomic-write, or TOCTOU work is in scope — those
are Phase 2/3. No dedicated plain-text log is removed or altered (REQ-002 keeps it).

## Assumptions

- Approval is an Agent-side gate for every MCP server (`server.py:136-150` reads only
  `x-session-id`, `x-request-id`, `x-idempotency-key`; no approval identifier is sent by
  `http_transport.py:158-159`). Server-side audit therefore records the request context, not
  an approval decision.
- Both file servers already call `extract_request_context(request)` in `call_tool`, so no new
  request plumbing is required — only capture and emit.
- The shared audit schema is additive-only: `requested_target` is `NotRequired[str]`, emitted
  only when non-empty, mirroring the existing `canonical_target` pattern. Existing consumers
  rely on key-sorted JSON lines.
- `FileAuthorizationError` is a `RuntimeError` that propagates through `dispatch_tool` to the
  registered 403 handler; `FileValidationError` is a `ValueError` that `dispatch_tool` turns
  into an error `DispatchResult`. Neither may have its HTTP status mapping changed.
- The file-server loggers run with `propagate=False` (`shared/logger.py:170`), so audit
  records cannot be captured via `caplog`; tests attach a handler directly to the server
  logger.

## Design decisions

- **Emit site.** Emit one record per `call_tool` invocation from the server layer, exactly as
  `git_server.py` does, using the request context already extracted. This matches the plan's
  "audit after REQ-001/002" per-layer status and keeps the dedicated plain-text log untouched.
- **`requested_target`.** Add `requested_target: NotRequired[str]` to `AuditRecord` and emit
  it in `_build_audit_record` when non-empty, following the `canonical_target` block. Callers
  pass the requested path; canonical resolution happens later in the service layer, so at the
  server layer `target` and `requested_target` both reflect the caller's requested resource.
- **Outcome vocabulary.** `ok` for a successful dispatch, `rejected` for a validation failure
  or an authorization rejection, `error` for any other exception. Every outcome emits exactly
  one record.
- **Audit-failure isolation.** Wrap `_audit_log` in `_audit_log_safe` (mirroring
  `git_server.py`) so an audit write failure never masks the original response.

## Alternatives considered

- **Emitting the shared record from the service layer instead of the server.** Rejected — the
  service layer has no single choke point for accepted-vs-rejected calls (validation failures
  return before dispatch), so the server `call_tool` is the correct place for "exactly one
  record per call".
- **Adding a new dedicated audit log for file-write/file-delete.** Rejected — the plan's
  intent is a single shared `mcp_tool_exec` record alongside the existing dedicated logs, not
  a third log format.
- **Making `requested_target` a required field.** Rejected — additive-only schema; servers
  that do not supply it must not gain a new key.

## Implementation

### Target files

- `scripts/mcp_servers/audit.py`
- `scripts/mcp_servers/file/write_server.py`
- `scripts/mcp_servers/file/delete_server.py`

### Procedure

#### REQ-003 — `scripts/mcp_servers/audit.py`

1. Add `requested_target: NotRequired[str]` to the `AuditRecord` TypedDict immediately after
   `canonical_target`.
2. In `_build_audit_record`, after the `canonical_target` emission block, add:
   ```python
   if requested_target:
       record["requested_target"] = requested_target
   ```
   This preserves key ordering (sorted at serialization) and the additive-only contract.

#### REQ-001 — `scripts/mcp_servers/file/write_server.py`

1. Import `_audit_log` from `mcp_servers.audit` and `import logging`.
2. Add module-level `_audit_failure_count: int = 0` and `_audit_log_safe(logger, **kwargs)`
   mirroring `git_server.py`.
3. Add `_emit_call_tool_audit(req, request, outcome)` that extracts `session_id`/`request_id`
   from `extract_request_context(request)`, derives `target` from the first present of
   `path`/`source`/`destination`, and calls `_audit_log_safe` with `action=req.name`,
   `target`, `outcome`, `server_key="file-write"`, and `requested_target=target`.
4. Rewrite `call_tool` to: emit `rejected` on `validate_args` ValueError; dispatch; catch
   `FileAuthorizationError` → emit `rejected` → re-raise (preserves the 403 handler); catch
   other exceptions → emit `error` → re-raise; otherwise emit `ok` and return the response.

#### REQ-002 — `scripts/mcp_servers/file/delete_server.py`

Identical to REQ-001 with `server_key="file-delete"` and `target` derived from `path` only
(delete tools expose only `path`).

### Method

- Locate `call_tool` in each server (write_server ~line 240, delete_server ~line 210).
- Insert the audit helpers above `call_tool`; replace the body to emit on every outcome path.
- Type `_audit_log_safe`'s logger parameter as `logging.Logger | Logger` (the shared logger
  wrapper) to match `_audit_log`'s accepted union and satisfy mypy.

### Details

- `FileValidationError` (a `ValueError`) becomes an error `DispatchResult` read directly as
  `outcome="rejected"`; it does not propagate as an exception.
- `FileAuthorizationError` (a `RuntimeError`) propagates; the explicit `except` clause emits
  `rejected` then re-raises so the FastAPI 403 handler still runs.
- `assert result is not None` guards the fall-through after the try/except (mypy).

## Compatibility considerations

- The audit schema gains one optional key; key-sorted JSON-line consumers are unaffected.
- No HTTP status mapping changes: 403 stays 403, validation errors stay their existing shape.
- The dedicated plain-text audit logs for both servers are left unchanged.

## Security considerations

- `requested_target` may carry an unresolved caller path; only callers that redact
  (`_sanitize_for_audit`) pass it elsewhere, and the field is emitted only when non-empty.
- Audit failure is non-fatal (logged, never raised) so a failed audit write cannot break a
  legitimate call.

## Rollback considerations

Revert the commit touching `audit.py`, `write_server.py`, `delete_server.py`, and the two
test files.

## Validation plan

- Unit (REQ-003): `uv run pytest -q tests/agent/test_audit_log_format.py` — `requested_target`
  present when supplied, absent otherwise, keys still sorted.
- Unit TestClient (REQ-001, REQ-002): `uv run pytest -q tests/mcp_servers/file/test_file_server_audit_records.py tests/mcp_servers/file/test_call_tool_validation.py` — one parseable
  `mcp_tool_exec` record per call for accepted and rejected paths; 403 preserved.
- Static: `uv run ruff check . && uv run mypy --no-namespace-packages scripts/`.
- Full suite: `uv run pytest` stays green.

## Completion criteria

- `file-write-mcp` and `file-delete-mcp` each emit exactly one parseable `mcp_tool_exec`
  record per `call_tool` for accepted and rejected calls, containing `session_id`,
  `request_id`, `tool`, `target`, `outcome`, `server_key`.
- The shared record carries `requested_target` when supplied and omits it otherwise.
- 403/400 behavior is unchanged; the dedicated plain-text logs are intact.

## Out of scope

Postcondition verification, `edit_file` byte limit/atomic write, `delete_directory`
allowed-root widening, the Git Stage 5b re-check, all documentation rows, and the MCP-006
ledger removal. Those are separate phases.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1.1 | Emit `requested_target` in `scripts/mcp_servers/audit.py` | Completed | 20261017-214xxx | 20261017-214xxx | REQ-003 / AC-003 |
| 1.2 | Emit audit record in `scripts/mcp_servers/file/write_server.py` | Completed | 20261017-214xxx | 20261017-214xxx | REQ-001 / AC-001 |
| 1.3 | Emit audit record in `scripts/mcp_servers/file/delete_server.py` | Completed | 20261017-214xxx | 20261017-214xxx | REQ-002 / AC-002 |
| 4.1 | File-server audit-record tests in `tests/mcp_servers/file/test_file_server_audit_records.py` | Completed | 20261017-215xxx | 20261017-215xxx | REQ-001, REQ-002 / AC-001, AC-002 |
| 4.5 | `requested_target` emission test in `tests/agent/test_audit_log_format.py` | Completed | 20261017-215xxx | 20261017-215xxx | REQ-003 / AC-003 |
| 6.1 | Targeted tests + lint/type gates | Completed | 20261017-215xxx | 20261017-215xxx | 25 audit tests pass; ruff + mypy clean |

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
- **Requirement ID**: REQ-003 (`requested_target` in `audit.py`), REQ-001 (file-write audit in
  `write_server.py`), REQ-002 (file-delete audit in `delete_server.py`)
- **Source issue**: `issues/20261017-115004_mcp006_implement-missing-guard-layers-for-high-risk-tool-categories.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-160222_plan.md` (active; supersersedes the archived
  `plans/20261017-133731_plan.md`)
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-220244
- **Related target files**: `scripts/mcp_servers/audit.py`, `scripts/mcp_servers/file/write_server.py`,
  `scripts/mcp_servers/file/delete_server.py`, `tests/mcp_servers/file/test_file_server_audit_records.py`,
  `tests/agent/test_audit_log_format.py`
