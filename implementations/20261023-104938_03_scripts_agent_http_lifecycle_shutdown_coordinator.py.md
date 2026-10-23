## Goal

Branch the coordinator's `shutdown_all` on the `TerminationOutcome` returned by each
server's `terminate_with_timeout` (row 2) so that "not stopped" is handled per
REQ-005: exit outcomes succeed, `SIGNAL_NOT_DELIVERED` errors out, and `EXIT_UNCONFIRMED`
warns and continues. This is what makes the four-way vocabulary from rows 1-2 actually
observable end-to-end (REQ-007).

## Scope

Only the `shutdown_all` loop in `scripts/agent/http_lifecycle_shutdown_coordinator.py`
around `:79-107`. No signature change. Consumer: the four other `shutdown_all`
definitions (rows 4-9), which must accept the same type. Reference read: the terminator
(row 2). Dependent test: `tests/agent/test_http_lifecycle_shutdown_coordinator.py`
(row 13).

## Assumptions

- `terminate_with_timeout` now returns `TerminationOutcome` (row 2); the coordinator is
  the first consumer and must switch from a bool check to an outcome comparison.
- The four outcome members are exactly `EXITED`, `ALREADY_EXITED`, `SIGNAL_NOT_DELIVERED`,
  `EXIT_UNCONFIRMED` (row 1).

## Design decisions

- **Branch on the outcome, not truthiness.** Replace the current
  `if result: logger.info(...): continue\nelse: raise ...` with a match/branch:
  - `EXITED`, `ALREADY_EXITED` → log success, continue (the server stopped).
  - `SIGNAL_NOT_DELIVERED` → raise `HttpShutdownError` (REQ-005: hard failure).
  - `EXIT_UNCONFIRMED` → log a warning and continue (REQ-005: degraded, not fatal).
- **Keep the loop and ordering unchanged.** The `for server_key in self._servers`
  iteration and per-server termination call stay as-is; only the post-call handling
  changes.
- **One exception type.** `HttpShutdownError` is the existing coordinator failure type
  (line `:38`); reuse it rather than introducing a new one.

## Alternatives considered

- Raising on every non-exit outcome — rejected by REQ-005: `EXIT_UNCONFIRMED` is a warn,
  not a raise, because a signal was delivered and the process may still stop.
- Collecting outcomes into a summary and deciding at the end — rejected: the Plan wants
  immediate per-server branching, and the current early-raise pattern is preserved.

## Implementation

### Target file

`scripts/agent/http_lifecycle_shutdown_coordinator.py`

### Procedure

1. Read `scripts/agent/http_lifecycle_shutdown_coordinator.py` around `:79-107`.
2. Import `TerminationOutcome` from `http_lifecycle_errors` (row 1).
3. In the loop, capture `outcome = await self._terminator.terminate_with_timeout(...)`
   and replace the bool branch with the three-way outcome branch from the Design
   decisions.
4. Raise `HttpShutdownError` only on `SIGNAL_NOT_DELIVERED`; warn on `EXIT_UNCONFIRMED`.
5. Confirm the other `shutdown_all` definitions (rows 4-9) compile against the new type.

### Method

In-place edit of the loop body. Do not reorder servers or change the timeout parameter.

### Details

- REQ-007 (graceful shutdown timeout across all servers) is already structurally present;
  this row wires the outcome-based decision into it.
- mypy across the five `shutdown_all` definitions proves the new return type flows
  everywhere the value is consumed.

## Compatibility considerations

- Behavioral: the coordinator now distinguishes `EXIT_UNCONFIRMED` (warn) from
  `SIGNAL_NOT_DELIVERED` (raise). Existing callers see finer-grained failures, not a
  coarse bool.
- No signature change; the method contract is stable, its decision detail is richer.

## Security considerations

- N/A: no auth, secret, or permission change.

## Rollback considerations

- Single logical commit; `git checkout -- scripts/agent/http_lifecycle_shutdown_coordinator.py`
  restores HEAD. Reversible; touches no config or DB.

## Validation plan

- `uv run pytest tests/agent/test_http_lifecycle_shutdown_coordinator.py` (row 13) —
  asserts warn-on-`EXIT_UNCONFIRMED` and raise-on-`SIGNAL_NOT_DELIVERED`.
- `uv run mypy --no-namespace-packages scripts/agent` (all five `shutdown_all` defs,
  rows 3-9).
- `uv run ruff check scripts/agent/http_lifecycle_shutdown_coordinator.py`.

## Completion criteria

`shutdown_all` branches on each server's `TerminationOutcome` per REQ-005, raises
`HttpShutdownError` only on `SIGNAL_NOT_DELIVERED`, warns and continues on
`EXIT_UNCONFIRMED`, and mypy plus tests pass.

## Out of Scope

- The vocabulary (row 1), the terminator conversion (row 2), the chain return (rows 4-9),
  the tests (row 13), and the docstring corrections (rows 5, 18-21).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Branch `shutdown_all` on `TerminationOutcome` (REQ-005, REQ-007) | Pending | — | — | |
| 2 | Add/update coordinator tests (row 13) | Pending | — | — | REQ-001 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | AC-9 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-005, REQ-007
- **Source issue**: `issues/20261021-093421_shutdown003-subprocess-termination-failures-report-success.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-082349_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-104938
- **Related target files**: `scripts/agent/http_lifecycle_shutdown_coordinator.py`
