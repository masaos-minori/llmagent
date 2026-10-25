# Fix stale message repository binding after session restore

## Priority
High

## Summary
After `/session load <id>` restores a previous session, `AgentSession` keeps writing
new messages under the OLD session row because its cached `SessionMessageRepository`
was constructed with the pre-restore `session_id`. Fix the binding so that after a
restore, all subsequent saves go to the restored session, and add a regression test
that runs against a real DB.

## Background
`AgentSession` caches its message repository in a lazily-built property
(`scripts/agent/session.py` `_message_repo`, lines 33-45). `SessionMessageRepository`
binds `session_id` at construction time and uses it on every `save` / `save_many`
call. `AgentSession.start()` rebinds the repo after creating a new session row
(`scripts/agent/session.py` lines 151-153), but `restore_session()` only assigns
`ctx.session.session_id = session_id` (`scripts/agent/services/session_restore.py`
line 97) and never rebinds the cached repo. The `_message_repo` setter exists but is
used only by `start()`.

Confirmed by reproduction (Evidence: confirmed, Confidence: High): a real-DB test
(`PYTHONPATH=scripts uv run pytest /tmp/opencode/test_repo_staleness.py -q -s`)
restores session 100 into a live session and then saves a turn; the DB shows
`{100: [], 101: ['in original session', 'turn in restored session']}` — the restored
session's rows are empty and the new turn was written under the pre-restore session
row 101. Existing tests in `tests/agent/test_session_restore.py` mock `ctx.session`
and cannot see this.

## Problem
Every turn after `/session load` is persisted under the wrong `session_id`:

- The restored session row receives no new messages.
- The old (usually pre-restore temporary) session row accumulates the restored
  conversation's ongoing turns, mixing unrelated histories.
- Re-exporting or re-restoring either session produces corrupted or duplicated
  conversation data.

## Reason for Change
This is a silent data-integrity defect hit by the normal `/session load` workflow.
It is invisible to the current test suite (all 194 session tests pass) because the
restore tests mock the session object. The longer it stays unfixed, the more real
user sessions accumulate misfiled messages that are hard to repair after the fact.

## Implementation Intent
Make the repository binding follow the active `session_id` after a restore. At the
responsibility level: the component that switches the active session id (the restore
flow) must also make the persistence layer bind to the new id — either the session
facade invalidates/rebuilds its cached repo when `session_id` changes, or the
repository stops caching an id-bound instance altogether. Preserve the existing
`start()` behavior (new session row + repo bind) and the restore semantics
(`session_restore.py` comment: history/stats preserved exactly).

## Target Files or Areas
- scripts/agent/session.py
- scripts/agent/services/session_restore.py
- tests/agent/test_session_restore.py (new real-DB regression test)

## Required Changes
- Rebind or invalidate the cached `SessionMessageRepository` when `restore_session`
  switches `ctx.session.session_id`.
- Add a regression test using a real temp DB (not mocks): start session A, save a
  message, restore session B, save a message, assert each row contains only its own
  messages.
- Verify the stats counters (`skipped_no_session_count`, `skipped_invalid_role`)
  still refer to the live repo after the fix.

## Constraints
- Do not change `start()` semantics: it must still create a new sessions row and
  bind the repo (existing callers depend on this).
- Keep `restore_session` non-destructive: it must not mutate DB rows of the restored
  session beyond what it already does.
- Respect the import-layer contract in `skills/DESIGN.md` Shared Vocabulary.

## Acceptance Criteria
- After `/session load` (directly `restore_session`), a subsequent
  `session.save(...)` writes under the restored `session_id` (verified by a real-DB
  test).
- The old pre-restore session row receives no new messages after the restore.
- All existing session tests still pass.
- New regression test fails before the fix and passes after it.

## Testing Expectations
- New real-DB regression test in `tests/agent/test_session_restore.py` (or a new
  test module) covering: start A → save → restore B → save → assert per-session
  message rows.
- Run the existing session test set: `test_session_restore.py`,
  `test_session_message_repo.py`, `test_agent_session.py`, `test_session_persister.py`,
  `test_session_memory_boundary.py`, `commands/test_agent_cmd_session.py`.
- `uv run ruff check` and `uv run mypy --no-namespace-packages` on the changed files.

## Documentation Impact
Documentation update required: `docs/23_agent/agent_09_01_data-layer-session-db.md`
and `docs/23_agent/agent_04_01_state-and-persistence-state-model.md` must state the
intent that the message persistence binding always tracks the active session id, and
that restore rebinds it. Describe the invariant and failure behavior only; do not
duplicate code.

## Out of Scope
- The dead `SQLITE_NOTFOUND (1017)` fallback in `AgentSession.start()` (tracked
  separately, see Dependencies).
- X-Session-Id refresh on tools after restore (tracked separately).
- Any migration/cleanup of already-corrupted historical session rows.

## Dependencies
- `issues/20261025-115550_sess002_unreachable-sqlite-error-fallback.md` — blocks
  nothing here, but both touch `scripts/agent/session.py`; land sess001 first and
  rebase sess002 onto the result.

## Unresolved Questions
- Should the fix live in the session facade (invalidate cache on id change) or in
  the repository (resolve the id per call)? Decide during planning; both satisfy the
  acceptance criteria.
- Whether `session_persister.py` writes with the same stale repo path at shutdown
  (it uses `ctx.session` saves; expected to inherit the fix, needs confirmation).

## AI Implementation Instruction
Change only the session/repo binding and its tests. Do not rewrite unrelated REPL or
command code. Keep the public `AgentSession` API unchanged. Add the regression test
first (red), then the fix (green). Stop and report if the restore semantics in
`session_restore.py` turn out to depend on the stale binding.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261025-115501
- **Related target files**: scripts/agent/session.py, scripts/agent/services/session_restore.py, tests/agent/test_session_restore.py
