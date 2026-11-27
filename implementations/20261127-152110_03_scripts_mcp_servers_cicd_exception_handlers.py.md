# Implementation Procedure — scripts/mcp_servers/cicd/exception_handlers.py

## Goal

Register handlers for the conflict and rate-limit exceptions at 409 and 429, keep upstream at 502, and
render the stable error code and the preserved metadata in the response body.

## Scope
**Release unit**: error mapping contract

Requirement implemented: REQ-004 (the handler registrations and the machine-readable response body).
Acceptance criterion: AC-3.

## Assumptions
- The exception types, the error-code vocabulary, and the exception-to-code mapping are defined by the
  `scripts/mcp_servers/cicd/cicd_models.py` row; this document reads them, it does not define them.
- The preserved `Retry-After` and reset fields are set by the backend row, so the handler only renders
  what the exception carries.
- The exact-body assertions in the companion test file are updated in the same release unit because the
  body shape is a response-contract change (Plan Assumption).

## Design decisions
- The body gains the error code and the preserved metadata; the existing `detail` key stays, so consumers
  that read `detail` are not broken (Plan Assumption, response-contract change).
- Only two registrations are added; the four existing ones at lines 38-41 keep their status codes.

## Alternatives considered
- Keeping `{"detail": str(exc)}` and putting the code inside the message: rejected — REQ-004 requires the
  code as a machine-readable field, and the message is the redacted text, not the code.

## Implementation
### Target file
`scripts/mcp_servers/cicd/exception_handlers.py`

### Procedure
- Register `CicdConflictError` (new) at 409 and `CicdRateLimitError` (new) at 429 in
  `setup_exception_handlers` (lines 36-41); keep `CicdUpstreamError` at 502 (line 41).
- Build the body from the exception's error code, taken from `EXCEPTION_ERROR_CODES` (new), plus the
  preserved metadata when the exception carries it.

### Method
- Lines 30-31 build `{"detail": str(exc)}` with no error code and no metadata (re-verified 20261127); the
  shared handler factory is extended so the existing four codes keep the same `detail` value.

### Details
- The handler does not re-derive the status from the message; the code comes from the mapping (REQ-004).

### Companion test files
- `tests/mcp_servers/cicd/test_cicd_exception_handlers.py`
  - Procedure: add the 409 and 429 handler tests, which the file has none of today, and update the exact
    body assertions at lines 54-73 in `tests/mcp_servers/cicd/test_cicd_exception_handlers.py` to the
    machine-readable shape.
  - Validation: `uv run pytest tests/mcp_servers/cicd/test_cicd_exception_handlers.py`.

## Compatibility considerations
- The response body shape is a contract change; the four existing status codes are unchanged, so only the
  body assertions move (Plan Assumption).

## Security considerations
- The rendered text is the bounded, redacted value produced by the backend row; no raw upstream payload
  appears in the body (REQ-003, AC-5).

## Rollback considerations
- N/A: revert the commit (release unit: validated with the models and backend rows).

## Validation plan
- Unit: isolated FastAPI app — `uv run pytest tests/mcp_servers/cicd/test_cicd_exception_handlers.py`.
- Full sequence per `rules/toolchain.md`.

## Completion criteria
- The handlers answer conflict at 409, rate limit at 429, and upstream at 502, and the body carries the
  stable error code with the preserved metadata (AC-3).

## Out of Scope
- The exception types and the code mapping (`scripts/mcp_servers/cicd/cicd_models.py` row); the status
  mapping and the redaction helper (`scripts/mcp_servers/cicd/cicd_service_github_actions.py` row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan (companion test file) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | documentation is covered by the Plan's docs rows |

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
- **Requirement ID**: REQ-004 (409 and 429 handler registrations, machine-readable body)
- **Source issue**: issues/20261119-141111_mcpci004_cicd-error-audit-coverage.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-070305_mcpci004_cicd-error-audit-coverage.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-152110
- **Related target files**: `scripts/mcp_servers/cicd/exception_handlers.py`, `tests/mcp_servers/cicd/test_cicd_exception_handlers.py`
