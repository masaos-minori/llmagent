## Goal

Update `tests/agent/test_orchestrator.py` for the split of the combined `is_partial`
signal into `had_partial_text` and `was_compensated` (`ispartial001`). The single existing
test that asserted the combined value on a compensated-no-partial turn must change to assert
the new semantics (`partial_completion=false`, `was_compensated=true`, REQ-001); add tests that
pin both signals independently on the compensated branch.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `had_partial_text` is derived from `exc.partial_text`; `was_compensated` from
  `boundary.rollback_partial_turn()`'s return. Both are threaded positionally to
  `emit_turn_end` after `error_kind` (index 4 and 5).
- `_make_ctx()` configures `turn_boundary` so `rollback_partial_turn()` returns a falsy value
  on the transport-error tests (established by the currently-passing
  `test_turn_end_event_has_partial_completion_false_on_non_partial_error`, which has no commit
  and asserts `partial_completion is False`).

## Design decisions
- Repurpose the existing compensated test (`test_non_persistence_exception_after_commit_records_is_partial`)
  to assert the REQ-001 fix instead of the old combined value: `partial_completion is False`
  (no partial text) and `was_compensated is True`.
- Add a companion case asserting both signals true when a committed write is followed by a
  partial-text exception (compensated AND had partial text).

## Alternatives considered
- Leave the old test unchanged. Rejected: it would fail under the corrected semantics and
  silently encode the bug REQ-001 removes.

## Implementation
### Target file
`tests/agent/test_orchestrator.py`

### Procedure
1. Edit `test_non_persistence_exception_after_commit_records_is_partial`
   (`test_orchestrator.py:1595-1621`): keep `rollback_partial_turn` returning `True`; change
   the assertion at line 1621 from `assert events[0]["partial_completion"] is True` to two
   assertions: `assert events[0]["partial_completion"] is False` and
   `assert events[0]["was_compensated"] is True`. Update the comment to reference REQ-001.
2. Add `test_committed_partial_text_reports_both_signals` after it: same setup (commit +
   `rollback_partial_turn` returns `True`) but the escaping exception carries `partial_text`,
   asserting `events[0]["partial_completion"] is True` and `events[0]["was_compensated"] is True`.

### Method
- The new test reuses `_persistence_boundary_mock()` + `AsyncMock(return_value=True)` for
  `rollback_partial_turn` and an engine.run side_effect exception whose `.partial_text` is set
  (mirror `_make_err(kind="PREMATURE_EOF", partial_text="partial")` used by the passing
  transport-error tests).

### Details
- No other existing test changes: every remaining partial-completion / turn-end assertion
  holds under the new semantics (verified against current source):
  - Transport-error tests (1224/1244/1386/1404/1498): no committed write, so
    `was_compensated is False`; `partial_completion` mirrors `had_partial_text`, unchanged.
  - Success test (1477): `had_partial_text is False`, `was_compensated is False`.
  - `test_non_persistence_exception_without_commit_keeps_is_partial_false` (1624): both
    signals False.
  - `test_persistence_failure_sets_distinct_error_kind_and_reraises` (3769-3772): mocks
    `emit_turn_end` and asserts `call_args[3] == "persistence"` (error_kind) and
    `call_args[4] is False`. Under the new signature index 4 is `had_partial_text`, which is
    `False` on the `ConversationPersistenceError` path — assertion still holds.

## Compatibility considerations
- `emit_turn_end` gains two positional parameters; the mocked-call test asserts indices 3 and
  4, both unaffected on the persistence-failure path.

## Security considerations
N/A: test-only change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_orchestrator.py` — updated compensated test plus all
  partial-completion / turn-end tests pass.

## Completion criteria
- `test_non_persistence_exception_after_commit_records_is_partial` asserts
  `partial_completion is False` and `was_compensated is True`.
- New test pins both signals true on the partial-text + compensated branch.
- All other partial-completion / turn-end assertions pass unchanged.

## Out of Scope
- The production signal computation (`orchestrator.py`, covered by its own procedure).
- `audit_event_emitter.py` signature (covered by its own procedure).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261118 | 20261118 | implemented,2:tests added+passing,3:validation green (4386 passed) |
| 2 | Add or update tests per Validation plan | Completed | 20261118 | 20261118 | — |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261118 | 20261118 | — |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261118 | 20261118 | N/A: no doc edit required for this file |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`
- **Source issue**: issues/20261118-141333_ispartial001_partial-flag-metric-conflation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-143411_ispartial001_partial-flag-metric-conflation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-152456
- **Related target files**: tests/agent/test_orchestrator.py
