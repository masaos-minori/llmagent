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

### Details
- The file lives under `tests/mcp_servers/`, not `tests/mcp_servers/mdq/`, so it is the shared-audit view of MDQ; the redaction assertions must not depend on MDQ-only fixtures.

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
