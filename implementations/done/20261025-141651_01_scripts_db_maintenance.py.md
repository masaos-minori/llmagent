# Implementation Procedure — scripts/db/maintenance.py

## Goal

Add an optional active-session guard to the retention purge: both delete rules
(`_delete_sessions_by_age` 167-182, `_delete_sessions_beyond_limit` 185-202) exempt a
passed `keep_session_id (new)`, and `purge_old_sessions` (205-238) surfaces the
exemption as a new additive `data` key `kept_active_session (new)` (REQ-001, REQ-002,
REQ-003, REQ-006).

## Scope

- Modify only `scripts/db/maintenance.py`: the two private delete helpers and
  `purge_old_sessions`.
- No signature change for existing positional callers: the guard is a keyword-only
  parameter with default `None` (REQ-001 contract).
- No REPL/agent state read inside `scripts/db/` (issue AI-instruction): the guard
  arrives only as a parameter.

## Assumptions

- The private helpers have no direct tests and no external callers (grep verified
  2026-10-25: they are referenced only inside `purge_old_sessions`), so changing their
  return type from `int` to `tuple[int, bool]` is safe.
- No existing test asserts the whole `data` dict by equality (grep of
  `result.data ==` in `tests/db/test_db_maintenance.py` is empty), so adding a `data`
  key is non-breaking.
- "Exempted" means the guarded session was a delete candidate under at least one rule
  and survived; a fresh active session that was never at risk reports `None`.

## Design decisions

- Keyword-only parameter (`*, keep_session_id: int | None = None`) on
  `purge_old_sessions` — positional contract of the exported function stays identical
  for `scripts/db/__init__.py` re-export consumers (23, 92).
- Helpers return `(deleted_count, exempted)` so `purge_old_sessions` can set
  `kept_active_session (new)` only when a rule actually spared the guard (plan Design
  "keep_session_id if exempted else None").
- Age rule stays a single SQL DELETE with an added `AND session_id != ?` clause
  (still parameterized); candidacy is probed with one parameterized SELECT before the
  DELETE.
- Count rule filters the Python candidate list `rows[max_sessions:]` by
  `sid != keep_session_id`; the exempted session does not consume a keep slot (plan
  Assumption 2).
- The `except` path's `extra_data` gains the same key for result-shape consistency.

## Alternatives considered

- Compute exemption as "row still present after purge": rejected — reports fresh
  never-at-risk sessions as kept and doubles post-delete queries.
- Bump the effective `max_sessions` by one when guarding: rejected by plan Assumption
  2; docs state the "may exceed by one" semantics instead.

## Implementation
### Target file
`scripts/db/maintenance.py`

### Procedure

1. `_delete_sessions_by_age (167)`: signature becomes
   `(db: SQLiteHelper, max_age_days: int, keep_session_id: int | None = None) -> tuple[int, bool]`.

   ```python
   if max_age_days <= 0:
       return 0, False
   if keep_session_id is None:
       cur = db.execute(  # existing SQL verbatim (AC-004)
           "DELETE FROM sessions WHERE created_at < datetime('now', ?)",
           (f"-{max_age_days} days",),
       )
       deleted = cur.rowcount
       ...existing logger.info unchanged...
       return deleted, False
   expired = db.fetchall(
       "SELECT 1 FROM sessions WHERE session_id = ? AND created_at < datetime('now', ?)",
       (keep_session_id, f"-{max_age_days} days"),
   )
   cur = db.execute(
       "DELETE FROM sessions WHERE created_at < datetime('now', ?) AND session_id != ?",
       (f"-{max_age_days} days", keep_session_id),
   )
   deleted = cur.rowcount
   ...existing logger.info unchanged...
   return deleted, bool(expired)
   ```

