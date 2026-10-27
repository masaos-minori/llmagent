# Make turn persistence atomic to prevent memory/DB divergence

## Priority
High

## Summary
Group each REPL turn's SQLite writes into a single transaction and reconcile the
in-memory conversation history when persistence fails, so the memory view and the
session database never silently diverge.

## Background
From a python-code-review pass over the REPL turn-execution path (finding F-001).
Evidence (Explicit in code):
- `scripts/agent/orchestrator.py` appends to `ctx.conv.memory` before calling
  `ctx.session.save` for the user message, and appends the assistant message to
  memory before `save_assistant_message`; `persist_compression` replaces
  `conv.history` before the DB snapshot rewrite.
- `scripts/agent/session.py` writes each step (user row, assistant row, tool rows)
  as a separate `SQLiteHelper` call; no shared transaction spans a turn.
- `scripts/agent/repl_input_loop.py` catches `ConversationPersistenceError` and only
  prints a warning; the already-mutated memory history is not rolled back.

## Problem
Any DB error mid-turn (busy timeout, disk error) leaves messages in memory that
never reached SQLite. After a compression, a failed `persist_compression` leaves
memory compressed while the DB keeps the uncompressed snapshot. On restart the
conversation reverts to a state the user believed was already saved.

## Reason for Change
Data-integrity risk in the highest-traffic path of the agent runtime. The divergence
is silent: the user sees the message in the session, but it is not persisted, and no
reconciliation path exists.

## Implementation Intent
Make the persistence layer own a turn-scoped transaction boundary: the writes that
belong to one turn (user row, assistant row, tool rows; and the compression snapshot
rewrite) commit as one unit. When a turn's persistence fails, roll the in-memory
history back to the last DB-committed state (or re-read it from the DB) before the
loop continues. Keep the existing `ConversationPersistenceError` exception type and
the current public session methods; the change is about transaction scope and
failure-time reconciliation, not a new persistence framework.

## Target Files or Areas
- `scripts/agent/orchestrator.py` (turn write sequence)
- `scripts/agent/session.py` (`save`, `save_assistant_message`, `complete_round`, `persist_compression`)
- `scripts/agent/session_message_repo.py` (row writes)
- `scripts/agent/repl_input_loop.py` (`ConversationPersistenceError` handling)
- DB helper layer in `scripts/db/` (`SQLiteHelper` transaction support)

## Required Changes
- Wrap each turn's session writes in one transaction (or an equivalent commit group).
- On persistence failure, restore memory state to the DB-committed state before the
  next prompt.
- Apply the same rule to `persist_compression`: do not adopt the compressed history
  in memory until the snapshot rewrite has committed.
- Add regression tests that fail persistence at each step of a turn.

## Constraints
- SQLite single-writer model: the transaction must not extend across the LLM call
  (no long-held write transaction while waiting on the backend).
- Preserve `ConversationPersistenceError` semantics and existing public method
  signatures.
- No performance regression in the normal (non-failing) turn path.

## Acceptance Criteria
- A forced DB failure at each turn step (user save, assistant save, round completion,
  compression persist) leaves in-memory history equal to DB state.
- Existing session/turn tests pass unchanged.
- `mypy`, `ruff`, and import-contract checks pass.

## Testing Expectations
- Characterization/unit tests injecting a failing `SQLiteHelper` write at each turn
  step, asserting memory equals DB after the failure.
- Integration test with a locked DB (second writer) to exercise busy_timeout failure.
- Regression test for `persist_compression` failure keeping memory uncompressed.

## Documentation Impact
Update the agent docs describing turn persistence to state the failure behavior:
what is committed, what is rolled back, and what the user sees on a persistence
error (failure behavior + operational note).

## Out of Scope
- Repairing history that was already persisted malformed by a hard crash (filed
  separately: orphaned tool_calls repair).
- Cancel-during-turn semantics (trailing user row is acceptable for chat APIs).
- Any change to the backend request path.

## Dependencies
- `issues/20261026-224729_turn002_repair-orphan-tool-call-rows.md` — blocks: the
  orphan-repair fix should be built on top of the atomic persistence boundary.

## Unresolved Questions
- Which layer should own the turn transaction (session methods vs. an orchestrator
 -level commit group) — a design decision for the plan stage.

## AI Implementation Instruction
Keep changes minimal and inside the existing session/message-repo boundaries; do not
introduce a new persistence framework or ORM. Do not hold a write transaction open
across LLM/backend calls. Preserve all public method signatures and the
`ConversationPersistenceError` contract. Add tests first (characterization of current
divergent behavior), then fix. Report, do not fix, any larger coupling you find in
`repl_input_loop.py`.

## Traceability
- **Workflow phase**: `python-code-review`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261026-224643
- **Related target files**: `scripts/agent/orchestrator.py`, `scripts/agent/session.py`, `scripts/agent/session_message_repo.py`, `scripts/agent/repl_input_loop.py`, `scripts/db/`
