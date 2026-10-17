# Implementation Procedure — `tests/mcp_servers/file/test_delete_service.py`

## Goal

Add audit before/after and regression tests for file-delete (`REQ-003`, `REQ-004`).

## Scope

Modify only `tests/mcp_servers/file/test_delete_service.py`. Assert the delete audit
record carries before/after + correlation fields and that legitimate deletes still behave
correctly. Depends on `delete_service.py` (this plan's row 2).

## Assumptions

- Existing delete-service test file is present; append new tests.
- `delete_service.py` extends its audit record (row 2).

## Design decisions

- Assert audit-record fields via the shared schema (separate doc row); regression-test
  legitimate delete success/failure semantics.

## Alternatives considered

- Appending to a single shared test module across servers: rejected — each
  server owns its existing test file and fixtures; keeping tests co-located
  preserves coverage locality and reuse.

## Implementation

### Target file

`tests/mcp_servers/file/test_delete_service.py`

### Procedure

1. Test that a successful delete emits an audit record with before/after + correlation.
2. Regression test that legitimate deletes succeed with unchanged semantics.
3. If a postcondition check was added (row 2), assert it fails closed on an invalid delete.

### Method

- Append test functions; reuse existing service fixtures.

### Details

- Keep assertions to documented schema fields, not internal formatting.

## Compatibility considerations

N/A: test-only change.

## Security considerations

Do not leak sensitive content in assertions.

## Rollback considerations

Revert the commit to the test file.

## Validation plan

- Run file-delete tests; all pass.
- Command: `uv run pytest tests/mcp_servers/file/ -q`.

## Completion criteria

Audit-content and regression tests exist and pass.

## Out of scope

`delete_service.py` (separate row), the audit schema doc.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the test changes in test_delete_service.py | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: `REQ-003`, `REQ-004`
- **Source issue**: `issues/20261017-115004_mcp006_implement-missing-guard-layers-for-high-risk-tool-categories.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-133731_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-155408
- **Related target files**: `tests/mcp_servers/file/test_delete_service.py`
