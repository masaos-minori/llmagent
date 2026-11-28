# Implementation Procedure — scripts/mcp_servers/cicd/cicd_models.py

## Goal

Add the conflict and rate-limit exception types, the CI/CD error-code vocabulary as a frozenset, the
exception-to-code mapping, and the maximum error-text length constant.

## Scope
**Release unit**: error mapping contract

Requirements implemented: REQ-001 (the new exception types), REQ-003 (the maximum error-text length
constant), REQ-004 (the exception-to-code mapping the handler renders), REQ-006 (the stable error-code
vocabulary). Acceptance criteria: AC-1, AC-3, AC-5.

## Assumptions
- The vocabulary is a CI/CD-scoped frozenset in this module, following the lowercase-snake style the
  shared helper recommends for new servers; `scripts/shared/mcp_call_state_contract.py`'s
  `CONTROL_ERROR_CODES` is not extended (Plan Assumption, consistent with the mcpci002 decision).
- The maximum length value is decided at implementation (UNK-04); the test asserts the bound rather than
  the specific value.
- The strict request models and the log response model added by the mcpci001 and mcpci003 passes already
  exist in this file; this document adds the exception types, the vocabulary, and the constant only
  (Plan Assumption, compatible overlap).

## Design decisions
- Constants and names: `CicdConflictError` (new), `CicdRateLimitError` (new), `CICD_ERROR_CODES` (new),
  `EXCEPTION_ERROR_CODES` (new), `MAX_ERROR_TEXT_LENGTH` (new). Values are decided at implementation
  (UNK-04).
- Error-code home: the CI/CD-scoped frozenset in this module (Plan Design decision), not the shared dedup
  control vocabulary.

## Alternatives considered
- Extending `CONTROL_ERROR_CODES`: rejected — it is the dedup control vocabulary, not an audit error-type
  vocabulary (Plan Design decision).

## Implementation
### Target file
`scripts/mcp_servers/cicd/cicd_models.py`

### Procedure
- Add `CicdConflictError` (new) and `CicdRateLimitError` (new) alongside the four existing exception
  classes at lines 63, 67, 71, and 75, keeping the existing hierarchy bases.
- Add `CICD_ERROR_CODES` (new) as a frozenset of stable lowercase-snake codes, and
  `EXCEPTION_ERROR_CODES` (new) mapping each exception type to its code.
- Add `MAX_ERROR_TEXT_LENGTH` (new), the bound the backend helper applies to upstream text.

### Method
- Lines 63-75 hold the four exception classes only (re-verified 20261127); the request models after them
  are unchanged by this document.
- Step 3b correction: the citation is stale against the current source. At revision da8097e74 the four
  exception classes are at lines 41, 45, 49, and 53, not 63-75; the two new classes were added after them
  at lines 57 and 61. The request models are unchanged, so the pin at
  `tests/mcp_servers/cicd/test_cicd_models.py` lines 193-197 stays valid.
- UNK-04, decided at implementation: `MAX_ERROR_TEXT_LENGTH = 500` as a module constant in this file. The
  companion test asserts the bound rather than the value.
- Step 3b correction: the vocabulary also carries `unexpected_error`, the audit category for a failure with
  no CI/CD exception class (`call_tool()`'s catch-all in `scripts/mcp_servers/cicd/cicd_server.py`). It has
  no entry in `EXCEPTION_ERROR_CODES`, so the companion test asserts the mapped values are a proper subset
  of the frozenset rather than equal to it. The codes for the dispatch categories and the disabled gate
  (`unknown_tool`, `idempotency_key_reused`, `validation_error`, `dedup_store_error`, `tool_disabled`) are
  not vocabulary members: they come from `scripts/mcp_servers/dedup_gate.py` and the disabled gate, so the
  frozenset holds only the exception codes plus `unexpected_error`.

### Details
- The exception types carry the preserved `Retry-After` and reset fields produced by the backend row; this
  document defines the types, not the parsing (REQ-003).

### Companion test files
- `tests/mcp_servers/cicd/test_cicd_models.py`
  - Procedure: extend `test_exception_hierarchy` in `tests/mcp_servers/cicd/test_cicd_models.py` lines 193-197, which pins four classes today, and add the error-code vocabulary tests.
  - Validation: `uv run pytest tests/mcp_servers/cicd/test_cicd_models.py`.

## Compatibility considerations
- The existing four exception types keep their hierarchy, so the pins in `tests/mcp_servers/cicd/test_cicd_models.py` lines 193-197 stay valid once the two new classes are added.

## Security considerations
- N/A: type and constant definitions only; no token or raw upstream text is stored.

## Rollback considerations
- N/A: revert the commit (release unit: validated with the backend and handler rows).

## Validation plan
- Unit: exception hierarchy and error-code vocabulary —
  `uv run pytest tests/mcp_servers/cicd/test_cicd_models.py` (the tests are written by the companion row).
- Full sequence per `rules/toolchain.md`, including the `agent-mcp-config-models` import-linter contract.

## Completion criteria
- The new classes and the frozenset are pinned (AC-1, AC-5); the mapping names the code the handler
  renders at 409 and 429 (AC-3).

## Out of Scope
- The status mapping and the redaction helper
  (`scripts/mcp_servers/cicd/cicd_service_github_actions.py` row); the handler registrations
  (`scripts/mcp_servers/cicd/exception_handlers.py` row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261128 | 20261128 | classes added at lines 57 and 61; `CICD_ERROR_CODES` includes `unexpected_error` (no mapping entry); `MAX_ERROR_TEXT_LENGTH = 500` (UNK-04) |
| 2 | Add or update tests per Validation plan (companion test file) | Completed | 20261128 | 20261128 | `test_exception_hierarchy` extended with the two new classes; vocabulary test asserts the seven-code frozenset; mapping test asserts a proper subset because `unexpected_error` has no exception; structured-field test for `retry_after` / `rate_limit_reset` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261128 | 20261128 | `uv run pytest tests/mcp_servers/cicd/test_cicd_models.py` passes; gates all Pass; `agent-mcp-config-models` contract kept |
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
- **Requirement ID**: REQ-001, REQ-003, REQ-004, REQ-006 (exception types, error-code vocabulary, maximum error-text length)
- **Source issue**: issues/20261119-141111_mcpci004_cicd-error-audit-coverage.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-070305_mcpci004_cicd-error-audit-coverage.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-152110
- **Related target files**: `scripts/mcp_servers/cicd/cicd_models.py`, `tests/mcp_servers/cicd/test_cicd_models.py`
