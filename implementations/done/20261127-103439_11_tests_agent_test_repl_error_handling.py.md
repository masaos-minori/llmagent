## Goal

Cover the degraded-session refusal and the distinct display of a compensation failure in the REPL error-handling tests.

## Scope
**Release unit**: N/A: not part of a release unit

Requirement implemented: REQ-004 (degraded session cannot silently continue). Acceptance criterion: AC-3.

## Assumptions
- This row keeps its own document because it is cited by two target rows (`scripts/agent/session.py` and `scripts/agent/repl_input_loop.py`), so it fails the companion condition of a single citing row.
- The existing test at lines 123-158 pins the distinct surface of a compensated persistence error through `write_turn_not_persisted`; it stays valid and is extended, not replaced.

## Design decisions
- New cases are added beside the existing persistence-error test rather than modifying it, so the pinned distinct-surface assertion remains a regression guard.

## Alternatives considered
- N/A: the test target is fixed by the Plan row.

## Implementation
### Target file
`tests/agent/test_repl_error_handling.py`

### Procedure
- Add a test that a degraded session refuses the next turn: the orchestrator is not called and the loop stays responsive.
- Extend the existing persistence-error test to assert the surfaced message reports the compensation status.

### Method
- Build the same `AgentContext`/`CLIView` mock fixture used by the existing test (lines 126-138) and set the session's degraded state before the turn.
- Assert the refusal path writes a warning and returns to the input loop instead of dispatching a turn.

### Details
- The degraded state is read from the session object, so the mock session must expose the flag the implementation defines in `scripts/agent/session.py`.
- Step 3b correction (20261127): the full-suite run hung on `tests/agent/test_repl.py::TestInterruptByState::test_ctrl_c_during_a_turn_cancels_only_the_turn`. The `_make_bare_repl` fixture uses a bare `MagicMock()` ctx, so `ctx.session.is_degraded` was truthy and the new turn-entry refusal skipped the turn dispatch, leaving the test's `started` event unset and its `_ctrl_c` task waiting forever. Fix: pin `ctx.session.is_degraded = False` in the fixture.
- Step 3b correction (20261127): `AgentContext` is a plain class, so `MagicMock(spec=AgentContext)` does not expose `session` (an instance attribute set in `__init__`); the existing tests' fixture must assign `ctx.session` and pin `is_degraded = False` for the turn-entry check to read. Added to both existing loop tests.
- Step 3b correction (20261127): the same fixture fix is required in `tests/agent/test_repl_shutdown_machine.py` `_make_loop` (8 full-suite failures from the truthy mock before the fix; 14 passed after).

## Compatibility considerations
- N/A: test-only change.

## Security considerations
- N/A: test-only change.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_repl_error_handling.py` — the pinned lines 123-158 test and the new refusal test pass.

## Completion criteria
- A degraded session cannot silently continue to the next turn (AC-3).
- The compensation failure is surfaced distinctly from the generic turn error (AC-3).

## Out of Scope
- The implementation of the degraded flag and the refusal (their own target rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261127-114932 | files changed: tests/agent/test_repl_error_handling.py (refusal test + status assertion + fixture session) |
| 2 | Add or update tests per Validation plan | Completed | — | 20261127-114932 | pinned test extended; 4 passed fixture fix also applied to tests/agent/test_repl.py _make_bare_repl (pin is_degraded False); test_repl.py 98 passed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261127-114932 | 20261127-151312 | ruff passed; full-suite run deferred to end of batch end-of-batch full suite: 16009 passed, 5 skipped; diff-cover 93% >= 90% |

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
- **Requirement ID**: REQ-004 (degraded session cannot silently continue)
- **Source issue**: `issues/20261119-145308_cliplc010_strict-turn-persistence.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-211240_cliplc010_strict-turn-persistence.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-103439
- **Related target files**: `tests/agent/test_repl_error_handling.py`