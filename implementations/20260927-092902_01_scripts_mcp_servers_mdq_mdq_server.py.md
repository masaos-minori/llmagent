## Goal

Fix `_mdq_error_handler`'s tuple-unpacking order in `scripts/mcp_servers/mdq/mdq_server.py`: `extract_request_context(request)` returns `(session_id, request_id, idempotency_key)`, but the handler unpacks it as `request_id, session_id, _`, swapping the two values in every MDQ error-path audit log record (REQ-001).

## Scope

In scope: the 1 unpacking line inside `_mdq_error_handler`. Out of scope: `scripts/mcp_servers/server.py::extract_request_context` (confirmed already correct — its docstring, return statement, and implementation all consistently order `(session_id, request_id, idempotency_key)`).

## Assumptions

- No other call site in `mdq_server.py` (or elsewhere) unpacks `extract_request_context`'s return value in the same swapped order — confirmed via Read that `_mdq_error_handler` is the sole call site in this file, and `extract_request_context` is defined once in `scripts/mcp_servers/server.py` with no other known caller sharing this same bug (not otherwise investigated beyond this file per the Plan's scope).

## Design decisions

- Swap only the two variable names in the unpacking statement — `_audit_log`'s downstream call already uses the correct keyword names (`session_id=session_id, request_id=request_id`), so no other line needs to change.

## Alternatives considered

- N/A: a single, unambiguous swapped-unpacking bug with one correct fix; no alternative approach considered.

## Implementation

### Target file

`scripts/mcp_servers/mdq/mdq_server.py`

### Procedure

1. Re-confirm the exact current line via `rg -n "extract_request_context" scripts/mcp_servers/mdq/mdq_server.py` (adversarial re-verification — line number may have shifted since the Plan was written).
2. Change `request_id, session_id, _ = extract_request_context(request)` to `session_id, request_id, _ = extract_request_context(request)`.

### Method

Direct variable-name swap on a single line — no other change.

### Details

- Before: `request_id, session_id, _ = extract_request_context(request)` (line ~81, inside `_mdq_error_handler`).
- After: `session_id, request_id, _ = extract_request_context(request)`.
- Confirmed downstream: `_audit_log(logger, session_id=session_id, request_id=request_id, action="call_tool", ...)` already uses the correct keyword names — no change needed there.

## Compatibility considerations

- This corrects every MDQ error-path audit log record's `session_id`/`request_id` fields going forward — any downstream log consumer/dashboard relying on the (currently swapped, incorrect) field values would see a behavior change, but this is the intended correctness fix, not a compatibility break to preserve.

## Security considerations

- This is an audit-logging correctness fix (session-based tracing and per-request correlation for the MDQ service's error paths) — restores intended security/operational-observability behavior; no new security exposure introduced.

## Rollback considerations

- `git revert` the commit, or manually swap the variable names back.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/mcp_servers/mdq/mdq_server.py` | Unit/Integration | `uv run pytest tests/mcp_servers/mdq/test_mdq_exception_handlers.py -q` | All tests pass, with `session_id` correctly reflecting the `x-session-id` header and `request_id` correctly reflecting the middleware-populated UUID |

## Completion criteria

- `uv run pytest tests/mcp_servers/mdq/test_mdq_exception_handlers.py -q` passes with no failures.
- No regression in `TestUnknownToolAuditDetail` or other classes in the same test file.

## Out of scope

- `scripts/mcp_servers/server.py::extract_request_context` (confirmed already correct).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: existing `test_session_id_from_header_and_request_id_from_middleware_state` test already covers this fix |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: internal audit-logging correctness fix, no documented contract changes |

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
- **Requirement ID**: REQ-001: fix `_mdq_error_handler`'s unpacking-order swap
- **Source issue**: issues/20260927-075250_mcp002_mdq-service-ignores-session_id-from-request-header.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-084346_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-092902
- **Related target files**: scripts/mcp_servers/mdq/mdq_server.py
