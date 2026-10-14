# Implement the /undo compression boundary (turns before compression cannot be undone)

## Priority
Medium

## Summary
Implement the specified `/undo` behavior: messages that existed when the history was last compressed (automatic compression, `/compact`, or fallback truncation) cannot be undone. The boundary is persisted in a new column `sessions.undo_floor_message_id` and restored by `/session load`. This resolves former Known Issue AGENT-008.

## Background
The specification was decided on 2026-10-14 (option A: store the boundary in `sessions`) and is already reflected in docs: `agent_07_03`, `agent_07_07`, `agent_04_01`, `agent_04_02`, `agent_09_01`, `db_02` section 6, `deployment_01` (upgrade note); AGENT-008 was removed from `governance_03`. No ADR is required because no ADR decision changes. The code does not implement it yet, so the docs currently describe the target behavior.

## Problem
- Compression rewrites the stored snapshot through `SessionMessageRepository.replace_messages()`; the summary (`[Conversation summary]`, `role=system`) replaces older messages.
- `scripts/agent/services/undo_service.py` `undo_last_turn()` finds the last `role='user'` message in `ctx.conv.history` with no knowledge of compression, and only returns a warning when the removed range contains a summary.
- It trims `ctx.conv.history` before calling `ctx.session.undo_last_turn()`, so a DB failure leaves history and DB inconsistent.
- `AgentSession.delete_last_turn()` (deletes at most the last 2 rows) has no production caller in `scripts/`.

## Reason for Change
After compression, the undoable range is unclear and a summary can be destroyed. A persisted boundary makes the range defined, survives `/session load`, and lets the DB itself refuse to delete rows at or before the boundary.

## Implementation Intent
- Add `sessions.undo_floor_message_id INTEGER NOT NULL DEFAULT 0` (0 = never compressed). The boundary is a `messages.message_id` (an `INTEGER PRIMARY KEY AUTOINCREMENT` exists, so the premise holds).
- Update the boundary in the same transaction as the snapshot rewrite: boundary = max `message_id` of the session after the rewrite.
- Keep an in-memory `ctx.conv.undo_floor` (index into `ctx.conv.history`; 0 = no boundary), updated after a successful snapshot write, reset on `/clear`, and derived from row IDs on `/session load`.
- `/undo`: search for the last user message only at or after the floor; if none, change nothing (history and DB) and report why. Delete in the DB first, restricted to `message_id` greater than the stored boundary, then change history through a verified method.
- Remove `delete_last_turn()` (no caller) instead of keeping a compatibility copy.
- Keep the existing stripping of preceding `_memory_injected` / `_ephemeral` markers in `undo_service`.

## Target Files or Areas
- `scripts/db/schema_sql.py` (`sessions` DDL in `_SESSION_SCHEMA_TEMPLATE`)
- `scripts/agent/session_message_repo.py` (`replace_messages()`, `fetch_messages()`; the current signature returns None and returns early on an empty list)
- `scripts/agent/session.py` (`AgentSession`: `replace_messages()`, `undo_last_turn()`, `delete_last_turn()`)
- `scripts/agent/services/undo_service.py`, `scripts/agent/services/models.py` (`UndoResult`), `scripts/agent/commands/cmd_context.py` (the `/undo` caller)
- `scripts/agent/conversation_state_manager.py` (`handle_history_compression()`), `scripts/agent/commands/cmd_rag_export.py` (`/compact` path calling `replace_messages()`)
- `scripts/agent/services/session_restore.py` (boundary restore on `/session load`)
- `scripts/agent/context.py` (`ctx.conv.undo_floor`, `/clear` reset) and the `ConversationState` definition (verified truncation method)
- `tests/` for each area above; `docs/23_agent/agent_13_reference-api-generated.md` (regenerate)

## Required Changes
- Add the column to the `sessions` DDL.
- Make the snapshot rewrite and boundary update atomic; update the boundary only when a snapshot is actually written (both callers write only when compression changed something).
- Add `ctx.conv.undo_floor`; set it after a successful write; reset on `/clear`; start at 0 on `/clear new`.
- On `/session load`, fetch rows with their IDs and the stored boundary, then convert the boundary row ID into a history index.
- Rework `undo_last_turn()` so it never deletes at or before the boundary, never mutates when nothing is undoable, and deletes in the DB before touching history.
- Show `Nothing to undo: the conversation was compressed, and turns before compression cannot be undone.` when blocked by the boundary; keep the current message when never compressed. Remove the summary-warning branch.
- Delete `AgentSession.delete_last_turn()` and its tests; confirm no remaining reference.
- Regenerate generated reference docs.

