## Goal

Confirm `test_lifecycle.py` covers REQ-010: the launcher starts each subprocess in its own
session (`start_new_session=True`) so the terminator's `os.killpg` path (row 2) has a real
group. This is a verify-and-strengthen row; add a case only if launcher session tracking
is untested.

## Scope

`tests/agent/test_lifecycle.py` only (1496 lines). Reference: the launcher (row 5), the
terminator (row 2). No change unless a gap is found.

## Assumptions

- This file already exercises the manager's start/health/restart/shutdown flow; the
  launcher's `Popen` construction (`start_new_session=True`) may or may not be asserted.

## Design decisions

- **Verify, then fill the gap.** Confirm there is a test asserting the launcher passes
  `start_new_session=True` to `Popen`. If absent, add one real-child test that launches a
  subprocess and asserts `os.getpgid(pid) == pid` (session-leader invariant), which is what
  row 2's termination depends on.
- **Preserve existing coverage.** Do not touch unrelated manager/health tests.

## Alternatives considered

- Refactoring `test_lifecycle.py` to centralize launcher assertions — rejected: verify-only,
  add minimally.

## Implementation

### Target file

`tests/agent/test_lifecycle.py`

### Procedure

1. Search `test_lifecycle.py` for `start_new_session` / `Popen` / `getpgid`.
2. If unasserted, add a real-child test asserting the session-leader invariant (REQ-010).
3. Otherwise record the confirmation.

### Method

Add one test method if a gap exists; otherwise no edit.

### Details

- REQ-010 ties here: without the session-leader assertion, a regression that drops
  `start_new_session=True` would go undetected and break row 2's termination.

## Compatibility considerations

- N/A unless a test is added; this row is verification-first.

## Security considerations

- N/A.

## Rollback considerations

- Single logical commit; `git checkout -- tests/agent/test_lifecycle.py` restores HEAD.
  Reversible.

## Validation plan

- `uv run pytest tests/agent/test_lifecycle.py`.
- `uv run mypy --no-namespace-packages scripts/agent`.
- `uv run ruff check tests/agent/test_lifecycle.py`.

## Completion criteria

`test_lifecycle.py` asserts the launcher's `start_new_session=True` / session-leader
invariant (REQ-010); a case is added only if missing, and the suite passes.

## Out of Scope

- The vocabulary (row 1), the terminator conversion (row 2), the coordinator branch
  (row 3), the manager (row 4), and the docstring corrections (rows 18-21).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify/strengthen launcher session test (REQ-010) | Pending | — | — | Verify-only |
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
- **Requirement ID**: REQ-010
- **Source issue**: `issues/20261021-093421_shutdown003-subprocess-termination-failures-report-success.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-082349_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-104938
- **Related target files**: `tests/agent/test_lifecycle.py`
