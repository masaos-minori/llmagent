# Guard the current session from /session purge retention deletes

## Priority
High

## Summary
`/session purge` deletes sessions by age and count without excluding the session
the REPL is actively using, so the live session row (and all its messages via
`ON DELETE CASCADE`) can be deleted mid-conversation. Add a current-session guard
to the purge path, matching the guard `/session delete` already has.

## Background
`/session delete` already refuses to delete the active session:
`scripts/agent/commands/cmd_session.py` `_session_delete` (lines 65-75) writes
"Cannot delete the current session." The purge path —
`cmd_session.py` line 229 -> `db_session_ops.purge` ->
`scripts/agent/services/db_maintenance_service.py` `purge()` ->
`scripts/db/maintenance.py` `purge_old_sessions()` (lines 205-229) — has no
equivalent guard. The asymmetry shows the risk is already understood for the
manual-delete path.

## Problem
Confirmed by code reading (Evidence: confirmed, Confidence: High):

- `_delete_sessions_by_age` (`scripts/db/maintenance.py` lines 167-182) runs
  `DELETE FROM sessions WHERE created_at < datetime('now', ?)` with
  `-max_age_days`.
- `_delete_sessions_beyond_limit` (lines 185-202) keeps only the most recent
  `max_sessions` rows ordered by `created_at DESC`.
- Both key on `created_at`, and `restore_session` preserves the original
  `created_at` of the loaded session (no `UPDATE sessions` for timestamps in
  `scripts/agent/services/session_restore.py`).
- `config/agent.toml` sets `sqlite_retention_max_age_days = 30`.

A session loaded with `/session load` from a row created more than 30 days ago is
a normal, fully active session; the next `/session purge` deletes its row, and
`messages` rows cascade away (`ON DELETE CASCADE`,
`scripts/db/schema_sql.py` `_SESSION_SCHEMA_TEMPLATE`). Subsequent saves then fail
with a foreign-key IntegrityError (`PRAGMA foreign_keys=ON` in
`scripts/db/helper.py` line 43), silently losing turns.

## Reason for Change
Data-integrity loss triggered by a documented normal workflow
(`/session load` old session + periodic `/session purge`). Recovery is not
possible after the cascade; the fix is preventive and cheap.

## Implementation Intent
Make the purge path session-aware at the boundary that already knows the active
session: the command/service layer passes the current `session_id` down (or the
deletion queries exclude it) so retention never removes the session the agent is
currently writing to. Keep retention semantics for all other sessions unchanged
(age rule, count rule, STRICT/BEST_EFFORT modes).

## Target Files or Areas
- scripts/db/maintenance.py (`purge_old_sessions`, `_delete_sessions_by_age`,
  `_delete_sessions_beyond_limit`)
- scripts/agent/services/db_maintenance_service.py
- scripts/agent/commands/db_session_ops.py / scripts/agent/commands/cmd_session.py
- scripts/agent/services/session_restore.py (validate_session_id default age, see
  Unresolved Questions)

## Required Changes
- Exclude the active session id from both retention delete rules.
- Surface the skip in the purge result (e.g. count/report note) so operators see
  it happened.
- Keep `/session delete`'s existing guard behavior unchanged.

## Constraints
- `purge_old_sessions` is also called from non-REPL contexts (service/ops layer)
  where no current session exists — the guard parameter must be optional.
- Do not change the retention config keys
  (`sqlite_retention_max_sessions`, `sqlite_retention_max_age_days`) or their
  defaults.
- Deletion queries stay parameterized.

## Acceptance Criteria
- With an active session whose `created_at` is older than the age limit (backdated
  in a real temp DB), `purge` keeps that session and its messages; all other
  expired sessions are deleted.
- The same holds for the count rule when the active session is beyond
  `max_sessions` most-recent.
- Purge result reporting is consistent with the new skip (verified by test).
- All existing purge/maintenance tests pass.

## Testing Expectations
- Real-DB regression tests in the maintenance test module: backdated active
  session + purge → survives; other expired sessions deleted; message cascade only
  for deleted sessions.
- Command-level test in `tests/agent/commands/test_agent_cmd_session.py` that
  `/session purge` does not drop the current session.
- `uv run ruff check` and `uv run mypy --no-namespace-packages` on changed files.

## Documentation Impact
Documentation update required: `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md`
(session retention behavior: the active session is exempt) and
`docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md`
(`/session purge` failure/operational note). State the guard as policy, not code.

## Out of Scope
- Changing retention ordering from `created_at` to `updated_at`/last-activity.
- Cleanup of sessions already corrupted by past purges.
- `/session delete` semantics (already guarded).

## Dependencies
- N/A: none

## Unresolved Questions
- Should a skipped active session be reported as "kept (active)" in the purge
  output? 不明 — decide output format in planning.
- `validate_session_id` in `scripts/agent/services/session_restore.py` defaults to
  a 90-day validity window while `agent.toml` purges at 30 days: restored sessions
  aged 30-90 days load fine today but are purge candidates. Whether that window
  should share one config source is a follow-up decision. 不明.

## AI Implementation Instruction
Thread an optional current-session id through the purge call chain; do not add
REPL-global state lookups inside `scripts/db/`. Keep the SQL parameterized. Add the
backdated-session regression tests first (red), then implement. Do not alter
checkpoint/vacuum/recover paths.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261025-115826
- **Related target files**: scripts/db/maintenance.py, scripts/agent/services/db_maintenance_service.py, scripts/agent/commands/db_session_ops.py, scripts/agent/commands/cmd_session.py, scripts/agent/services/session_restore.py
