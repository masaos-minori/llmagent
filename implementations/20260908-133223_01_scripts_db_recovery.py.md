## Goal

Add a domain-identity check to `_restore_from_backup()` so a structurally valid SQLite
backup belonging to the wrong persistence domain (rag/session/workflow/eventbus) is
rejected before the live database is touched (REQ-001, REQ-002, REQ-003).

## Scope

In scope: a new `_verify_domain_identity(backup, target)` helper function, and one call
site inserted between the existing integrity check and the archive/copy step inside
`_restore_from_backup()`. Out of scope: any change to `os.replace()`/the atomic-replace
mechanism itself, backup retention/rotation, and enabling recovery for
workflow/eventbus domains — none of that is touched by this change.

## Assumptions

- A lightweight, required-table-name signature check (not full logical-consistency
  verification) is sufficient to detect a cross-domain backup — consistent with the
  Plan's `UNK-01` (non-blocking): table names differ across domains, so table-only
  validation is expected to catch every cross-domain case without needing
  column-level checks.
- Required tables per domain: `rag` → `documents`, `chunks`; `session` → `sessions`.
  Confirmed via `rg -n "CREATE TABLE" scripts/db/schema_sql.py` (lines 27, 37 for rag;
  line 94 for session `sessions`, plus `messages`/`memories`/`memory_links`/
  `session_diagnostics` at lines 99/108/131/136 — a "wrong domain" is already caught by
  checking for the presence of just the primary table named above, per the Plan's
  Design decision).
- `workflow`/`eventbus` targets are out of scope per the Plan (recovery is prohibited
  for those domains already, per `test_recover_corrupt_workflow_prohibited`), so the
  required-table mapping only needs `rag` and `session` entries.

## Design decisions

- Reuse `SQLiteHelper(target, db_path=str(backup)).open()` to query `sqlite_master` —
  the exact call pattern `_run_integrity_check` already uses (`scripts/db/recovery.py:58`)
  — instead of opening a second, parallel connection mechanism. This satisfies the
  Plan's Implementation intent directly.
- Query `SELECT name FROM sqlite_master WHERE type='table'` and check that the
  domain's required table name is present in the result set; this is a read-only,
  single-query check with no side effects on `backup`.
- Insert the call immediately after the integrity-check early-return block (current
  line 204) and before `ts = format_timestamp()` (current line 206) in
  `_restore_from_backup()` — i.e. before `corrupt_archive`/`temp_restore` paths are
  computed and before any archive/copy occurs, satisfying REQ-003.
- On failure, return `RecoveryResult(success=False, action="backup_wrong_domain",
  detail=err, dry_run=dry_run)`, mirroring the existing `bad_backup` early-return
  pattern immediately above it (lines 199-204).

## Alternatives considered

- Running `_run_logical_verification()` (the existing RAG/session-specific
  consistency check) before the archive/copy step instead of a new lightweight check —
  rejected: that function is designed to run post-restore against the live DB path and
  duplicating it pre-restore against the backup would perform much heavier validation
  than the Plan's Problem/Reason for change calls for, and duplicates `_run_logical_verification`'s
  existing responsibility.
- Column-level schema validation in addition to table-name checking — rejected per
  `UNK-01`'s resolution path (non-blocking; table names already differ across domains,
  so table-only validation is expected to be sufficient).

## Implementation
### Target file
`scripts/db/recovery.py`

### Procedure
1. Add a `_REQUIRED_TABLE_BY_DOMAIN` mapping (or equivalent inline logic) near
   `_run_integrity_check` (before `_restore_from_backup`, i.e. after line 168) giving
   the one primary required table per domain: `{"rag": "documents", "session":
   "sessions"}`.
2. Add `_verify_domain_identity(backup: Path, target: str) -> tuple[bool, str | None]`
   in the same location, opening `backup` via `SQLiteHelper(target,
   db_path=str(backup)).open()` and querying `sqlite_master` for the domain's
   required table.
3. Call `_verify_domain_identity(backup, target)` in `_restore_from_backup()`
   immediately after the integrity-check block (after current line 204) and before
   `ts = format_timestamp()` (current line 206); return early with
   `action="backup_wrong_domain"` on failure.

