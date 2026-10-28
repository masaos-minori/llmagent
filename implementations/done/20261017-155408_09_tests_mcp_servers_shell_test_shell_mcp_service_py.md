# Implementation Procedure — `tests/mcp_servers/shell/test_shell_mcp_service.py`

## Goal

Add audit and regression tests for the shell server (`REQ-004`).

## Scope

Modify only `tests/mcp_servers/shell/test_shell_mcp_service.py`. Assert the shell audit
record carries before/after + correlation fields; regression-test legitimate calls.
Depends on `shell_service.py` (this plan's row 3).

## Assumptions

- Existing shell-service test file is present; append new tests.
- `shell_service.py` extends its audit record (row 3).

## Design decisions

- Assert audit fields via the shared schema (separate doc row); regression-test
  legitimate-call success/failure semantics.

## Alternatives considered

- Appending to a single shared test module across servers: rejected — each
  server owns its existing test file and fixtures; keeping tests co-located
  preserves coverage locality and reuse.

## Implementation

### Target file

`tests/mcp_servers/shell/test_shell_mcp_service.py`

### Procedure

1. Test that a successful shell operation emits an audit record with before/after +
   correlation fields.
2. Regression test that legitimate shell calls succeed with unchanged semantics.

### Method

- Append test functions; reuse existing service fixtures.

### Details

- Assertions limited to documented schema fields.

## Compatibility considerations

N/A: test-only change.

## Security considerations

Do not capture or assert on sensitive command output.

## Rollback considerations

Revert the commit to the test file.

## Validation plan

- Run shell tests; all pass.
- Command: `uv run pytest tests/mcp_servers/shell/ -q`.

## Completion criteria

Audit-content and regression tests exist and pass.

## Out of scope

`shell_service.py` (separate row), the audit schema doc.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the test changes in test_shell_mcp_service.py | Completed | 20261017-183816 | 20261017-183816 | added TestRunCommandAuditLog(successful run_command emits cmd/argv/cwd/uid pre-context + exit/elapsed/truncated post-result + op=run_command correlation; no stdout/stderr leak) + TestWriteAuditLog.test_write_audit_log_honors_custom_op(op param(row3) propagated) + TestRunCommandRegression(legitimate success + audit written); ruff format/check+mypy clean; 3 new tests pass; full shell suite 109 pass |
| 2 | Add or update tests per Validation plan | Completed | 20261017-183816 | 20261017-183816 | added TestRunCommandAuditLog(successful run_command emits cmd/argv/cwd/uid pre-context + exit/elapsed/truncated post-result + op=run_command correlation; no stdout/stderr leak) + TestWriteAuditLog.test_write_audit_log_honors_custom_op(op param(row3) propagated) + TestRunCommandRegression(legitimate success + audit written); ruff format/check+mypy clean; 3 new tests pass; full shell suite 109 pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261017-183816 | 20261017-183816 | added TestRunCommandAuditLog(successful run_command emits cmd/argv/cwd/uid pre-context + exit/elapsed/truncated post-result + op=run_command correlation; no stdout/stderr leak) + TestWriteAuditLog.test_write_audit_log_honors_custom_op(op param(row3) propagated) + TestRunCommandRegression(legitimate success + audit written); ruff format/check+mypy clean; 3 new tests pass; full shell suite 109 pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261017-183816 | 20261017-183816 | N/A added TestRunCommandAuditLog(successful run_command emits cmd/argv/cwd/uid pre-context + exit/elapsed/truncated post-result + op=run_command correlation; no stdout/stderr leak) + TestWriteAuditLog.test_write_audit_log_honors_custom_op(op param(row3) propagated) + TestRunCommandRegression(legitimate success + audit written); ruff format/check+mypy clean; 3 new tests pass; full shell suite 109 pass |

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
- **Requirement ID**: `REQ-004`
- **Source issue**: `issues/20261017-115004_mcp006_implement-missing-guard-layers-for-high-risk-tool-categories.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-133731_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-155408
- **Related target files**: `tests/mcp_servers/shell/test_shell_mcp_service.py`