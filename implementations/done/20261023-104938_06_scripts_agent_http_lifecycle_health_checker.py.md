## Goal

Confirm the health checker's call sites need no change now that the launcher (row 5)
tracks spawned subprocesses and the terminator (row 2) owns outcome reporting. The health
checker observes liveness, not termination; its contract is unchanged by this Plan.

## Scope

`scripts/agent/http_lifecycle_health_checker.py` only. Reference reads: the launcher
(row 5), the terminator (row 2). No code change unless verification finds a gap.

## Assumptions

- The health checker calls `_mark_health_checked` on the manager (`:159`, `:166`) and does
  not itself terminate processes; termination is the terminator's domain (row 2).

## Design decisions

- **Verify, do not modify.** Confirm the `HealthChecker` class (`:63`) and its timeout
  helper (`:67`) are consistent with the manager's shutdown flow, and that no call site
  assumes a bool return from `terminate_with_timeout`.
- **If a gap exists**, fix only the specific call site; otherwise leave untouched.

## Alternatives considered

- Adding health-aware termination hooks — rejected: out of scope; the Plan keeps health
  and termination separated.

## Implementation

### Target file

`scripts/agent/http_lifecycle_health_checker.py`

### Procedure

1. Read `scripts/agent/http_lifecycle_health_checker.py` around `:63-70`, `:135-167`.
2. Confirm no call site interprets `terminate_with_timeout`'s return (it does not).
3. Confirm the health-check timeout is independent of the shutdown timeout (row 2).
4. Record the confirmation; edit only if a gap is found.

### Method

Read-and-confirm. Edit only if verification finds a concrete gap.

### Details

- The health checker never returns or consumes `TerminationOutcome`; row 2's change is
  invisible to it.

## Compatibility considerations

### Corrections found while implementing

- Verify-only confirmed: the call at `http_lifecycle_health_checker.py:181` already passes `timeout=terminate_timeout_sec` (5.0) explicitly and does not read the return value; no edit. With the signature default removed, this explicit keyword is now required (AC-5).


- N/A unless a gap is found; this row is verification-first.

## Security considerations

- N/A: no auth, secret, or permission change.

## Rollback considerations

- Single logical commit; `git checkout -- scripts/agent/http_lifecycle_health_checker.py`
  restores HEAD. Reversible; touches no config or DB.

## Validation plan

- `uv run mypy --no-namespace-packages scripts/agent`.
- `uv run ruff check scripts/agent/http_lifecycle_health_checker.py`.

## Completion criteria

The health checker's call sites are consistent with the terminator's ownership of
termination (row 2); if unmodified, the confirmation is recorded and mypy passes.

## Out of Scope

- The vocabulary (row 1), the terminator conversion (row 2), the launcher (row 5), the
  tests (row 14), and the docstring corrections (rows 5, 18-21).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify health-checker call sites unchanged | Completed | 20261023-152942 | 20261023-152942 | Verify-only implemented; full suite passed |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261023-152942 | 20261023-152942 | AC-9 |
| 3 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261023-152942 | 20261023-152942 |  |

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
- **Requirement ID**: REQ-010 (indirect)
- **Source issue**: `issues/20261021-093421_shutdown003-subprocess-termination-failures-report-success.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-082349_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-104938
- **Related target files**: `scripts/agent/http_lifecycle_health_checker.py`