## Constraints
- Do not add a compatibility shim; remove the old behavior and function.
- `session.sqlite` has no incremental migration mechanism, and the `_SESSION_SCHEMA_TEMPLATE` comment states that the migration-versus-recreate decision is deferred to the next session.sqlite schema-change proposal, which must address data preservation. The decided approach is recreation (see Unresolved Questions).
- Ephemeral messages (`_ephemeral`, `_memory_injected`) can be in history without a DB row, so a history index cannot be derived from a row count; use row IDs.
- Never touch `/opt/llm` production DBs from tests; follow the existing test isolation (patched `build_db_config`, fake `SQLiteHelper`).

## Acceptance Criteria
- A turn added after compression can be undone (history and DB); the summary remains in both.
- Turns at or before the boundary, including protected recent turns, cannot be undone; nothing changes and the message above is shown.
- Automatic compression, `/compact`, and fallback truncation each create a boundary.
- After `/session load`, the same boundary applies (compress, add 2 turns, load, `/undo` three times: two succeed).
- A failure inside the snapshot rewrite changes neither snapshot nor boundary; a failed DB delete leaves history unchanged.
- With `ctx.conv.undo_floor` forced to 0, rows at or before the DB boundary are still not deleted.
- Never-compressed sessions behave as before; `/clear` and `/clear new` reset the boundary.
- A DB created by `create_session_schema()` has `undo_floor_message_id` with default 0.
- `delete_last_turn` has zero references in code, tests, and docs.

## Testing Expectations
- Unit and integration tests for each acceptance criterion above (fake `SQLiteHelper` backed by in-memory SQLite, as in `tests/agent/test_agent_session.py`).
- Schema test for the new column and default.
- `uv run ruff`, `mypy --no-namespace-packages scripts/`, `lint-imports`, bandit, full `pytest`, `diff-cover`.
- Run all test commands with the sandbox config so no production DB is opened.
- Docs checkers per `routing.md` plus `tools/generate_reference_table.py` where applicable.

## Documentation Impact
The docs listed in Background already describe the target behavior. After implementation: regenerate `agent_13_reference-api-generated.md`; confirm `agent_12_reference-api.md` and `agent_10_01` need no change; run the docs checkers.

## Out of Scope
- Adding an incremental migration mechanism to `session.sqlite` (would change the db_03 policy; separate proposal).
- Making compression preserve original messages.
- The memory/session responsibility changes tracked separately.
- Production deployment and the actual recreation of the production `session.sqlite`.

## Dependencies
- Depends on the docs already updated on 2026-10-14.
- The release needs the recreation procedure in `deployment_01` (Upgrade note: `/undo` compression boundary).

## Unresolved Questions
- The schema comment requires the next session.sqlite schema change to address data preservation, while the decided approach is lossy recreation (sessions, messages, and diagnostics are lost; memories are recovered from JSONL without deletes and pins). Confirm the decision, or choose `ALTER TABLE sessions ADD COLUMN ... DEFAULT 0` at startup (which needs a db_03 policy change).
- `session_message_repo.replace_messages()` returns early on an empty list: decide whether the boundary resets to 0 in that case.
- `cmd_rag_export.py` and `conversation_state_manager.py` each decide when to write the snapshot; confirm both route through one boundary-updating path.
- Whether `_ephemeral` / `_memory_injected` messages are written to `messages` was not verified; it determines the row-ID-to-index conversion on `/session load`.

## AI Implementation Instruction
Implement only what this issue states, in the order: DDL, repository and session, context, undo service, compression callers, restore, tests, generated docs. Verify each Unresolved Question against the code before relying on it. Prefer existing repository patterns; no compatibility code; no changes to `/opt/llm`.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261014-154803
- **Related target files**: scripts/db/schema_sql.py, scripts/agent/session_message_repo.py, scripts/agent/session.py, scripts/agent/services/undo_service.py, scripts/agent/conversation_state_manager.py, scripts/agent/commands/cmd_rag_export.py, scripts/agent/services/session_restore.py, scripts/agent/context.py
