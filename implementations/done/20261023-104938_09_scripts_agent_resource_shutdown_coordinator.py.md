## Goal

Verify that `ResourceShutdownCoordinator` consumes the lifecycle shutdown correctly: it
awaits `svc.lifecycle.shutdown_all()` alongside `svc.http.aclose()` in a single
`asyncio.gather` (`:138-140`), and that the outcome-based behavior from the coordinator
(row 3) is handled there without masking the HTTP close. This is a consumption-site check.

## Scope

`scripts/agent/resource_shutdown_coordinator.py` only. Reference reads: the coordinator
(row 3), the router (row 8). No code change unless verification finds a gap.

## Assumptions

- The gather at `:138-140` uses `return_exceptions=True` (`:140`), so a raised
  `HttpShutdownError` from one service does not prevent the other from closing.

## Design decisions

- **Verify, do not modify.** Read the shutdown block around `:137-145` and confirm:
  - `svc.lifecycle.shutdown_all()` (`:138`) is awaited before or alongside `svc.http.aclose()`
    (`:139`).
  - `return_exceptions=True` (`:140`) preserves the "continue past a failure" contract.
  - The error labeling (`:143`) distinguishes `lifecycle_shutdown` from `http_close`.
- **If a gap exists** (e.g., ordering that drops the lifecycle shutdown), fix only that
  block.

## Alternatives considered

- Changing the gather to raise on first failure — rejected: the existing
  `return_exceptions=True` (`:140`) is intentional for best-effort shutdown.

## Implementation

### Target file

`scripts/agent/resource_shutdown_coordinator.py`

### Procedure

1. Read `scripts/agent/resource_shutdown_coordinator.py` around `:115-150`.
2. Confirm the lifecycle `shutdown_all` (`:138`) and HTTP `aclose` (`:139`) are gathered
   with `return_exceptions=True` (`:140`).
3. Confirm the per-result error handling (`:143`) covers the lifecycle path.
4. Record the confirmation; edit only if a gap is found.

### Method

Read-and-confirm against the shutdown block. Edit only if verification finds a concrete gap.

### Details

- This is the outermost shutdown layer; it must not swallow the `HttpShutdownError`
  that row 3 raises on `SIGNAL_NOT_DELIVERED`, but also must not let it block the HTTP
  close. The existing gather already expresses this.

## Compatibility considerations

### Corrections found while implementing

Authoritative contract is the source plan's REQ-001..REQ-011 (plans/done/20261022-082349_plan.md); this procedure's earlier Design/Procedure text diverged from it (wrong REQ numbering, nonexistent `HttpShutdownError`, a `for server_key in self._servers` loop, raising on a failed outcome) and was not followed. Contrary to 'verify only': the service gather now uses a distinct `svc_results` name; a list result at index 0 is turned into one `("http_termination", "<key> (<outcome>)")` entry per item. pid/pgid are in the agent log line of the terminator/coordinator, not in the summary entry, because the plan fixes the carried type at `(str, TerminationOutcome)`.


- N/A unless a gap is found; this row is verification-first.

## Security considerations

- N/A: no auth, secret, or permission change.

## Rollback considerations

- Single logical commit; `git checkout -- scripts/agent/resource_shutdown_coordinator.py`
  restores HEAD. Reversible; touches no config or DB.

## Validation plan

- `uv run mypy --no-namespace-packages scripts/agent`.
- `uv run ruff check scripts/agent/resource_shutdown_coordinator.py`.

## Completion criteria

The shutdown block gathers lifecycle `shutdown_all` (`:138`) and HTTP `aclose` (`:139`)
with `return_exceptions=True` (`:140`) and labels results (`:143`); if unmodified, the
confirmation is recorded and mypy passes.

## Out of Scope

- The vocabulary (row 1), the terminator conversion (row 2), the coordinator branch
  (row 3), the router (row 8), the tests (rows 16), and the docstring corrections
  (rows 5, 18-21).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify shutdown consumption at gather (`:138-140`) | Completed | 20261023-152945 | 20261023-152945 | Verify-only implemented; full suite passed |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261023-152945 | 20261023-152945 | AC-9 |
| 3 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261023-152945 | 20261023-152945 |  |

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
- **Requirement ID**: REQ-007 (indirect)
- **Source issue**: `issues/20261021-093421_shutdown003-subprocess-termination-failures-report-success.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-082349_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-104938
- **Related target files**: `scripts/agent/resource_shutdown_coordinator.py`