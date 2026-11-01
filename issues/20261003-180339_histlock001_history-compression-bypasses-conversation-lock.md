# History compression bypasses conversation lock

## Priority
Low

## Summary
`ConversationState` documents that history access is synchronized via an `asyncio.Lock`, but `handle_history_compression()` in `conversation_state_manager.py` reassigns `ctx.conv.history` without acquiring that lock, from a list built from a pre-await snapshot (the compression awaits an LLM summarization round trip). A concurrent append during that window would be silently dropped. No active writer was found, so this is a latent trap, not a demonstrated bug.

## Background
Found during an adversarial code review (`python-code-review` skill) of the REPL's session-state subsystem (`scripts/agent/context.py`, `scripts/agent/conversation_state_manager.py`, `scripts/agent/history.py`).

## Problem
`scripts/agent/context.py`, `ConversationState` docstring: history access is synchronized via `asyncio.Lock`, and locking must be added if concurrent access becomes possible. `append_message()`, `extend_messages()` and `replace_history()` take `self._ensure_lock`. In `scripts/agent/conversation_state_manager.py`, `handle_history_compression()` does `ctx.conv.history, result = await ctx.services_required.hist_mgr.compress(ctx.conv.history)`: `compress()` awaits `_check_limits` and `_get_summary_text`, and the compressed list is built from the pre-await snapshot; the caller then reassigns `ctx.conv.history` with no lock. `clear_previous_turn_ephemeral_messages()` also reassigns directly, but it is synchronous with no await between read and write, so on a single event loop it cannot interleave and does not need the lock.

## Reason for Change
If a coroutine calls `append_message()` or `extend_messages()` (which mutate the old list in place) while `compress()` is in flight, that append is invisible to the new list and is dropped on the swap. The only `create_task` in `conversation_state_manager.py` is the first-turn title generation, which runs before compression and writes only the session title, so the risk is latent; it matches the class of race the `ConversationState` docstring warns about.

## Implementation Intent
Route the compression swap through `ConversationState`'s lock with a new helper that performs a raw swap of the history list under `self._ensure_lock` and keeps messages appended during the await. Do not reuse the existing `replace_history(msgs, *, source=...)`: it is async, clears and re-validates each message as untrusted and strips ephemeral and summary markers, which would change the compressed result.

## Target Files or Areas
- `scripts/agent/context.py` (`ConversationState`, new lock-guarded swap helper with a name distinct from `replace_history`)
- `scripts/agent/conversation_state_manager.py` (`handle_history_compression()`)

## Required Changes
- Add a lock-guarded raw-swap method (for example `swap_history`) on `ConversationState`.
- Use it in `handle_history_compression()` instead of direct assignment, preserving any message appended between the snapshot and the swap.
- Record the result of the background-task audit below.
- Audit every `asyncio.create_task(...)` site reachable during a turn for calls to `append_message()`/`extend_messages()` during the compression await window.

## Constraints
- Do not change `compress()`'s own summarization logic or its return contract.
- Do not introduce a new lock — reuse `ConversationState`'s existing `self._ensure_lock`.

## Acceptance Criteria
- `handle_history_compression()` mutates `ctx.conv.history` only through a lock-guarded path.
- A concurrent `append_message()` during `compress()`'s in-flight LLM round trip is not dropped (verified by a test that interleaves an append with an in-flight compression call).

## Testing Expectations
Add a test that starts `handle_history_compression()`, interleaves a concurrent `append_message()` call during the simulated LLM round trip, and asserts the appended message survives the compression swap. Run `tests/agent/test_conversation_state_manager.py` and `tests/agent/test_context.py` after the change.

## Documentation Impact
N/A: `ConversationState`'s own docstring already documents the intended locking contract; this fix brings the code into conformance with it.

## Out of Scope
- `HistoryManager.compress()`'s own selection logic.
- Any change to the first-turn title-generation background task.
- `clear_previous_turn_ephemeral_messages()`, which is synchronous and cannot interleave.

## Dependencies
N/A: none. The related `histsel001` issue was closed because `history_selection_policy` was rewritten; the `undo_floor` and `replace_messages` code near this swap may still touch the same lines.

## Unresolved Questions
Whether any `asyncio.create_task(...)` site reachable during a turn appends to `ctx.conv.history` during the compression window today: only `_on_first_turn` was found in `conversation_state_manager.py`; a full audit of the workflow executor and tool_runner background paths is still needed before the issue can be closed as confirmed inactive.

## AI Implementation Instruction
Add the lock-guarded swap helper on `ConversationState` first (not reusing `replace_history`), then update `handle_history_compression()` to use it. Perform the background-task audit and record its result. Add the interleaving regression test before considering this done.

## Traceability
- **Workflow phase**: python-code-review -> issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261003-180339
- **Related target files**: scripts/agent/context.py, scripts/agent/conversation_state_manager.py, scripts/agent/history.py
