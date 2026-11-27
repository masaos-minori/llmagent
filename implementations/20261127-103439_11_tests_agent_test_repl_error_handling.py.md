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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