### Method
```python
_REQUIRED_TABLE_BY_DOMAIN: dict[str, str] = {
    "rag": "documents",
    "session": "sessions",
}


def _verify_domain_identity(
    backup: Path, target: str
) -> tuple[bool, str | None]:
    """Verify backup contains the required table for target's domain.

    Returns (True, None) if the domain's required table is present in the backup's
    sqlite_master; (False, detail) otherwise. Unknown/unmapped targets pass through
    (no domain-identity constraint defined for them).
    """
    required_table = _REQUIRED_TABLE_BY_DOMAIN.get(target)
    if required_table is None:
        return True, None
    with SQLiteHelper(target, db_path=str(backup)).open() as db:
        cursor = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (required_table,),
        )
        if cursor.fetchone() is None:
            return False, (
                f"backup missing required table '{required_table}' for "
                f"domain '{target}'"
            )
    return True, None
```

### Details
- Place `_REQUIRED_TABLE_BY_DOMAIN` and `_verify_domain_identity` directly after
  `_run_integrity_check` (which ends at line 67) and before `_restore_from_backup`
  (line 171), so both integrity-related helpers stay adjacent.
- Call site inside `_restore_from_backup()`, inserted between the existing lines 204
  and 206:
  ```python
  domain_ok, domain_error = _verify_domain_identity(backup, target)
  if not domain_ok:
      err = domain_error or f"backup failed domain-identity check for target={target}"
      logger.error("Backup belongs to a different persistence domain: %s", err)
      return RecoveryResult(
          success=False, action="backup_wrong_domain", detail=err, dry_run=dry_run
      )
  ```
- No new imports are required — `SQLiteHelper` and `Path` are already imported in
  this module (confirmed via `rg -n "^import|^from" scripts/db/recovery.py`).
- `RecoveryResult(action="backup_wrong_domain", ...)` requires the corresponding field
  addition in `scripts/db/models.py` — tracked separately in
  `implementations/20260908-133223_02_scripts_db_models.py.md` (REQ-002); `action` is a
  plain string field (not an enum), so no import/type dependency exists between the two
  files.

## Compatibility considerations

`action` is a string field on `RecoveryResult` (`scripts/db/models.py:127`), not an
enum — adding a new value is additive and does not change the type or break existing
callers that pattern-match on known string values (they already tolerate unmatched
strings as a fallthrough case, since `action` has always been an open string field).

## Security considerations

N/A: this change only adds a read-only `sqlite_master` query against a backup file
that is already being read by `_run_integrity_check` in the same code path — no new
file access, network access, or credential handling is introduced.

## Rollback considerations

Revert is a single-file code revert (`git checkout` on this commit's change to
`scripts/db/recovery.py`) — no data migration, schema change, or persisted state is
introduced by this change, so no rollback risk beyond the normal code-revert path.

## Validation plan

- `uv run pytest tests/db/test_db_recovery.py -v` — new wrong-domain rejection test(s)
  pass (tracked in `implementations/20260908-133223_03_tests_db_test_db_recovery.py.md`).
- `uv run pytest tests/db/test_db_recovery.py -v` — `test_recover_corrupt_rag_restores`
  and `test_recover_bad_backup` continue to pass unchanged (REQ-004): both already
  mock `SQLiteHelper` via the `mock_sqlite_helper` fixture, so the new
  `_verify_domain_identity` call will operate against the mocked instance in those
  tests, not a real file — no test-side change needed for them to keep passing.
- Full validation sequence per `rules/toolchain.md` (ruff, mypy, lint-imports,
  ast-grep, bandit, pytest, diff-cover, pre-commit).

## Completion criteria

- `_verify_domain_identity()` exists in `scripts/db/recovery.py` and is called between
  the integrity check and the archive/copy step in `_restore_from_backup()`.
- A wrong-domain backup returns `action="backup_wrong_domain"` before
  `corrupt_archive`/`temp_restore` paths are touched.
- `test_recover_corrupt_rag_restores` and `test_recover_bad_backup` pass unchanged.
- Full validation sequence (`rules/toolchain.md`) passes with no new failures.

## Out of scope

Changes to `scripts/db/models.py` (new `action` value — separate document) and
`tests/db/test_db_recovery.py` (new test cases — separate document); no other file is
modified by this document.

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003
- **Source issue**: issues/20260907-124049_h0703_backup_candidate_domain_identity_validation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-072325_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260908-133223
- **Related target files**: scripts/db/recovery.py
