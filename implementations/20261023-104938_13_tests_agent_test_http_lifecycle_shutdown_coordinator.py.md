## Goal

Add tests for the coordinator's outcome-based branching (row 3): `EXITED`/`ALREADY_EXITED`
succeed, `SIGNAL_NOT_DELIVERED` raises `HttpShutdownError`, and `EXIT_UNCONFIRMED` warns
and continues (REQ-005). Verify existing coordinator tests still pass against the new
return type.

## Scope

`tests/agent/test_http_lifecycle_shutdown_coordinator.py` only. Reference: the coordinator
(row 3), the terminator (row 2). No change unless a gap is found.

## Assumptions

- The coordinator test currently drives `shutdown_all` via a mocked terminator; the mock's
  `terminate_with_timeout` must now return `TerminationOutcome` members instead of `bool`.

## Design decisions

- **Update the mock terminator's return values** to `TerminationOutcome` members and add
  three cases: success on `EXITED`, raise on `SIGNAL_NOT_DELIVERED`, warn-and-continue on
  `EXIT_UNCONFIRMED`.
- **Preserve existing coverage** of ordering and multi-server shutdown.

## Alternatives considered

- Rewriting the coordinator test from scratch — rejected: migrate the mock return values
  and add the three outcome branches.

## Implementation

### Target file

`tests/agent/test_http_lifecycle_shutdown_coordinator.py`

### Procedure

1. Read `tests/agent/test_http_lifecycle_shutdown_coordinator.py`.
2. Change any mocked `terminate_with_timeout` return from `True`/`False` to the mapped
   `TerminationOutcome` members.
3. Add the three REQ-005 cases (success / raise / warn-and-continue).
4. Import `TerminationOutcome` and `HttpShutdownError`.

### Method

Edit mock return values; add three test methods.

### Details

- REQ-005 is covered by the three new cases; the raise case asserts
  `HttpShutdownError` and the warn case asserts a warning was logged.

## Compatibility considerations

- N/A: test-only. Mock returns must match row 3's branching.

## Security considerations

- N/A.

## Rollback considerations

- Single logical commit; `git checkout -- tests/agent/test_http_lifecycle_shutdown_coordinator.py`
  restores HEAD. Reversible.

## Validation plan

- `uv run pytest tests/agent/test_http_lifecycle_shutdown_coordinator.py`.
- `uv run mypy --no-namespace-packages scripts/agent`.
- `uv run ruff check tests/agent/test_http_lifecycle_shutdown_coordinator.py`.

## Completion criteria

The coordinator's three outcome branches are asserted (REQ-005), mock returns use
`TerminationOutcome`, and the suite passes.

## Out of Scope

- The vocabulary (row 1), the terminator conversion (row 2), the manager (row 4), the
  launcher verify (row 5), and the docstring corrections (rows 18-21).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add outcome-branching tests (REQ-005) | Pending | — | — | |
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
- **Requirement ID**: REQ-005
- **Source issue**: `issues/20261021-093421_shutdown003-subprocess-termination-failures-report-success.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-082349_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-104938
- **Related target files**: `tests/agent/test_http_lifecycle_shutdown_coordinator.py`
