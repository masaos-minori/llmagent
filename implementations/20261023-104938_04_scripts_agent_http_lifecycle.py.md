## Goal

Wire the graceful-shutdown timeout into `HttpServerLifecycleManager.shutdown_all`
(REQ-007) and update its internal call sites so they accept the `TerminationOutcome`
returned by `terminate_with_timeout` (row 2). This file is the manager that owns
`TERMINATE_TIMEOUT_SEC` and fans termination out to the coordinator (row 3); the
startup failure return contract (REQ-006) is triggered here indirectly via
`lifecycle.shutdown_all()` on startup failure (see row 10).

## Scope

`scripts/agent/http_lifecycle.py` only: the `shutdown_all` method (`:338`), the
`restart` method's termination call (`:328`, call at `:334`), and the module constant
`TERMINATE_TIMEOUT_SEC` (`:57`). Reference reads: the coordinator (row 3), the terminator
(row 2). No new public method.

## Assumptions

- `TERMINATE_TIMEOUT_SEC` (`:57`) is the graceful bound the coordinator applies; the
  change makes `shutdown_all` route through it explicitly rather than relying on a
  default.
- `restart` (`:334`) already awaits `terminate_with_timeout`; it now yields a
  `TerminationOutcome` instead of `bool`, which is a no-op at this call site but must
  still type-check under mypy.

## Design decisions

- **`shutdown_all` (`:338`) passes the graceful timeout to the coordinator.** The method
  currently delegates unconditionally; make the delegation carry `TERMINATE_TIMEOUT_SEC`
  (or confirm the coordinator already reads it from the terminator), so REQ-007's
  per-server timeout is explicit at the manager level.
- **Update the `restart` call site (`:334`).** It awaits `terminate_with_timeout`; no
  handling change is required beyond mypy acceptance of the new return type.
- **Import hygiene (`:46`).** `TerminationOutcome` is imported by the coordinator (row 3);
  this file does not need to name it unless the timeout wiring requires it.

## Alternatives considered

- Adding a new parameter to `shutdown_all` — rejected: the timeout already lives in
  `TERMINATE_TIMEOUT_SEC` (`:57`); threading a new arg would widen the signature for no
  benefit.
- Handling the outcome inline here instead of in the coordinator — rejected: the
  per-outcome branching belongs in the coordinator (row 3), not the manager.

## Implementation

### Target file

`scripts/agent/http_lifecycle.py`

### Procedure

1. Read `scripts/agent/http_lifecycle.py` around `:55-58`, `:328-343`.
2. In `shutdown_all` (`:338`), ensure the graceful `TERMINATE_TIMEOUT_SEC` (`:57`) is the
   bound passed to / read by the coordinator's termination loop (REQ-007).
3. Confirm the `restart` call at `:334` type-checks against the new
   `TerminationOutcome` return (row 2).
4. Leave the manager's start/health/restart logic untouched otherwise.

### Method

In-place edits to `shutdown_all` and a type-check pass on `restart`. Do not add methods.

### Details

- REQ-006 (`run()` returning `StartupFailure | HttpStartupError | None`) is owned by
  `startup.py` (row 10); this file participates because `run()` calls
  `lifecycle.shutdown_all()` on startup failure. No `run()` exists here.
- mypy across the five `shutdown_all` definitions (rows 3-9) validates the delegation.

## Compatibility considerations

- Behavioral: the graceful timeout is now explicit at the manager level; the shutdown
  outcome semantics come from the coordinator (row 3). No signature change to callers.

## Security considerations

- N/A: no auth, secret, or permission change.

## Rollback considerations

- Single logical commit; `git checkout -- scripts/agent/http_lifecycle.py` restores HEAD.
  Reversible; touches no config or DB.

## Validation plan

- `uv run pytest tests/agent/test_http_lifecycle.py` (row 15) — asserts the graceful
  timeout propagates through `shutdown_all`.
- `uv run mypy --no-namespace-packages scripts/agent` (rows 3-9).
- `uv run ruff check scripts/agent/http_lifecycle.py`.

## Completion criteria

`shutdown_all` (`:338`) applies `TERMINATE_TIMEOUT_SEC` (`:57`) as the graceful bound, the
`restart` call site (`:334`) type-checks against the new return type, and mypy plus tests
pass.

## Out of Scope

- The vocabulary (row 1), the terminator conversion (row 2), the coordinator branch
  (row 3), the other `shutdown_all` definitions (rows 4-9), the tests (row 15), and the
  docstring corrections (rows 5, 18-21).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Route graceful `TERMINATE_TIMEOUT_SEC` through `shutdown_all` (REQ-007) | Pending | — | — | |
| 2 | Add/update lifecycle tests (row 15) | Pending | — | — | REQ-001 |
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
- **Requirement ID**: REQ-006, REQ-007
- **Source issue**: `issues/20261021-093421_shutdown003-subprocess-termination-failures-report-success.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-082349_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-104938
- **Related target files**: `scripts/agent/http_lifecycle.py`
