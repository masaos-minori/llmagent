# Implementation Procedure — `tests/mcp_servers/file/test_file_write_mcp_service.py`

## Goal

Add unit tests for file-write's new audit record and guards (`REQ-004`, `REQ-005`).

## Scope

Modify only `tests/mcp_servers/file/test_file_write_mcp_service.py`. Add tests asserting
the audit record is emitted with before/after + correlation fields, and that a disallowed
write is rejected. Depends on the code change in `write_service.py` (this plan's row 1).

## Assumptions

- The existing file-write service test file is present; append new test functions rather
  than rewriting fixtures.
- `write_service.py` will emit an audit record per mutating call (row 1).

## Design decisions

- Assert audit-record presence and field contents using the shared schema from
  `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md` (that doc is a separate row).
- Keep negative guard tests focused on allowlist/denylist rejection semantics.

## Alternatives considered

- Appending to a single shared test module across servers: rejected — each
  server owns its existing test file and fixtures; keeping tests co-located
  preserves coverage locality and reuse.

## Implementation

### Target file

`tests/mcp_servers/file/test_file_write_mcp_service.py`

### Procedure

1. Add a test that a successful write emits an audit record containing before/after and
   approval-correlation fields.
2. Add a negative test that a disallowed write (denylist / out-of-allowlist) does not
   produce a success audit record and returns the expected rejection.
3. Regression: a legitimate write still succeeds with unchanged semantics.

### Method

- Append test functions to the existing file; reuse existing service fixtures/builders.

### Details

- Do not assert on internal audit-line formatting beyond the documented schema fields.

## Compatibility considerations

N/A: test-only change.

## Security considerations

Tests must not depend on or leak sensitive file contents.

## Rollback considerations

Revert the commit to the test file.

## Validation plan

- Run the new and existing file-write tests; all pass.
- Command: `uv run pytest tests/mcp_servers/file/ -q`.

## Completion criteria

Audit-record and guard-rejection tests exist and pass; legitimate-call regression holds.

## Out of scope

Any change to `write_service.py` (separate row) or the audit schema doc.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the test changes in test_file_write_mcp_service.py | Pending | — | — | |
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
- **Requirement ID**: `REQ-002`, `REQ-004`, `REQ-005`
- **Source issue**: `issues/20261017-115004_mcp006_implement-missing-guard-layers-for-high-risk-tool-categories.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-133731_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-155408
- **Related target files**: `tests/mcp_servers/file/test_file_write_mcp_service.py`
