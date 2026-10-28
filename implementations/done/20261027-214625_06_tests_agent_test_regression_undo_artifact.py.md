# Implementation Procedure: Update regression-artifact DB-undo assertions to row-list returns

## Goal

Adapt `tests/agent/test_regression_undo_artifact.py` to the new `list[DeletedRow]` return type (row 03) — replacing count assertions with `len()` / `== []` — while keeping the artifact walk-back and history/DB-parity expectations (`REQ-002`, `REQ-005`).

## Scope

One test file, `tests/agent/test_regression_undo_artifact.py`. Adapt assertions in `TestUndoLastTurnDeletesFromDb`, `TestUndoHistoryDbParity`, and `TestUndoReturnValue` (L145-232). No new tests here (row 07).

## Assumptions

- After row 03, `session.undo_last_turn()` returns `list[DeletedRow]` (`[]` when blocked).
- Cases that call `session.undo_last_turn()` without asserting the return (e.g. `test_undo_preserves_earlier_turns`, `test_history_length_matches_db_after_undo`) need no change beyond remaining valid.

## Design decisions

- `assert deleted == 2` → `assert len(deleted) == 2`; `assert deleted == 0` → `assert deleted == []`; `assert count == 2` → `assert len(count) == 2`.
- Keep the `_msgs(fetch_messages(...))` parity assertions unchanged.

## Alternatives considered

- Rewriting the fixtures — rejected: the `_FakeSQLiteHelper`/fixture setup is correct; only the return-value assertions adapt.

## Implementation

### Target file
`tests/agent/test_regression_undo_artifact.py`

### Procedure
1. `TestUndoLastTurnDeletesFromDb.test_undo_removes_user_and_assistant`: `assert deleted == 2` → `assert len(deleted) == 2`.
2. `TestUndoHistoryDbParity.test_undo_noop_when_no_messages`: `assert deleted == 0` → `assert deleted == []`.
3. `TestUndoReturnValue.test_undo_returns_count_of_deleted_rows`: `assert count == 2` → `assert len(count) == 2`.
4. `TestUndoReturnValue.test_undo_single_message_returns_one`: `assert count == 1` → `assert len(count) == 1`.
5. Leave the two cases that ignore the return value as-is.

### Method
Mechanical assertion edits across four sites in three classes.

## Compatibility considerations

- Test-only; no production code touched. Artifact walk-back expectations preserved (AC-005).

## Security considerations

- N/A: test-only.

## Rollback considerations

- Single logical commit; rollback is `git revert`.

## Validation plan

- `uv run pytest tests/agent/test_regression_undo_artifact.py -q` — all cases pass.
- Static: `uv run ruff check tests/agent/test_regression_undo_artifact.py` and `uv run mypy --no-namespace-packages tests/agent/test_regression_undo_artifact.py` — clean.

## Completion criteria

- All count assertions read the row-list return (`len()` / `== []`); history/DB parity assertions unchanged. pytest green; mypy/ruff clean.

## Out of Scope

- New parity regression tests (row 07).
- `test_agent_session.py` updates (row 05).
- Production changes (rows 01-04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Adapt the four count assertions to the row-list return type | Completed | 20261028-094341 | 20261028-094341 |  |
| 2 | Run the validation sequence (pytest + static) | Completed | 20261028-094341 | 20261028-094341 |  |

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
- **Requirement ID**: `REQ-002`, `REQ-005`
- **Source issue**: issues/20261026-224959_undo002_undo-db-memory-set-consistency.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-074657_undo002_undo-db-memory-set-consistency.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-214625
- **Related target files**: tests/agent/test_regression_undo_artifact.py