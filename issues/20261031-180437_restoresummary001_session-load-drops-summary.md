# Loading a compressed session silently drops its conversation summary

## Priority
High

## Summary
History compression summarizes old turns into one `[Conversation summary]` message with role `system`, deletes the old rows, and persists the compressed set. `restore_session` (used by `/session load`) discards every persisted system-role row and rebuilds history from only the current system prompt plus the non-system rows. After loading a session that was ever compressed, the model therefore has neither the old turns (deleted) nor their summary (dropped), and nothing tells the user. Make restore keep the summary without letting arbitrary persisted rows act as system instructions.

## Background
Found during an adversarial review (`python-code-review`) of the agent REPL runtime.
- `HistoryManager.compress` returns preserved system rows, then the single summary row, then the remaining turns (`issues/done/20261021-093421_turn006_history-compression-reorders-and-duplicates-summary.md` made the summary a single replaceable row). `TurnPersistence.replace_messages` stores that list; `SessionMessageRepository.replace_messages` deletes all rows of the session first, so the original turns exist nowhere else.
- `services/session_restore.restore_session` builds the restored history as the current `system_prompt_content` plus `[m for m in repaired if m["role"] != "system"]`. `_boundary_to_index` also subtracts every persisted system row when it converts the `/undo` boundary.
- `issues/done/20261017-123157_restore01_block-ephemeral-key-injection-through-session-history-restore.md` established that restored rows are untrusted because a local actor can edit the session database. That is a plausible reason system rows are not restored.
- The same persisted set can also contain the ephemeral memory block (`_memory_injected`), because compression keeps ephemeral system rows and `replace_messages` stores them without their marker key.

## Problem
Reproduction (throwaway script, not committed): rows shaped exactly as compression persists them (system prompt, a `[Conversation summary]` system row, one user row, one assistant row), a stubbed session API, and a real `ConversationState`, then `restore_session`. Observed: the persisted rows include the summary row; the restored history is system prompt, user row, assistant row; the summary row is absent. The real session database was not used.

Effects:
- A resumed session loses the earlier part of the conversation without any notice; later answers can contradict earlier decisions.
- The persisted ephemeral memory block, if present, is stored indefinitely but never restored, so the stored session no longer matches what the model saw.

## Reason for Change
`/session load` is the documented way to continue earlier work, and compressed sessions are exactly the long ones people want to continue. Losing the summary is a silent correctness failure, not a degraded mode.

## Implementation Intent
Distinguish three kinds of persisted system-role rows: the system prompt (replaced by the current one), the conversation summary (must be restored), and ephemeral injections such as the memory block (should not be persisted or restored). Restore the summary in a way that respects the existing untrusted-restore policy, so that a row an attacker added to the database cannot become an instruction merely by having role `system` (for example by recognizing only the summary shape through a single shared constant and validating it, or by restoring it under a controlled form). Keep the `/undo` boundary arithmetic consistent with whatever is restored.

## Target Files or Areas
- `scripts/agent/services/session_restore.py` (`restore_session`, `_boundary_to_index`)
- `scripts/agent/history.py` (`_SUMMARY_PREFIX`, `_build_summary_msg`, as the source of the summary shape)
- `scripts/agent/session_message_repo.py` (`replace_messages`, what is persisted)
- `scripts/agent/conversation_state_manager.py` (`handle_history_compression`, ephemeral rows at compression time)
- `tests/agent/` session restore and compression consistency tests

## Required Changes
- Restore the `[Conversation summary]` row after the system prompt when loading a session, with the trust handling described above.
- Stop persisting ephemeral system rows (memory block, other ephemeral rows) when the compressed set is stored, or filter them on restore by a rule that does not depend on the dropped marker key.
- Update the undo boundary conversion so the restored summary row is counted correctly.
- Add tests: compress, persist, restore, and assert the summary is present, that a forged non-summary system row is not restored as an instruction, and that the undo boundary still points at the same turn.

## Constraints
- Rows read from the database remain untrusted (see the restore01 issue); no arbitrary persisted system row may become a system instruction.
- Do not change the compression algorithm or the single-summary rule.
- The current system prompt must still replace any persisted prompt row.
- No schema change unless unavoidable; if needed, record the decision in the issue before implementing.

## Acceptance Criteria
- After compression and `/session load`, the restored history contains exactly one summary row, positioned after the system prompt.
- A persisted system row that is not the summary shape is still dropped.
- The ephemeral memory block is not present in the persisted rows after a compression.
- `/undo` after a load behaves as before the change for sessions with and without a summary.
- The new tests fail on the current code and pass after the change.

## Testing Expectations
- Unit tests of `restore_session` with a stubbed session API, plus a compression-then-restore round trip on a temporary SQLite database; include a forged system row case.
- Regression: run the session restore, compression consistency, undo, and message schema tests.
- Run `ruff` and `mypy --no-namespace-packages` on the touched files.

## Documentation Impact
Needs confirmation: check whether the session or history documentation describes what `/session load` restores. If it does, state that the summary is restored and which system rows are not, with the reason (untrusted restore). Do not copy concrete values.

## Out of Scope
- Changing how compression chooses turns or builds the summary.
- Replaying the original turns (they are deleted by compression and are not recoverable).
- Persistence compensation after a compressing turn (tracked in `issues/20261031-180341_compresscomp001_compression-compensation-wipes-session.md`).

## Dependencies
- Related to `issues/20261031-180341_compresscomp001_compression-compensation-wipes-session.md`: both concern what the database holds after compression. They touch `session_message_repo.py` and can be done in either order, but the persisted-row rules decided here should be reflected in that fix's tests.

## Unresolved Questions
- Whether dropping all persisted system rows was a deliberate security decision that also covered the summary, or an oversight: `Needs confirmation`. The fix must satisfy the untrusted-restore constraint either way.
- Whether a summary should be restored as a system row or in another controlled form: a design choice for the implementer.

## AI Implementation Instruction
Change only restore, the persisted-row filtering, and the matching tests. Keep the untrusted-restore guarantee: add no path by which an arbitrary stored system row reaches the model as an instruction. Reuse one shared constant for the summary shape instead of copying the prefix string. Stop and report if the fix would need a schema change.

## Traceability
- **Workflow phase**: python-code-review -> issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261031-180437
- **Related target files**: scripts/agent/services/session_restore.py, scripts/agent/history.py, scripts/agent/session_message_repo.py, scripts/agent/conversation_state_manager.py
