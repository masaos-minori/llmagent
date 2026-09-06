## Goal
Create `scripts/db/session_consistency.py`: a new `check_session_consistency()`
function, report dataclass, and `is_consistent()` predicate mirroring
`rag_consistency.py`'s existing shape, covering the Session domain's required
logical checks (REQ-003).

## Scope
- In scope: new file `scripts/db/session_consistency.py` only, containing a
  `SessionConsistencyReport` dataclass (new — added to `scripts/db/models.py` per this
  row's Method note below, or defined in this new file if `models.py`'s own row
  (seq 02) is out of scope for it — see Design decisions), `check_session_consistency()`,
  and `is_consistent()`.
- Out of scope: `rag_consistency.py` itself (reused unmodified); wiring this new
  function into `_restore_from_backup()` (seq 01); any change to `store_impl.py`'s
  `SQLiteSessionStore` methods (read-only reference for how sessions/messages are
  normally accessed).

## Assumptions
- The write smoke test (Testing Expectations > Session: "Write smoke-test failure
  where applicable") is in scope per the Plan's Unknowns UNK-02 resolution: the
  restore is already committed to `db_path` (via `os.replace()`) before this
  function would run, so a scoped insert-then-delete smoke test does not violate
  ADR-008 INV-16 (Dry Run no-mutation guarantee, which governs Dry Run only).
- `SessionConsistencyReport` is added to `scripts/db/models.py` alongside
  `RecoveryResult`'s new field (seq 02) — both are additive dataclass changes to the
  same file's existing pattern (`RagConsistencyReport` already lives there); if seq 02
  is implemented first without this addition, add `SessionConsistencyReport` to
  `models.py` as part of this row instead, noting the cross-file dependency in that
  row's own Execution Status.

## Design decisions
- Mirror `rag_consistency.py`'s three-part shape exactly: a frozen report dataclass
  (counts + affected-identifier tuples, `None` when not applicable), a
  `check_session_consistency(db: SQLiteHelper) -> SessionConsistencyReport` collector
  function using try/except-per-check-group (matching `check_rag_consistency()`'s
  `diagnostic_errors` accumulation pattern so one failing check group does not abort
  the others), and `is_consistent(report) -> bool`.
- Place `SessionConsistencyReport` in `scripts/db/models.py` (alongside
  `RagConsistencyReport`), not in this new file — matches the existing precedent
  exactly (`rag_consistency.py` imports its report type from `db.models`, does not
  define it locally).
- Do not invent additional Session invariants beyond the Issue's own list (required
  tables exist; sessions readable; message→session referential validity;
  memory/memory-link validity per the schema's declared FK constraints; session
  diagnostics readable; read smoke test; write smoke test) — confirmed via direct read
  of `_SESSION_SCHEMA_TEMPLATE` (`scripts/db/schema_sql.py:93-152`) that these checks
  correspond exactly to: `sessions`/`messages`/`memories`/`memories_fts`/
  `memory_links`/`session_diagnostics`/`memories_vec` existing; `messages.session_id`
  orphans (no matching `sessions.session_id`); `memory_links.src_id`/`dst_id` orphans
  (no matching `memories.memory_id`); `session_diagnostics` readable via its
  `session_id` FK.

## Alternatives considered
- Add Session consistency checks as new methods on `SQLiteSessionStore`
  (`scripts/db/store_impl.py`): rejected — Plan's own Assumptions section rejects this
  for structural symmetry with the RAG precedent (`rag_consistency.py` is a standalone
  module, not methods on the RAG store class); this row follows that decision.
- Generalize `check_rag_consistency()` to accept a `target` parameter and branch
  internally for Session: rejected — confirmed via direct read that
  `check_rag_consistency()` operates on RAG-specific tables
  (`chunks`/`chunks_fts`/`chunks_vec`/`documents`) with no structural overlap with the
  Session schema; a shared function would need two entirely separate query sets
  behind one name, adding indirection without reducing duplication.

## Implementation
### Target file
`scripts/db/session_consistency.py`

### Procedure
1. Add `SessionConsistencyReport` to `scripts/db/models.py` (or confirm seq 02 already
   added it), with fields: `sessions: int`, `messages: int`, `memories: int`,
   `orphaned_message_count: int`, `orphaned_memory_link_count: int`,
   `session_diagnostics_readable: bool`, `read_smoke_test_ok: bool`,
   `write_smoke_test_ok: bool | None` (`None` when not run/not applicable),
   `affected_orphaned_message_ids: tuple[int, ...] | None = None`,
   `affected_orphaned_memory_link_pairs: tuple[tuple[str, str], ...] | None = None`,
   `diagnostic_errors: tuple[str, ...] | None = None` — mirroring
   `RagConsistencyReport`'s "counts + affected identifiers + diagnostic_errors" shape.
