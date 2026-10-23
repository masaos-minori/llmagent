## Goal

Add/update the behavioral tests for the `TerminationOutcome` conversion (rows 2-3). This is
the Plan's highest-risk test row: the existing `test_http_lifecycle_process_terminator.py`
encodes the OLD `bool` contract (`assert result is True` at lines `:119`, `:135`, `:148`,
`:164`, `:245`, `:274`), which will break once `terminate_with_timeout` returns
`TerminationOutcome`. These tests assert each of the four outcomes for the corresponding
process state (REQ-001, REQ-004).

## Scope

`tests/agent/test_http_lifecycle_process_terminator.py` only. Update existing assertions
that check the return value; add new cases covering `SIGNAL_NOT_DELIVERED` and
`EXIT_UNCONFIRMED` escalation. Reference: the terminator (row 2), the coordinator (row 3).

## Assumptions

- Each existing `assert result is True` maps to a specific outcome per row 2's mapping; the
  tests must be migrated, not deleted.
- Real-child tests (`TestProcessTerminatorRealChild`, `:231-277`) exercise the exit and
  SIGKILL-escalation paths end-to-end.

## Design decisions

- **Migrate the bool assertions to outcome members**, matching row 2's arm mapping:
  - `:119` (no pgid, `proc.terminate()` fallback) → `TerminationOutcome.EXIT_UNCONFIRMED`.
  - `:135` (already exited, no signal) → `TerminationOutcome.ALREADY_EXITED`.
  - `:148` (non-integer pid, fallback) → `TerminationOutcome.EXIT_UNCONFIRMED`.
  - `:164` (resolved group, `poll()==0`) → `TerminationOutcome.ALREADY_EXITED`.
  - `:245` (child exits on SIGTERM) → `TerminationOutcome.EXITED`.
  - `:274` (child ignores SIGTERM, SIGKILL escalated) →
    `TerminationOutcome.EXIT_UNCONFIRMED`.
- **Add a `SIGNAL_NOT_DELIVERED` case**: mock `os.killpg` SIGKILL to raise `OSError` and
  assert `TerminationOutcome.SIGNAL_NOT_DELIVERED`.
- **Preserve the real-child tests** (`:231-277`), updating their `is True` assertions to
  the mapped outcomes.

## Alternatives considered

- Deleting the existing tests and rewriting from scratch — rejected: they encode valuable
  pgid-resolution and fallback coverage; migrate in place.

## Implementation

### Target file

`tests/agent/test_http_lifecycle_process_terminator.py`

### Procedure

1. Read `tests/agent/test_http_lifecycle_process_terminator.py` fully (`:1-277`).
2. Replace each `assert result is True` with the mapped
   `TerminationOutcome` member from the Design decisions.
3. Add a `SIGNAL_NOT_DELIVERED` unit test: patch `os.killpg` to raise `OSError` on the
   SIGKILL call and assert the returned outcome.
4. Update the real-child assertions (`:245`, `:274`) to their mapped outcomes.
5. Import `TerminationOutcome` from `agent.http_lifecycle_errors`.

### Method

Edit assertions in place; add one new test method to
`TestProcessTerminatorSigKillFailureScenarios`. Keep the `# nosec` helper `_spawn` intact.

### Details

- REQ-004 is covered by the `:274` migration (SIGKILL escalation → `EXIT_UNCONFIRMED`) and
  the new escalation assertion.
- If row 2's mapping differs, reconcile the test expectations with row 2 before running.

## Compatibility considerations

- N/A: test-only change. The assertions must match row 2's exact mapping or the suite
  fails.

## Security considerations

- N/A: no auth, secret, or permission change. The `# nosec B603` on `_spawn` (`:206`) is
  unchanged.

## Rollback considerations

- Single logical commit; `git checkout -- tests/agent/test_http_lifecycle_process_terminator.py`
  restores HEAD. Reversible; touches no config or DB.

## Validation plan

- `uv run pytest tests/agent/test_http_lifecycle_process_terminator.py` — all migrated and
  new cases pass.
- `uv run mypy --no-namespace-packages scripts/agent` (row 2's return type resolves here).
- `uv run ruff check tests/agent/test_http_lifecycle_process_terminator.py`.

## Completion criteria

Every prior `assert result is True`/`False` is migrated to the correct `TerminationOutcome`
member, a `SIGNAL_NOT_DELIVERED` case is added, real-child tests are updated, and the full
suite passes.

## Out of Scope

- The vocabulary (row 1), the terminator conversion (row 2), the coordinator branch
  (row 3), the launcher verify (row 5), the manager (row 4), and the docstring corrections
  (rows 18-21).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Migrate bool assertions to `TerminationOutcome` + add SIGNAL_NOT_DELIVERED case | Pending | — | — | High risk |
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
- **Requirement ID**: REQ-001, REQ-004
- **Source issue**: `issues/20261021-093421_shutdown003-subprocess-termination-failures-report-success.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-082349_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-104938
- **Related target files**: `tests/agent/test_http_lifecycle_process_terminator.py`
