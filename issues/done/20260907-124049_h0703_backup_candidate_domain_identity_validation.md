# Reject backup candidates from the wrong SQLite persistence domain during restore

## Priority
High

## Summary
`_restore_from_backup()` in `scripts/db/recovery.py` already checks that a backup candidate
exists and passes `PRAGMA integrity_check` before restoring, but it never verifies that the
candidate actually belongs to the target's persistence domain (`rag`/`session`/`workflow`/
`eventbus`). A structurally valid SQLite file belonging to a different domain — e.g. restoring
`session.sqlite`'s backup onto `rag.sqlite` — currently passes validation and would be
atomically swapped into place.

## Background
Confirmed by direct read of `scripts/db/recovery.py` lines 171-257 (`_restore_from_backup`):
existence check (line 188) and integrity check via `_run_integrity_check(backup, target)`
(line 198) both run before restoring, matching part of memo2.md's Issue H-07-03 intent.
However `_run_integrity_check()` only runs `PRAGMA integrity_check` (line 59) — it opens the
file through `SQLiteHelper(target, db_path=...)` but does not verify that the file's schema
matches `target`'s required tables.

## Problem
- No required-table/schema-signature check exists anywhere in the restore path.
  `SQLiteHelper(target, db_path=str(db_path)).open()` accepts any well-formed SQLite file
  regardless of its actual schema — it only opens the file and lets the caller run whatever
  query it wants; nothing rejects a schema mismatch on open.
- `tests/db/test_db_recovery.py` has no test case for "valid SQLite backup belonging to the
  wrong domain" — the closest existing test (`test_recover_bad_backup`) only covers a backup
  that itself fails `PRAGMA integrity_check`, not one that passes it but belongs to a
  different domain.
- `RecoveryResult.action` values are currently limited to `no_backup` and `bad_backup` for
  pre-restore failures — there is no distinct action for "backup exists, is valid SQLite, but
  is the wrong domain," so an operator cannot currently distinguish "no valid backup was
  found" from "a backup was found but would have been applied cross-domain" from the action
  alone.

## Reason for Change
Applying a structurally valid but wrong-domain backup would silently replace, e.g.,
`rag.sqlite` with a copy of `session.sqlite`, passing the current physical-integrity check
while producing a database that fails every subsequent RAG-specific logical-consistency check
(`check_rag_consistency`) — by which point the original `rag.sqlite` has already been moved to
`corrupt_archive` (not deleted, but no longer live) and the operator must recover from the
quarantine copy instead of the intended backup.

## Implementation Intent
Add a lightweight domain-identity check between the existing integrity check and the
archive/copy step in `_restore_from_backup()`: verify the candidate contains the required
table(s) for `target` (e.g. a `documents`/`chunks` table for `rag`, a `sessions` table for
`session`) before proceeding to archive-and-replace. Reuse `SQLiteHelper` to query
`sqlite_master`/`sqlite_schema` rather than opening a second, parallel connection mechanism.

## Target Files or Areas
- `scripts/db/recovery.py` (`_restore_from_backup()`, and a new helper for domain-identity
  verification)
- `scripts/db/models.py` (`RecoveryResult.action` — new value)
- `tests/db/test_db_recovery.py`

## Required Changes
- Add a domain-identity check (required-table signature) that runs after the existing
  integrity check and before the archive/copy step in `_restore_from_backup()`.
- Return a new `action="backup_wrong_domain"` (or equivalent, matching existing naming style)
  when the candidate fails this check, without touching `db_path` or writing
  `corrupt_archive`.
- Add test cases: a structurally valid SQLite file for a different domain, and confirm the
  live database and any files under its directory are unchanged when this check fails.

## Constraints
- Do not overload the existing `bad_backup` action for this new failure category — this
  requires a distinct action rather than conflating "corrupt file" with "wrong domain, but
  structurally valid."
- Do not implement backup retention/rotation policy (out of scope; owned elsewhere in
  `scripts/db/rotation.py`).
- Keep the domain-identity check lightweight (schema/table-name signature) — do not implement
  full logical-consistency verification here (that is `_run_logical_verification()`'s existing
  post-restore role).

## Acceptance Criteria
- [ ] A structurally valid SQLite file belonging to a different persistence domain is
      rejected before the live database is touched.
- [ ] The rejection returns a distinct `action` value from `no_backup`/`bad_backup`.
- [ ] The live database and its directory (no new `corrupt_archive` file) are unchanged when
      domain-identity validation fails.
- [ ] Existing `test_recover_corrupt_rag_restores`/`test_recover_bad_backup` tests continue to
      pass unchanged.

## Testing Expectations
`uv run pytest tests/db/test_db_recovery.py -v`; add the wrong-domain test case described
above.

## Documentation Impact
If a canonical recovery specification under `docs/` enumerates `RecoveryResult.action`
values, add the new value there. Otherwise none expected.

## Out of Scope
- Do not change the final atomic-replacement mechanism itself beyond adding the pre-check
  (no change to `os.replace()` — tracked separately in this batch).
- Do not implement backup retention or rotation policy.
- Do not enable recovery for `workflow`/`eventbus` (remains prohibited per
  `no_recovery_allowed`).

## Dependencies
Depends on `issues/done/20260903-110304_h0701_define-recovery-policy-per-sqlite-persistence-domain.md`
(H-07-01) and the structured-classification issue filed alongside this one (reliable
`INVALID_FORMAT`/`CORRUPTION` distinction feeding into the same integrity check this issue
builds on).

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Keep the new check schema-signature-based (table/column existence), not a full
data-consistency pass — the post-restore logical-verification stage
(`_run_logical_verification`, already implemented) is the correct place for deeper checks. Do
not change `os.replace()`/atomic-swap or WAL/SHM handling in this issue.