2. Implement `check_session_consistency(db: SQLiteHelper) -> SessionConsistencyReport`:
   - Required tables: query `sqlite_master` for `sessions`, `messages`, `memories`,
     `memories_fts`, `memory_links`, `session_diagnostics`, `memories_vec`; missing any
     is a `diagnostic_errors` entry.
   - Sessions readable: `SELECT COUNT(*) FROM sessions`.
   - Message→session referential validity: `SELECT COUNT(*) FROM messages WHERE
     session_id NOT IN (SELECT session_id FROM sessions)` (orphan count), plus up to
     10 affected `message_id`s.
   - Memory/memory-link validity: `SELECT COUNT(*) FROM memory_links WHERE src_id NOT
     IN (SELECT memory_id FROM memories) OR dst_id NOT IN (SELECT memory_id FROM
     memories)` (orphan count), plus up to 10 affected `(src_id, dst_id)` pairs.
   - Session diagnostics readable: `SELECT COUNT(*) FROM session_diagnostics` (no
     error raised).
   - Read smoke test: one read query against each required table succeeds without
     raising.
   - Write smoke test: `INSERT` a throwaway row (e.g. into `session_diagnostics`,
     the lowest-risk table with no unique-constraint collision risk) then `DELETE` it
     within the same check, asserting the table's row count is unchanged before/after.
   - Wrap each check group in its own `try/except sqlite3.Error`, appending to
     `diagnostic_errors` on failure, matching `check_rag_consistency()`'s
     per-group isolation.
3. Implement `is_consistent(report: SessionConsistencyReport) -> bool`: `True` only
   when `orphaned_message_count == 0 and orphaned_memory_link_count == 0 and
   session_diagnostics_readable and read_smoke_test_ok and (write_smoke_test_ok is not
   False) and not diagnostic_errors`.

### Method
Confirmed this cycle (2026-09-06) via direct read of
`scripts/db/schema_sql.py:93-152` (`_SESSION_SCHEMA_TEMPLATE`): tables `sessions`,
`messages` (FK `session_id → sessions.session_id ON DELETE CASCADE`), `memories`,
`memories_fts` (FTS5 virtual), `memory_links` (FK `src_id`/`dst_id → memories.memory_id
ON DELETE CASCADE`), `session_diagnostics` (FK `session_id → sessions.session_id ON
DELETE CASCADE`), `memories_vec` (vec0 virtual). Confirmed via direct read of
`scripts/db/rag_consistency.py` (full file, 403 lines) that its three-part
shape (report dataclass in `db.models`, collector function with per-group
`try/except sqlite3.Error`, `is_consistent()` predicate) is the structural precedent
this row mirrors.

### Details
`ON DELETE CASCADE` on both FK relationships means orphans should not occur under
normal SQLite operation with foreign keys enabled — this check exists specifically to
catch the post-restore case where a backup was taken with foreign keys disabled, WAL
checkpointing interrupted mid-write, or the backup itself predates a schema migration,
none of which `PRAGMA integrity_check` (physical) detects.

## Compatibility considerations
New file, new dataclass — no existing caller affected. `SQLiteHelper.execute()`
(Reference Files, `scripts/db/helper.py:288`) is reused with its existing signature,
matching how `check_rag_consistency()` already consumes it.

## Security considerations
`diagnostic_errors` and any affected-identifier tuple must carry only IDs/counts —
`messages.content`/`memories.content` (row content) must never appear in a report
field or log line (REQ-010/AC-7). The write smoke test's throwaway row must use
placeholder content, never real user data.

## Rollback considerations
New file — revert via `git rm scripts/db/session_consistency.py` (and the
corresponding `SessionConsistencyReport` addition to `models.py`) if
`tests/db/test_session_consistency.py` (seq 09) or the integration tests (seq 10)
find the report shape needs a different structure than this row implements.

## Validation plan
- `uv run pytest tests/db/test_session_consistency.py -v` (seq 09, new unit tests).
- `uv run pytest tests/integration/test_session_recovery.py -v` (seq 10, exercises
  this function via `_restore_from_backup()`).
- `uv run mypy scripts/db/session_consistency.py scripts/db/models.py`.
- `PYTHONPATH=scripts uv run lint-imports` — confirm the new module respects the same
  layer as `rag_consistency.py` (both import only from `db.helper`/`db.models`).

## Completion criteria
- `scripts/db/session_consistency.py` exists with `check_session_consistency()` and
  `is_consistent()`.
- `SessionConsistencyReport` exists in `scripts/db/models.py` with the fields listed
  in Procedure step 1.
- Every check the Issue's Testing Expectations > Session lists is covered.

## Out of scope
- Wiring this function into `_restore_from_backup()` — tracked in seq 01.
- `rag_consistency.py` — reused unmodified, not touched by this row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20260903-110305_h0707_add-rag-session-recovery-verification.md
- **Source plan**: plans/20260905-163508_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-144010
- **Related target files**: scripts/db/session_consistency.py
