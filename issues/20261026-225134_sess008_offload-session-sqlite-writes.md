# Offload turn-path session SQLite writes from the REPL event loop

## Priority
Medium

## Summary
Turn-path session persistence (`save`, `save_assistant_message`, `complete_round`)
runs synchronous SQLite calls directly inside async code, so lock contention can
block the whole event loop for up to the 30-second `busy_timeout`. Run these writes
off the loop the way the command paths already do.

## Background
From a python-code-review pass over the REPL turn path (finding F-010). Evidence
(Explicit in code for the call shape; stall impact strongly implied):
- `scripts/db/` helper layer sets `PRAGMA busy_timeout=30000`.
- `scripts/agent/session.py` persistence methods are synchronous sqlite calls
  invoked directly from `async` turn code in `scripts/agent/orchestrator.py`.
- Command paths already offload the same kind of work via `asyncio.to_thread`
  (`scripts/agent/commands/cmd_session.py` dispatch table), showing the established
  pattern in this repo.

## Problem
When another writer (maintenance command, background task) holds the session DB
lock, a mid-turn save blocks the single event loop for up to 30s: signal handling,
shutdown coordination, and background-task callbacks stall.

## Reason for Change
Shutdown/signal responsiveness is part of the REPL's reliability contract; a hidden
30s synchronous wait inside the turn path undermines it under contention.

## Implementation Intent
Wrap the turn-path session persistence calls with the existing offload pattern
(`asyncio.to_thread`), or make the persistence methods async at the session
boundary. Prefer the existing pattern over a new abstraction. Ordering guarantee to
preserve: each write completes before the step that depends on it (the turn flow is
sequential today).

## Target Files or Areas
- `scripts/agent/orchestrator.py` (persistence call sites)
- `scripts/agent/session.py` (sync methods being offloaded)
- `scripts/db/` helper layer (connection-per-call behavior under threads)

## Required Changes
- Offload turn-path persistence calls off the event loop.
- Confirm the DB helper opens per-call connections safely from worker threads
  (check `check_same_thread` handling).
- Add a test that a contended write does not block the loop beyond a bounded time.

## Constraints
- SQLite connections are not shareable across threads by default — offloading must
  use a per-call connection (the helper layer's existing open-per-call pattern) or
  an explicitly thread-safe setup.
- Preserve strict write ordering within a turn.
- Coordinate with the atomic-persistence issue so the transaction work and this
  offload do not implement two different persistence wrappers.

## Acceptance Criteria
- No direct synchronous session-write call remains in the async turn path (review +
  grep).
- A contention test shows signal/shutdown handling proceeds while a write waits.
- Full turn/session tests pass unchanged.

## Testing Expectations
- Integration test: hold a second write lock, run a turn, assert the event loop
  stays responsive (e.g. a timer task fires during the wait).
- Thread-safety test for the DB helper under `asyncio.to_thread`.

## Documentation Impact
Record the threading boundary of the persistence layer (which calls run on worker
threads, connection-per-call rule) in the DB/env docs (boundaries, operational
note).

## Out of Scope
- WAL mode changes or `busy_timeout` value changes.
- Command-path dispatch (already offloaded).

## Dependencies
- `issues/20261026-224643_turn001_atomic-turn-persistence.md` — depends on: sequence
  after turn001 so both changes share one persistence call boundary.

## Unresolved Questions
- Whether the DB helper's per-call connection opening is safe from worker threads
  (`check_same_thread` and `sqlite-vec` extension loading per connection) — confirm
  before choosing `asyncio.to_thread` vs. an async session API.

## AI Implementation Instruction
Reuse the repo's existing `asyncio.to_thread` pattern; do not introduce an
executor/queue abstraction. Verify thread safety of the DB helper first (it is an
open question above — resolve it with a probe test before wiring the offload).
Preserve write ordering and public method signatures.

## Traceability
- **Workflow phase**: `python-code-review`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261026-225134
- **Related target files**: `scripts/agent/orchestrator.py`, `scripts/agent/session.py`, `scripts/db/`
