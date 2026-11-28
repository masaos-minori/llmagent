## Goal

Add redaction tests with customer names, secrets, regexes, and absolute paths against the single emission boundary (REQ-005 exactly-one-record, REQ-006 redaction).

## Scope
**Release unit**: boundary-characterization-tests (Plan step 1 cites this row; the unit covers Phases 1, 3, 4, 5, 6)

## Assumptions
- This row keeps its own document because the redaction test design is its own decision: it defines the sample values and the absence assertions that no code row's document states.
- It fails the companion condition (2) only in the sense that it is named by one row (`scripts/mcp_servers/mdq/audit_target.py`, seq 03); condition (3) is what keeps it separate.
- Written in Phase 1 before the production change; the tests fail first and pin the current raw-value behavior.
- The existing assertions in this file (`test_error_type_used_not_embedded_in_detail`, `test_result_count_sourced_from_metadata_not_text`, `test_concurrent_requests_do_not_leak_metadata`) stay unchanged.

## Design decisions
- The assertions are absence assertions: no raw query, regex, customer name, secret, or absolute path appears in the persisted record (AC-4).
- The test runs against the emission boundary, so it also confirms the record count is one for the same call.

## Alternatives considered
- N/A: the row is a test file.

## Implementation
### Target file
`tests/mcp_servers/test_mdq_audit.py`

### Procedure
- Add redaction tests for query values, regex patterns, customer names, secrets, and absolute paths.
- Keep the existing metadata-sourcing assertions unchanged.

### Method
- Values are asserted as hashed or root-relative forms produced by `scripts/mcp_servers/mdq/audit_target.py` (seq 03) and the helper in `scripts/mcp_servers/audit.py` (seq 10).
- Step 3b correction (20261128): the expected values are computed by calling `hash_query_value()` and `path_identifier()` from the shared helper, so the test does not re-implement the redaction policy; it asserts that the persisted record matches what the helper produces.
- Step 3b correction (20261128): records are read from the server module's `logger` sink, not from a patched `_audit_log`. `AuditEmission.emit()` calls `audit.py`'s own module-level `_audit_log`, so patching the attribute in `mdq_server` would miss a record written through the boundary. Non-record info lines are skipped because `call_tool()` also logs a non-JSON line.

### Details
- The file lives under `tests/mcp_servers/`, not `tests/mcp_servers/mdq/`, so it is the shared-audit view of MDQ; the redaction assertions must not depend on MDQ-only fixtures.
- Step 3b correction (20261128): the redaction assertions use the shared helpers in `scripts/mcp_servers/audit.py` for the expected values; the fixtures that drive a call through the MDQ app are MDQ-specific by nature of this file and cannot be avoided.
- Step 3b correction (20261128): "keep the existing metadata-sourcing assertions unchanged" conflicts with AC-4 in one place. `TestAuditDetailIndependentOfOutputText.test_concurrent_requests_do_not_leak_metadata` selects each call's record by the raw query in `target`, which stops working once seq 03 hashes the target. The selection is changed to the hashed form; the assertion itself (one record per call, per-query `result_count`) is unchanged.
- Step 3b correction (20261128): the five redaction tests fail against current source as intended — `extract_audit_target()` returns the raw query, pattern, chunk id, and absolute path truncated to 80 characters. The changed selection in the concurrency test also fails today for the same reason. Recorded as the pinned disagreement; all six pass after seq 03 lands.
- Step 3b correction: a path inside an authorized root is asserted as the root-relative identifier, not as a redacted absolute path, per the plan's Path redaction design; the absence assertion is on the absolute root itself.
- Step 3b correction (20261128): the file-level `mock_audit` fixture is migrated to the same logger-sink reader the redaction tests use, because `mdq_server` no longer has a module-level `_audit_log` once seq 01 lands and the patched attribute raises `AttributeError` at fixture setup. The assertions keep their meaning: each reads the single persisted record rather than the mock's call arguments.
- Step 3b correction (20261128): `TestValidationErrorAudit` asserts the code, not the exception-class name, and the refusal case now records `error_type="tool_disabled"` with `outcome="rejected"` because seq 01's availability gate refuses `grep_docs` before the service runs. `TestAuthorizationErrorAudit` asserts `authorization_error` for the same reason. The detail assertion stays: a refusal does not repeat its kind in `detail`.

## Compatibility considerations
- `tests/mcp_servers/test_audit_redaction.py` is the shared behavior lock and is run unchanged.

## Security considerations
- This file is the AC-4 guard: raw values must not reach persistent logs.

## Rollback considerations
- N/A: revert the commit; the added tests fail again.

## Validation plan
- `uv run pytest tests/mcp_servers/test_mdq_audit.py tests/mcp_servers/test_audit_redaction.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria
- No raw query, regex, customer name, secret, or absolute path appears in a persisted record.
- Exactly one record is emitted for the tested call.

## Out of Scope
- The redaction implementation (seq 03, seq 10) and the emission boundary (seq 01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261128 | 20261128 | `TestRedactedTargets` (5 tests) added to `tests/mcp_servers/test_mdq_audit.py`; the concurrency test's record selection changed to the hashed form (see Step 3b correction) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261128-093658 | 20261128-093658 | Targeted run 20261128: 6 failed as designed (the pinned raw-value behavior), 51 passed including the unchanged shared behavior lock. ruff format/check Pass. Validation completes at the end of the release unit, after seq 03 lands end-of-unit gate 20261128 as recorded in seq 01's gates row; the six failing-first assertions pass after seq 03 landed |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Requirement ID**: REQ-005 (single audit boundary), REQ-006 (redaction)
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: `issues/done/20261119-142123_mdqmcp001_mdq-server-boundary.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-160114_mdqmcp001_mdq-server-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-213547
- **Related target files**: `tests/mcp_servers/test_mdq_audit.py`