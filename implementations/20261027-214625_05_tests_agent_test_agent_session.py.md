# Implementation Procedure: Update `undo_last_turn` test cases to the row-list return type

## Goal

Update the `TestUndoLastTurn` and `TestUndoLastTurnBoundary` cases in `tests/agent/test_agent_session.py` to the new `list[DeletedRow]` return type (row 03) instead of int counts, keeping the boundary-gate assertions intact. (`REQ-001`, `REQ-005`, `REQ-006`)

## Scope

One test file, `tests/agent/test_agent_session.py`. Adapt the assertions in the `TestUndoLastTurn` class (L584-624) and the `TestUndoLastTurnBoundary` class (L638-705). No new tests here (the parity regression module is row 07).

## Assumptions

- After row 03, `session.undo_last_turn()` returns `list[DeletedRow]` (`[]` when blocked), ascending `message_id`.
- Existing `_msgs(session.fetch_messages(...))` unwrapping stays valid; the deleted rows carry `message_id`, `role`, `content`, `tool_call_id`.
- Overlap with `sess008` on this file: sess008 targets `turn_boundary()` factory consumers (await-contract), which do not exist until turn001 lands; this row targets the `undo_last_turn` cases (L584-705). Disjoint sections → Compatible. sess008 is Blocked until turn001 is implemented.

## Design decisions

- Replace `assert deleted == N` with `assert len(deleted) == N` and, where useful, assert the returned `message_id`s are ascending and match the expected deleted set. Replace `assert deleted == 0` with `assert deleted == []`.
- Keep the boundary-gate structure (patched `SQLiteHelper`, `undo_floor_message_id` UPDATE) unchanged; only the assertion on the return value changes.

## Alternatives considered

- Rewriting the cases from scratch — rejected: the fixture/boundary setup is correct; only the return-value assertions need adapting (minimal, mechanical change).

## Implementation

### Target file
`tests/agent/test_agent_session.py`

### Procedure
1. In `TestUndoLastTurn.test_removes_from_last_user_message`: change `assert deleted == 2` to `assert len(deleted) == 2`; optionally assert `[r.message_id for r in deleted]` is ascending.
2. `test_with_tool_result_messages`: `assert deleted == 1` → `assert len(deleted) == 1`.
3. `test_no_op_when_no_user_message`, `test_no_op_when_session_id_none`, `test_no_op_when_empty_history`: `assert deleted == 0` → `assert deleted == []`.
4. `TestUndoLastTurnBoundary.test_blocks_when_last_user_at_or_before_boundary`: `assert session.undo_last_turn() == 0` → `assert session.undo_last_turn() == []`.
5. `test_deletes_only_last_turn_beyond_boundary`: `assert session.undo_last_turn() == 2` → `assert len(session.undo_last_turn()) == 2`.

### Method
Mechanical assertion edits across seven sites in two classes. No signature or fixture change.

### Details
- Deleted rows are `DeletedRow` (new) instances; `len()` gives the count, `.message_id` gives identity. For the boundary-below test, the two deleted rows should have ascending ids greater than the boundary id (1).

## Compatibility considerations

- Test-only change; no production code touched. The `TestAgentSessionRagBoundary.test_delete_last_turn_absent_from_facade` case (L734) already asserts no `delete_last_turn` attribute — unaffected.

## Security considerations

- N/A: test-only.

## Rollback considerations

- Single logical commit touching this test file; rollback is `git revert`.

## Validation plan

- `uv run pytest tests/agent/test_agent_session.py -q` — all `undo` cases pass with the new return type.
- Static: `uv run ruff check tests/agent/test_agent_session.py` and `uv run mypy --no-namespace-packages tests/agent/test_agent_session.py` — clean.

## Completion criteria

- All `TestUndoLastTurn` / `TestUndoLastTurnBoundary` assertions read the row-list return (`len()` / `== []`); boundary-gate behavior asserted unchanged.
- pytest green; mypy/ruff clean.

## Out of Scope

- New parity regression tests (row 07).
- The regression-artifact module (row 06).
- Production changes (rows 01-04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Adapt the seven undo assertions to the row-list return type | Pending | — | — | |
| 2 | Run the validation sequence (pytest + static) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001`, `REQ-005`, `REQ-006`
- **Source issue**: issues/20261026-224959_undo002_undo-db-memory-set-consistency.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-074657_undo002_undo-db-memory-set-consistency.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-214625
- **Related target files**: tests/agent/test_agent_session.py
