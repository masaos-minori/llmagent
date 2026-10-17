# Implementation Procedure — `tests/mcp_servers/github/test_service_security.py`

## Goal

Add audit before/after and guard-sufficiency tests for github (`REQ-002`, `REQ-004`).

## Scope

Modify only `tests/mcp_servers/github/test_service_security.py`. Assert the github audit
record carries before/after + correlation fields and that existing command guards reject
disallowed repo/path/branch. Depends on `github_service_security.py` (this plan's row 5).

## Assumptions

- Existing github security test file is present; append new tests.
- `github_service_security.py` extends its audit log and is assessed for guard coverage
  (row 5).

## Design decisions

- Audit assertion: before/after + correlation present via the shared schema (separate row).
- Guard-sufficiency negative tests: `_assert_allowed_repo`/`_path`/`_branch` reject bad
  inputs; `_clamp_per_page` clamps.

## Alternatives considered

- Appending to a single shared test module across servers: rejected — each
  server owns its existing test file and fixtures; keeping tests co-located
  preserves coverage locality and reuse.

## Implementation

### Target file

`tests/mcp_servers/github/test_service_security.py`

### Procedure

1. Test that the github audit record contains before/after + correlation fields.
2. Negative tests for each existing guard rejecting disallowed input.
3. Regression: legitimate calls still succeed.

### Method

- Append test functions; reuse existing security/fixtures helpers.

### Details

- Assertions limited to documented schema fields.

## Compatibility considerations

N/A: test-only change.

## Security considerations

Do not leak sensitive payloads (issue/pr/body) in assertions.

## Rollback considerations

Revert the commit to the test file.

## Validation plan

- Run github tests; all pass.
- Command: `uv run pytest tests/mcp_servers/github/ -q`.

## Completion criteria

Audit-content and guard-sufficiency tests exist and pass.

## Out of scope

`github_service_security.py` (separate row), the audit schema doc.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the test changes in test_service_security.py | Pending | — | — | |
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
- **Requirement ID**: `REQ-002`, `REQ-004`
- **Source issue**: `issues/20261017-115004_mcp006_implement-missing-guard-layers-for-high-risk-tool-categories.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-133731_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-155408
- **Related target files**: `tests/mcp_servers/github/test_service_security.py`
