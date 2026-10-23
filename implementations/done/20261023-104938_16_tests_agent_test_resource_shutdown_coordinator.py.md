## Goal

Confirm `test_resource_shutdown_coordinator.py` covers the consumption site (row 9): the
gather of `svc.lifecycle.shutdown_all()` (`:138`) alongside `svc.http.aclose()` (`:139`)
with `return_exceptions=True` (`:140`), and that a raised `HttpShutdownError` does not
mask the HTTP close. Verify existing tests still pass.

## Scope

`tests/agent/test_resource_shutdown_coordinator.py` only. Reference: the resource
coordinator (row 9), the lifecycle coordinator (row 3). No change unless a gap is found.

## Assumptions

- The existing tests exercise WAL checkpoint/backup and task cancellation; the service
  lifecycle shutdown gather may be partially covered.

## Design decisions

- **Verify, then fill the gap.** Confirm there is a test asserting the lifecycle
  `shutdown_all` and HTTP `aclose` are gathered with `return_exceptions=True`. If absent,
  add a test where the lifecycle shutdown raises `HttpShutdownError` and assert the HTTP
  close still runs and the error is captured, not propagated.
- **Preserve existing coverage.**

## Alternatives considered

- Rewriting the resource coordinator test from scratch — rejected: verify-only, add
  minimally.

## Implementation

### Target file

`tests/agent/test_resource_shutdown_coordinator.py`

### Procedure

1. Search `test_resource_shutdown_coordinator.py` for `shutdown_all` / `aclose` / gather.
2. If the best-effort gather is unasserted, add the `HttpShutdownError`-does-not-block-HTTP-close
   case (row 9).
3. Otherwise record the confirmation.

### Method

Add one test method if a gap exists; otherwise no edit.

### Details

- Row 9's contract ("continue past a failure") is what keeps shutdown resilient; the test
  must prove the lifecycle error is captured, not raised.

## Compatibility considerations

### Corrections found while implementing

- Two cases added (`TestHttpTerminationReported`): two unconfirmed servers -> two `http_termination` entries while WAL and `aclose` still run; `[]` -> no warning.


- N/A unless a test is added; this row is verification-first.

## Security considerations

- N/A.

## Rollback considerations

- Single logical commit; `git checkout -- tests/agent/test_resource_shutdown_coordinator.py`
  restores HEAD. Reversible.

## Validation plan

- `uv run pytest tests/agent/test_resource_shutdown_coordinator.py`.
- `uv run mypy --no-namespace-packages scripts/agent`.
- `uv run ruff check tests/agent/test_resource_shutdown_coordinator.py`.

## Completion criteria

`test_resource_shutdown_coordinator.py` asserts the best-effort gather (row 9); a case is
added only if missing, and the suite passes.

## Out of Scope

- The vocabulary (row 1), the terminator conversion (row 2), the coordinator branch
  (row 3), the router (row 8), the tests (row 17), and the docstring corrections (rows
  18-21).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify/strengthen best-effort shutdown gather (row 9) | Completed | 20261023-152953 | 20261023-152953 | Verify-only implemented; full suite passed |
| 2 | Run validation sequence (`rules/toolchain.md`) | Completed | 20261023-152953 | 20261023-152953 | AC-9 |

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
- **Related target files**: `tests/agent/test_resource_shutdown_coordinator.py`