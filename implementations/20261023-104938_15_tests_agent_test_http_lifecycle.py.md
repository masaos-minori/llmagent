## Goal

Add a test that the manager's `shutdown_all` applies the graceful `TERMINATE_TIMEOUT_SEC`
(REQ-007) when terminating servers, and that a server ignoring SIGTERM is escalated per the
terminator (row 2). Verify existing manager shutdown tests still pass against the new
return type.

## Scope

`tests/agent/test_http_lifecycle.py` only. Reference: the manager (row 4), the coordinator
(row 3), the terminator (row 2). No change unless a gap is found.

## Assumptions

- The manager reads `TERMINATE_TIMEOUT_SEC` (`:57`) and passes it through the coordinator;
  the test can drive a mocked terminator and assert the timeout value forwarded.

## Design decisions

- **Verify, then add.** Confirm an existing test asserts the graceful timeout flows through
  `shutdown_all`. If absent, add a test that mocks the coordinator/terminator and asserts
  `TERMINATE_TIMEOUT_SEC` is the bound used, plus a SIGKILL-escalation case mirroring
  row 2.
- **Preserve existing coverage.**

## Alternatives considered

- Rewriting the manager test from scratch — rejected: verify-only, add minimally.

## Implementation

### Target file

`tests/agent/test_http_lifecycle.py`

### Procedure

1. Search `test_http_lifecycle.py` for `TERMINATE_TIMEOUT_SEC` / `shutdown_all` / timeout
   assertions.
2. If unasserted, add a test asserting the graceful timeout propagation (REQ-007).
3. Otherwise record the confirmation.

### Method

Add one test method if a gap exists; otherwise no edit.

### Details

- REQ-007 is what makes the manager's shutdown observable in tests; without it, a timeout
  regression is invisible.

## Compatibility considerations

- N/A unless a test is added; this row is verification-first.

## Security considerations

- N/A.

## Rollback considerations

- Single logical commit; `git checkout -- tests/agent/test_http_lifecycle.py` restores
  HEAD. Reversible.

## Validation plan

- `uv run pytest tests/agent/test_http_lifecycle.py`.
- `uv run mypy --no-namespace-packages scripts/agent`.
- `uv run ruff check tests/agent/test_http_lifecycle.py`.

## Completion criteria

`test_http_lifecycle.py` asserts the graceful `TERMINATE_TIMEOUT_SEC` propagation (REQ-007);
a case is added only if missing, and the suite passes.

## Out of Scope

- The vocabulary (row 1), the terminator conversion (row 2), the coordinator branch
  (row 3), the launcher verify (row 5), and the docstring corrections (rows 18-21).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify/strengthen graceful-shutdown timeout test (REQ-007) | Pending | — | — | Verify-only |
| 2 | Run validation sequence (`rules/toolchain.md`) | Pending | — | — | AC-9 |

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
- **Requirement ID**: REQ-007
- **Source issue**: `issues/20261021-093421_shutdown003-subprocess-termination-failures-report-success.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-082349_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-104938
- **Related target files**: `tests/agent/test_http_lifecycle.py`
