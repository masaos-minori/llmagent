# Repair orphaned assistant tool_calls rows on session history load

## Priority
High

## Summary
When the REPL is hard-killed mid tool-round, the session database keeps an assistant
row with `tool_calls` but no matching tool-result rows. Detect and repair such
unpaired rows when history is loaded, so resumed sessions send a well-formed
message sequence to the backend.

## Background
From a python-code-review pass over the REPL turn-execution path (finding F-002).
Evidence (Explicit in code):
- `scripts/agent/session.py` persists the assistant row (`save_assistant_message`)
  before tool results are written by `complete_round`.
- `scripts/agent/tool_runner.py` writes synthetic tool rows only for in-process
  `BaseException`; SIGKILL or power loss between the two persistence steps leaves
  the assistant row with no tool rows.
- `scripts/agent/session_message_repo.py` `fetch_messages` filters orphaned
  tool-result rows but applies no repair to assistant rows whose `tool_calls` have
  no matching tool rows.
- `scripts/agent/tool_round_completion.py` already has synthetic-completion
  semantics (`SyntheticToolCallCompletion`) that a load-time repair can mirror.

## Problem
After a hard crash mid tool-round, `/session load` (or startup resume) replays a
history where an assistant `tool_calls` row is not followed by `tool` rows. The
backend's handling of that sequence is undefined (see Unresolved Questions); worst
case the session becomes permanently unloadable.

## Reason for Change
Crash-resume is a core reliability path. The malformed state is already in the DB;
without a load-time repair the damage is permanent for that session, and every
resume attempt can fail.

## Implementation Intent
Add a repair step in the history-load boundary (`fetch_messages` or the restore
service that consumes it): for each assistant row carrying `tool_calls`, verify a
tool row exists for every `tool_call_id`; for missing ones, synthesize an
"interrupted" tool result (same semantics as the existing synthetic round
completion) or strip the dangling `tool_calls`. The repair must be deterministic,
logged, and idempotent.

## Target Files or Areas
- `scripts/agent/session_message_repo.py` (`fetch_messages`)
- `scripts/agent/services/session_restore.py` (restore path consumer)
- `scripts/agent/tool_round_completion.py` (existing synthetic-completion semantics to reuse)

## Required Changes
- Detect assistant rows with `tool_calls` lacking paired tool rows at load time.
- Synthesize interrupted tool-result rows (preferred) or strip dangling `tool_calls`.
- Log the repair (warning with session id and row count).
- Add regression tests for the orphaned-row state.

## Constraints
- Repair must not rewrite DB rows destructively without logging; a synthesized row
  should carry an identifiable marker consistent with existing synthetic rows.
- Keep the repair at the read/load boundary; do not change the turn write path
  (covered by the atomic-persistence issue).
- Idempotent: running the repair twice must not double-insert rows.

## Acceptance Criteria
- A test DB containing an assistant row with `tool_calls` and zero tool rows yields
  a paired history after load.
- `/session load` of such a session succeeds and the follow-up backend request
  contains paired tool calls.
- Existing fetch/restore tests pass unchanged; `mypy`/`ruff` pass.

## Testing Expectations
- Regression test inserting an orphaned assistant tool_calls row → `fetch_messages`
  output is paired.
- Restore-path test (`session_restore`) end to end.
- Idempotency test (load twice).

## Documentation Impact
State the resume/repair behavior (what an interrupted tool round looks like after
resume) in the agent docs section covering session persistence and crash recovery
(failure behavior, operational note).

## Out of Scope
- Preventing the orphan state at write time (transaction work, filed separately as
  the atomic-persistence issue).
- Backend-side validation changes.

## Dependencies
- `issues/20261026-224643_turn001_atomic-turn-persistence.md` — this issue should be
  implemented after it; atomic persistence reduces new orphans, this issue repairs
  existing ones. Re-verify against current source once turn001 is resolved.

## Unresolved Questions
- Needs confirmation: how the llamacpp backend actually responds to an assistant
  `tool_calls` row with no matching tool rows (hard rejection vs. tolerated).
  Confirm by resuming a crashed session against the live backend.
- Choose between synthesizing an interrupted tool result and stripping the
  `tool_calls`; decision needed before implementation (synthesis preserves the
  model's own record of what it attempted).

## AI Implementation Instruction
Do not modify the turn write path in this issue. Keep the repair at the
load/read boundary and reuse the existing synthetic-completion semantics rather
than defining a new row shape. Log every repair. Stop and report if the backend
behavior question above materially changes the chosen strategy.

## Traceability
- **Workflow phase**: `python-code-review`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261026-224729
- **Related target files**: `scripts/agent/session_message_repo.py`, `scripts/agent/services/session_restore.py`, `scripts/agent/tool_round_completion.py`