2. `_delete_sessions_beyond_limit (185)`: signature becomes
   `(db: SQLiteHelper, max_sessions: int, keep_session_id: int | None = None) -> tuple[int, bool]`.

   ```python
   rows = db.fetchall("SELECT session_id FROM sessions ORDER BY created_at DESC")
   if len(rows) <= max_sessions:
       return 0, False
   candidates = [row[0] for row in rows[max_sessions:]]
   if keep_session_id is None:
       exempted = False
       to_delete = candidates
   else:
       exempted = keep_session_id in candidates
       to_delete = [sid for sid in candidates if sid != keep_session_id]
   if not to_delete:
       return 0, exempted  # guard emptied the list; IN () must not be built
   placeholders = ",".join("?" * len(to_delete))
   cur = db.execute(
       f"DELETE FROM sessions WHERE session_id IN ({placeholders})",  # nosec B608 justification unchanged
       tuple(to_delete),
   )
   ...existing logger.info unchanged...
   return cur.rowcount, exempted
   ```

3. `purge_old_sessions (205)`: append `*, keep_session_id: int | None = None` to the
   signature; unpack the helper tuples; set
   `kept = keep_session_id if (age_exempted or count_exempted) else None`; add
   `"kept_active_session": kept` to the success `data` dict (230) and to the except
   path's `extra_data` (237). When `kept` is not None, log
   `"Retention: kept active session %s beyond retention"` (logger.info, new line).

### Method
No new symbols; changed signatures/returns of the two private helpers and
`purge_old_sessions`. New parameter names `keep_session_id (new)`, new `data` key
`kept_active_session (new)`. Docstring of `purge_old_sessions` gains one sentence:
the active-session guard and its additive result key.

### Details
- The unguarded branches keep the current SQL byte-for-byte (AC-004).
- `IN ()` syntax error when the guard empties `to_delete` is prevented by the
  explicit early return in step 2.
- `logger.info` texts of both rules stay unchanged so existing log-based expectations
  hold.
- Existing `# nosec B608` comment stays on the placeholder-built DELETE; no new
  suppression.

## Compatibility considerations

- `scripts/db/__init__.py` re-export (23, 92) and all non-agent callers keep working
  via the default `None` (REQ-001).
- Existing `MaintenanceResult.data` keys `age_deleted`/`count_deleted` unchanged;
  `DbMaintenanceService.purge` sums them exactly as today
  (`db_maintenance_service.py:73`).
- STRICT/BEST_EFFORT semantics and checkpoint/vacuum/recover paths untouched.

## Security considerations

- All guard queries are parameterized; the only f-string SQL remains the placeholder
  list (`"?" * n`), unchanged.

## Rollback considerations

`git checkout -- scripts/db/maintenance.py`; no schema, config, or data migration is
involved.

## Validation plan

- Red-first: `uv run pytest tests/db/test_db_maintenance.py -x -q` shows the four new
  guard tests failing before this procedure, passing after (procedure
  `20261025-141651_05_tests_db_test_db_maintenance.py.md`).
- `uv run pytest tests/db/test_db_maintenance.py tests/agent/commands/test_agent_cmd_session.py -x -q`.
- ruff + mypy on this file; bandit: existing B608 justification unchanged.

## Completion criteria

- AC-001, AC-002: new guard tests green; `data["kept_active_session"]` reports the
  exempted id.
- AC-004: every existing purge/maintenance test passes unmodified.

## Out of Scope

- Service/command layer forwarding (procedures 02, 04).
- Retention ordering change and config keys (issue out-of-scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the four red guard tests first (procedure 05) | Completed | 2026-10-25 | 2026-10-25 | red recorded: 4 new failed, 51 pre-existing passed |
| 2 | Apply steps 1-3 to maintenance.py | Completed | 2026-10-25 | 2026-10-25 | helpers return `tuple[int, bool]`; keyword-only `keep_session_id` on `purge_old_sessions` |
| 3 | Run targeted validation | Completed | 2026-10-25 | 2026-10-25 | 55 passed; ruff/mypy clean; bandit nosec justification unchanged |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002, REQ-003 (db layer), REQ-006
- **Source issue**: `issues/20261025-115826_sess005_purge-deletes-current-session.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-124106_sess005_purge-deletes-current-session.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-141651
- **Related target files**: tests/db/test_db_maintenance.py (procedure 05)
