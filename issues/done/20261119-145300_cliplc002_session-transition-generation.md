# Make session transitions, clear, undo, title tasks, and persistence generation-safe

## Priority
High

## Summary
Introduce session generations and one atomic `SessionTransitionService` for `/clear new`, `/session load`, title generation, background tasks, undo recovery, and shutdown persistence, so a transition either commits completely or leaves the old session intact.

## Background
Source: consolidated CLI REPL and MCP lifecycle backlog (`memo-issue.md`, Issue 2). Related archived work: `issues/done/20261031-180437_restoresummary001_session-load-drops-summary.md`, `issues/done/20261014-154803_undo001_undo-compression-boundary.md`, `issues/done/20261026-225036_bgmonitor001_reset-background-failure-pause.md`.

Evidence (`Explicit in code`, by listing and `rg`): `scripts/agent/session_title.py` named by the backlog does not exist; title code lives in `scripts/agent/commands/session_title.py`; `scripts/agent/services/session_restore.py` has `restore_session(ctx, session_id)`. All behavior claims below (sequential replacement without rollback, title written to the current session, shutdown reading state at different times, `/clear` leaving persisted rows, undo reload failure) are from the backlog and `Needs confirmation`.

## Problem
Session identity and state can drift: a new session may start without finalizing the old one; a load may replace history, undo floor, id, correlation, and statistics sequentially without rollback; title and background results may be applied to whichever session is current; shutdown persistence reads fields at different times; `/clear` may leave persisted messages so cleared history returns after reload; `/undo` may leave runtime history inconsistent after a failed reload.

## Reason for Change
Data-integrity risk across session boundaries; maintenance jobs, shutdown, and turn persistence need stable session ownership.

## Implementation Intent
A monotonically increasing session generation, one transition service with snapshot, temporary build, atomic commit, and rollback, and an immutable persistence snapshot used by shutdown and pre-transition finalization. `/clear` and `/undo` get explicit durable semantics.

## Target Files or Areas
- `scripts/agent/services/session_restore.py`, `conversation_service.py`, `undo_service.py`
- `scripts/agent/session_persister.py`, `session.py`, `bg_task_monitor.py`, `commands/session_title.py`, `commands/cmd_session.py`
- New transition service under `scripts/agent/services/` and tests under `tests/agent/` (the backlog's `ConversationStateManager`, `on_first_turn` wiring, and title-task creation point are `不明` until located)

## Required Changes
- Add a session generation; add `SessionTransitionService` for `/clear new` and `/session load`; require an idle turn; snapshot session id, generation, history, undo floor, correlation, statistics; finalize old-session Memory and diagnostics before switching; build restored state in a temporary structure; commit all fields together; roll back on failure.
- Capture session id and generation for title and other session-specific tasks; save titles to an explicit target session; reject stale-generation results; store `title_pending` per target session; register task type, instance id, session id, and generation with `BgTaskMonitor` and group failures by type; remove title text and raw failure reasons from logs and audit.
- Add an immutable `SessionPersistenceSnapshot` (session id, generation, defensive-copy history, turn id, statistics) for shutdown and pre-transition finalization; reject persistence when the generation changed.
- Decide whether `/clear` is persistent deletion or a temporary view reset (rename command and docs if temporary); route `/clear new` through the service; say "in-memory conversation history"; keep pre-delete state so `/undo` can recover; verify long-term Memory tables and JSONL stay unchanged.
- Report fetched, synthesized, dropped, and restored message counts separately; separate title storage and display limits.

## Constraints
- Long-term Memory must not change through undo.
- A `/clear` semantics change is user-visible and must be documented.

## Acceptance Criteria
- [ ] A failed `/session load` leaves the previous session unchanged; `/clear new` finalizes the old session.
- [ ] Old-generation title or background results cannot mutate the new session.
- [ ] Shutdown diagnostics and Memory persistence use one snapshot.
- [ ] `/clear` behavior matches persistence and documentation; `/undo` cannot leave DB and in-memory history silently divergent.

## Testing Expectations
- Load failure at every transition step; title completion during clear and load; shutdown racing a transition.
- Clear followed by reload; undo reload failure after DB deletion; title and monitor generation tests.
- Run ruff, mypy, and the full test suite.

## Documentation Impact
Yes. Session transition and generation semantics; `/clear` and `/undo` persistence behavior; remove ambiguous uses of "memory".

## Out of Scope
- Maintenance jobs (`issues/20261119-145301_cliplc003_maintenance-job-framework.md`); shutdown state machine (`issues/20261119-145302_cliplc004_bounded-shutdown-machine.md`); strict turn persistence (`issues/20261119-145308_cliplc010_strict-turn-persistence.md`).

## Dependencies
- Depends on `issues/20261119-145259_cliplc001_repl-input-controller.md` (confirmation and cancellation use the corrected input model). Blocks `issues/20261119-145301_cliplc003_maintenance-job-framework.md`, `issues/20261119-145302_cliplc004_bounded-shutdown-machine.md`, and `issues/20261119-145308_cliplc010_strict-turn-persistence.md`.

## Unresolved Questions
- `不明`: whether `/clear` should delete persisted messages or only reset the view (owner decision).
- `不明`: where session-title tasks are created and registered.

## AI Implementation Instruction
Locate the title-task creation point and the `/clear` persistence behavior first and confirm the reported defects with tests before changing code. Keep the change within session lifecycle code. Stop and report the `/clear` decision instead of choosing silently.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-145300
- **Related target files**: `scripts/agent/services/session_restore.py`, `scripts/agent/services/conversation_service.py`, `scripts/agent/services/undo_service.py`, `scripts/agent/session_persister.py`, `scripts/agent/session.py`, `scripts/agent/bg_task_monitor.py`, `scripts/agent/commands/session_title.py`, `scripts/agent/commands/cmd_session.py`
