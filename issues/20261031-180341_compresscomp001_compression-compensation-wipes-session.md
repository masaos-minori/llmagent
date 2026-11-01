# Turn compensation after history compression deletes the whole persisted session

## Priority
High

## Summary
When a turn compresses the conversation history and a later write in the same turn fails, `TurnPersistence` compensates by deleting every row with `message_id` greater than the turn-start marker. Compression rewrites the whole session with `replace_messages` (delete all rows, insert the compressed set). Because `messages.message_id` is `AUTOINCREMENT`, every re-inserted row is above the marker, so the compensation deletes the entire session from the database while the in-memory history is restored to the pre-turn, uncompressed snapshot. Make compensation correct for turns that include a compression rewrite.

## Background
Found during an adversarial review (`python-code-review`) of the agent REPL runtime.
- `plans/done/20261027-070403_turn001_atomic-turn-persistence.md` (REQ-006) intended that a mid-turn compression failure is compensated like any other turn write. Its compensation primitive is `SessionMessageRepository.delete_messages_from(session_id, marker)`, where the marker is `MAX(message_id)` captured by `AgentSession.turn_boundary` at turn start. That primitive is correct for appended rows; the plan did not cover a rewrite that reassigns every row id.
- In a turn, `WorkflowEngineAdapter._prepare_turn_input` appends the user message through the boundary and then calls `ConversationStateManager.handle_history_compression`, which calls `TurnPersistence.replace_messages`. The tool rounds and the final assistant message are written afterward through the same boundary.
- The in-memory side is restored by `ConversationState.restore_messages` from the snapshot taken before the compression.

## Problem
Sequence for a turn whose history exceeds the limit:
1. Turn start: marker is the session's current maximum `message_id` (6 in the reproduction); the snapshot holds the full, uncompressed history.
2. `replace_messages` deletes all rows of the session and inserts the compressed snapshot. New ids come from the `AUTOINCREMENT` sequence, so they are above the marker (7, 8, 9 in the reproduction).
3. A later boundary write raises `sqlite3.Error` (for example a locked or full database). `_fail_from_error` runs `delete_messages_from(session_id, marker)`.
4. That statement matches every re-inserted row. The session ends with zero persisted messages, and `conv.history` is restored to the old uncompressed snapshot, so memory and database disagree.

Reproduction (throwaway script, not committed): a temporary SQLite file with the real `messages` DDL, six prior rows, then `turn_start_marker`, `replace_messages` with three rows, and `delete_messages_from(1, marker)`. Observed: marker 6, rows after compression with ids 7 to 9, compensation deleted 3 rows, rows left for the session: 0. The real session database was not opened. The failing later write itself was not injected end to end.

## Reason for Change
This is silent loss of the user's whole persisted conversation, triggered by a transient database error in a turn that happened to compress. The next `/session load` of that session finds nothing, and the session list shows no messages. The atomicity feature exists to prevent exactly this class of loss, so it should not be able to cause it.

## Implementation Intent
Compensation must restore the database to what it was at turn start, including when the turn rewrote the session. Choose one consistent mechanism for the rewrite case, for example performing the compression rewrite and the rest of the turn in one database transaction, or capturing what is needed to undo the rewrite before it happens, or deferring the compression rewrite until the turn has otherwise succeeded. Keep the append-only path as it is. After a compensated failure the database and `conv.history` must describe the same conversation.

## Target Files or Areas
- `scripts/agent/turn_persistence.py` (`TurnPersistence.replace_messages`, `_compensate`, `_fail_from_error`)
- `scripts/agent/session_message_repo.py` (`replace_messages`, `delete_messages_from`, `turn_start_marker`)
- `scripts/agent/conversation_state_manager.py` (`handle_history_compression`)
- `tests/agent/test_history_compression_consistency.py`, `tests/agent/` turn persistence tests

## Required Changes
- Define and implement a compensation path that is correct after `replace_messages` within a turn (database content equals the turn-start content, or the compression result is kept consistently in both database and memory).
- Make the compensation fail safe: it must never delete rows that existed at turn start without a way to restore them.
- Add tests with a real temporary SQLite database: compress, then inject a failing later write, then assert the database rows equal the turn-start rows and equal `conv.history`.
- Keep the existing test for a failure of the compression write itself.

## Constraints
- Do not change the schema of `messages` or `sessions` without a migration decision.
- Append-only turns must keep the current compensation behavior and cost.
- The `/undo` boundary (`undo_floor_message_id`) must stay consistent with the surviving rows.
- Database work must stay off the event loop (worker thread), as in the current boundary.
- Tests must use a temporary database and must not touch the real session database.

## Acceptance Criteria
- A turn that compresses and then fails a later write leaves the session's persisted rows identical to the turn-start rows (or consistently compressed), never empty.
- `conv.history` and the persisted rows agree after the compensated failure.
- The new test fails on the current code and passes after the change.
- Existing turn persistence and undo tests still pass.

## Testing Expectations
- Integration-style unit tests as described, using a temporary SQLite database and injected `sqlite3.Error` on the write after the compression.
- Regression: run `tests/agent/test_history_compression_consistency.py`, the turn persistence tests, and the undo tests.
- Run `ruff` and `mypy --no-namespace-packages` on the touched files.

## Documentation Impact
Needs confirmation: check whether the turn persistence or session documentation under `docs/` states that a compression write is compensated like any other turn write. If it does, state the actual guarantee after the fix (what the database holds after a failed turn that compressed). Do not copy concrete values.

## Out of Scope
- Changing how or when compression is triggered, or the compression algorithm.
- The `cmd_rag_export*` scripts' own use of `replace_messages`.
- Restoring a session's compression summary on load (tracked separately).

## Dependencies
N/A: none. No open issue or in-flight plan targets `turn_persistence.py` or `replace_messages` for this behavior; the archived plan `plans/done/20261027-070403_turn001_atomic-turn-persistence.md` is history only.

## Unresolved Questions
- Whether `sqlite3.Error` after a successful compression is likely in practice (busy timeout, disk full): not measured. The severity assumes it can happen.
- Whether the preferred fix is a single transaction across the turn or deferring the rewrite: a design choice for the implementer.

## AI Implementation Instruction
Change only the persistence boundary and repository code needed for correct compensation after a rewrite, plus tests. Write the failing test first. Do not change compression selection or the schema. Stop and report if the fix needs a schema change or alters the `/undo` semantics.

## Traceability
- **Workflow phase**: python-code-review -> issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261031-180341
- **Related target files**: scripts/agent/turn_persistence.py, scripts/agent/session_message_repo.py, scripts/agent/conversation_state_manager.py, tests/agent/test_history_compression_consistency.py
