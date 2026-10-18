# Implementation Procedure — `tests/agent/test_startup_rollback.py`

## Goal

Add regression coverage for surfacing startup rollback failures at the operator-visible
level (`REQ-002`, `REQ-003`, `REQ-004`).

## Scope

Modify only `tests/agent/test_startup_rollback.py`. Extend
`test_rollback_shutdown_failure_preserves_original_error` to assert the view emit
(`write_fatal`/`write_stderr`) was called on rollback failure and that the original error is
still raised; add/confirm a rollback-success assertion that no such emit occurs. Depends on
the code change in `scripts/agent/startup.py` (this plan's row 1).

## Assumptions

- The helper `_make_rollback_startup()` builds `orch = StartupOrchestrator(ctx, view)` with
  `view = MagicMock()`, so `view.write_fatal` / `view.write_stderr` are mockable.
- The rollback-failure path is driven by making a startup step raise while
  `shutdown_all()` also raises (as in the existing test).
- Row 1 adds an emit in the rollback-failure branch.

## Design decisions

- Assert the specific channel the implementation uses (start with `write_fatal`):
  `view.write_fatal.assert_called_once()` (or `.assert_called()`), matching the chosen
  approach in row 1.
- Assert the original error is still raised: `with pytest.raises(RuntimeError, match=...)`.
- For the success-path assertion, drive a run where `shutdown_all()` succeeds and assert the
  emit was NOT called.

## Alternatives considered

- Asserting exact call args vs. call presence: assert call presence (the message wording is
  an implementation detail); keep arg assertions minimal to avoid brittleness.

## Implementation

### Target file

`tests/agent/test_startup_rollback.py`

### Procedure

1. In `test_rollback_shutdown_failure_preserves_original_error`:
   - After `await orch.run()` raises, assert `view.write_fatal.assert_called_once()` (or the
     `write_stderr` variant actually used by row 1).
   - Keep/assert `pytest.raises(RuntimeError, match="...")` for the original error (REQ-002).
   - Keep `mock_lifecycle.shutdown_all.assert_awaited_once()`.
2. Add a rollback-success test (or extend an existing success-path test): drive `orch.run()`
   with `shutdown_all()` succeeding and assert `view.write_fatal` was NOT called (REQ-003).
3. Confirm all existing rollback tests still pass (re-raise behavior locked, REQ-002).

### Method

Append/extend test functions; reuse `_make_rollback_startup()` and the autouse
`_stub_component_init` fixture.

### Details

- If row 1 uses `write_stderr` instead of `write_fatal`, assert on `view.write_stderr`
  instead — keep the test aligned with the implementation choice.
- Ensure the success-path test exercises the same component-init stubbing so only the
  rollback window differs.

## Compatibility considerations

N/A: test-only change.

## Security considerations

N/A (operational-reliability property).

## Rollback considerations

Revert the commit to the test file.

## Validation plan

- Run the rollback suite; all pass.
- Command: `uv run pytest tests/agent/test_startup_rollback.py -q`.

## Completion criteria

The rollback-failure test asserts the view emit was called and the original error is still
raised; the rollback-success path produces no operator-visible rollback emit.

## Out of scope

`scripts/agent/startup.py` (separate row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the test changes in test_startup_rollback.py | Completed | 20261018-104329 | 20261018-104329 | align emit channel with row 1 |
| 2 | Add or update tests per Validation plan | Completed | 20261018-104329 | 20261018-104329 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261018-104329 | 20261018-104329 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261018-104329 | 20261018-104329 | N/A |

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
- **Requirement ID**: `REQ-002` (re-raise preserved), `REQ-003` (no emit on success),
  `REQ-004` (rollback-failure surfacing test)
- **Source issue**: `issues/20261017-123338_rollback01_surface-startup-rollback-failures-beyond-a-log-line.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-151428_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-162051
- **Related target files**: `tests/agent/test_startup_rollback.py`