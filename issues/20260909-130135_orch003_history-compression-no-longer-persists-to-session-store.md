# History compression no longer persists compressed history to the session store

## Priority
High

## Summary
`tests/integration/test_orchestrator_integration.py::TestCompleteTurnExecution::test_handle_turn_history_compression_persists_when_needed`
fails with `AssertionError: Expected 'replace_messages' to have been called once. Called
0 times.` Confirmed genuine production defect (not a stale test): the
`Orchestrator._handle_history_compression()` extraction dropped the
`ctx.session.replace_messages(...)` call that persisted compressed conversation history
back to the session store. Compression now only updates in-memory `ctx.conv.history`,
so the persisted session store still holds the pre-compression history, including any
ephemeral system messages the compression step was designed to strip.

## Background
Before commit `35a1e1969` ("refactor: extract orchestrator into dedicated component
modules"), `Orchestrator._handle_history_compression()` explicitly called
`ctx.session.replace_messages(ctx.conv.history)` after compressing — confirmed by an
earlier commit's own message describing this exact call: `_handle_history_compression()`
now strips ephemeral system messages before calling `replace_messages()`, so they are
not reloaded in future sessions. This was a deliberate design decision, not incidental
behavior.

## Problem
Post-refactor, `Orchestrator._handle_history_compression()` delegates to
`ConversationStateManager.handle_history_compression()`
(`scripts/agent/conversation_state_manager.py`), whose entire body is:
```python
if ctx.services_required.hist_mgr is not None:
    ctx.conv.history, _result = await ctx.services_required.hist_mgr.compress(ctx.conv.history)
```
This updates `ctx.conv.history` in memory only — it never calls
`ctx.session.replace_messages(...)`. The persistence call was dropped during
extraction, not intentionally removed as part of a documented design change (no commit
message or code comment states this was deliberate). The sibling test
`test_handle_turn_history_compression_noop_when_unnecessary`
(asserting `replace_messages.assert_not_called()` when compression is a no-op) still
passes, but only trivially — `replace_messages` is now never called in either the
compression or no-compression case, so it provides no real coverage of the intended
"persist only when compression actually happened" behavior.

## Reason for Change
Without this call, a session's persisted message history diverges from what the agent
actually operates on in memory after compression. Concretely: ephemeral system messages
that compression is meant to strip before persistence are never actually stripped from
the session store, so they get reloaded on a future session restore — defeating the
original, documented purpose of the call this refactor dropped. This is a data-integrity
regression in session persistence, not merely a missing test.

## Implementation Intent
Restore the `ctx.session.replace_messages(ctx.conv.history)` call (or an equivalent
persistence call through whatever the current session-store interface is) inside
`ConversationStateManager.handle_history_compression()`, gated on compression actually
having occurred (matching the original design: only persist when compression ran, not
on every turn). Confirm the exact original condition (e.g. whether `hist_mgr.compress()`
returns a result indicating whether compression happened, via the discarded `_result`
value) before restoring the call, rather than calling `replace_messages` unconditionally.

## Target Files or Areas
- `scripts/agent/conversation_state_manager.py` (`ConversationStateManager.handle_history_compression()`)
- `scripts/agent/orchestrator.py` (reference only — confirms `_handle_history_compression()`
  is a pure delegation to `ConversationStateManager`; not itself a target unless the
  delegation signature needs to change to expose the compression-occurred result)
- `tests/integration/test_orchestrator_integration.py`
  (`TestCompleteTurnExecution::test_handle_turn_history_compression_persists_when_needed`,
  `::test_handle_turn_history_compression_noop_when_unnecessary`) — reference; both
  already assert the correct intended behavior, no test change expected unless the fix
  changes the exact call signature they assert against

## Required Changes
- Add the dropped `ctx.session.replace_messages(...)` call (or current equivalent) to
  `ConversationStateManager.handle_history_compression()`, conditioned on compression
  having actually occurred.
- Confirm `hist_mgr.compress()`'s return value (the currently-discarded `_result`) can
  supply this condition; if not, determine the correct signal from `RagIngester`/history
  manager's own contract before implementing.

## Constraints
Do not change `hist_mgr.compress()`'s own compression algorithm or the ephemeral
system-message-stripping logic itself — this issue is scoped to restoring the
persistence call, not re-designing compression.

## Acceptance Criteria
- [ ] `uv run pytest tests/integration/test_orchestrator_integration.py::TestCompleteTurnExecution::test_handle_turn_history_compression_persists_when_needed -q` passes
- [ ] `uv run pytest tests/integration/test_orchestrator_integration.py::TestCompleteTurnExecution::test_handle_turn_history_compression_noop_when_unnecessary -q` continues to pass, now with real (not trivial) coverage — verify by temporarily reverting the fix and confirming this test would fail without it, then re-applying
- [ ] `ctx.session.replace_messages(...)` (or current equivalent) is called exactly when
  compression actually occurred, not on every turn

## Testing Expectations
- `uv run pytest tests/integration/test_orchestrator_integration.py -q` — both
  `TestCompleteTurnExecution` history-compression tests must pass meaningfully (not
  just by coincidence)
- `uv run pytest tests/agent/test_orchestrator.py -q` — confirm no regression in any
  passing history-compression-adjacent test in this file

## Documentation Impact
N/A: internal correctness fix restoring already-documented (via git history) intended
behavior; no `docs/*.md` currently describes this persistence step per
`docs/00_index.md`'s task-scope mapping (unconfirmed — check before closing, add a note
if a matching Agent-area doc exists and omits this behavior).

## Out of Scope
- Any other `test_orchestrator_integration.py`/`test_orchestrator.py` failure — all
  other failures in these two files are tracked by `orch002`.
- Redesigning the history-compression algorithm itself.

## Dependencies
N/A: none. Discovered while investigating `orch002`'s scope
(`issues/20260909-105759_orch002_llm-turn-executor-attribute-rename-not-propagated-to-tests.md`)
— independent of that issue's rename fix.

## Unresolved Questions
Exact mechanism to determine "compression actually occurred" for the persistence
condition — whether `hist_mgr.compress()`'s discarded `_result` already carries this, or
whether a different signal (e.g. comparing before/after history length) is more
appropriate. Resolve empirically during implementation by reading `hist_mgr.compress()`'s
actual return type.

## AI Implementation Instruction
Restore the dropped persistence call with the correct occurred-vs-no-op condition; do
not call `replace_messages` unconditionally on every turn, since that would fail the
no-op test's intent even if its current assertion happens to still pass. Do not modify
`hist_mgr.compress()`'s own compression logic.
