# Handle stale -wal/-shm files during staged atomic database replacement

## Priority
High

## Summary
`_restore_from_backup()` already stages the restored candidate via a temp file and swaps it in
with `os.replace()` (atomic replace, already implemented per memo2.md's Issue H-07-04 core
intent), and already quarantines the pre-existing corrupt database rather than deleting it.
However, it never touches the target's `-wal`/`-shm` sidecar files, so a stale `-wal`/`-shm`
pair left next to the old `db_path` can be picked up by SQLite against the newly-restored main
database file after the swap.

## Background
Confirmed by direct read of `scripts/db/recovery.py` lines 206-250 (`_restore_from_backup`):
quarantine (`corrupt_archive`, line 213), staged copy (`temp_restore`, line 217), and atomic
swap (`os.replace(temp_restore, db_path)`, line 218) are all already implemented, satisfying
most of memo2.md's H-07-04 structural requirements. There is no reference anywhere in
`scripts/db/recovery.py` to `.wal` or `.shm` suffixes (confirmed by `grep`).

## Problem
- If `db_path` was operating in WAL journal mode before corruption, `db_path`'s `-wal`/`-shm`
  sidecars may still exist on disk after `os.replace()` swaps in the restored main file.
  SQLite associates a `-wal`/`-shm` pair with the main database file by path, not by
  content-identity — a stale `-wal` file from the old (corrupt) database, left in place next
  to the freshly-restored main file, can be replayed against it on next open, potentially
  reintroducing exactly the inconsistency the restore was meant to fix.
- The backup file itself may or may not include committed WAL content depending on how it was
  produced (`scripts/db/rotation.py`'s `rotate_all_dbs()`) — this issue's scope does not
  extend to changing backup creation, but the restore path must not assume the backup
  captured WAL state without checking whether `-wal`/`-shm` files exist for `backup_path` too.
- No test in `tests/db/test_db_recovery.py` exercises `-wal`/`-shm` file presence/absence
  around a restore.

## Reason for Change
Restoring a validated main-database file while leaving a stale `-wal`/`-shm` pair from the
pre-restore state can silently undo or corrupt the just-completed restore the next time the
database is opened, defeating the purpose of the atomic-replace step that already exists.

## Implementation Intent
Before the atomic swap, quarantine (alongside `corrupt_archive`) or remove any pre-existing
`-wal`/`-shm` files associated with `db_path` so they cannot be paired with the restored main
file. If the backup itself has associated `-wal`/`-shm` files, stage and swap them together
with the main file so the triple stays consistent. Do not invent checkpoint behavior beyond
what `scripts/db/rotation.py`'s existing backup mechanism already guarantees — inspect it
first to confirm whether backups are taken via SQLite's online backup API (WAL-consistent) or
a raw file copy (potentially WAL-inconsistent) before deciding how `-wal`/`-shm` should be
handled here.

## Target Files or Areas
- `scripts/db/recovery.py` (`_restore_from_backup()`)
- `scripts/db/rotation.py` (read-only, to confirm existing backup-creation mechanism and
  whether it produces `-wal`/`-shm` sidecars)
- `tests/db/test_db_recovery.py`

## Required Changes
- Inspect `scripts/db/rotation.py`'s backup-creation implementation to confirm whether WAL
  content is checkpointed into the main file before backup, or whether `-wal`/`-shm` sidecars
  are backed up alongside it.
- Quarantine or remove stale `db_path`-associated `-wal`/`-shm` files before the atomic swap,
  consistent with whatever the backup-creation mechanism guarantees.
- If the backup has its own `-wal`/`-shm` sidecars, stage and swap them atomically together
  with the main file (same staging directory, same atomic-replace pattern already used for
  the main file).
- Add test cases: restore succeeds cleanly when stale `-wal`/`-shm` files exist next to
  `db_path` before the swap; restore does not reintroduce the old `-wal`'s content after the
  swap.

## Constraints
- Do not invent WAL-checkpoint behavior that `scripts/db/rotation.py`'s actual backup
  mechanism does not already support — confirm current behavior before implementing rather
  than assuming.
- Do not change backup-creation itself (`rotation.py`) unless the investigation shows the
  current backup mechanism cannot support a WAL-consistent restore at all; if so, stop and
  report rather than expanding this issue's scope silently.
- Preserve the existing quarantine-not-delete behavior for the pre-existing corrupt database
  (already implemented) — extend the same non-destructive principle to any `-wal`/`-shm`
  handling added here.

## Acceptance Criteria
- [ ] A stale `-wal`/`-shm` pair present next to `db_path` before restore does not affect the
      restored database's state after the atomic swap.
- [ ] The restore path's handling of `-wal`/`-shm` files is consistent with what
      `scripts/db/rotation.py`'s backup mechanism actually guarantees (documented, not
      assumed).
- [ ] Stale `-wal`/`-shm` files are quarantined (not silently deleted) consistent with the
      existing `corrupt_archive` pattern, unless investigation shows deletion is safe and
      quarantine is unnecessary.
- [ ] Existing atomic-replace tests (`test_recover_corrupt_rag_restores`,
      `test_recover_restore_verify_failed`) continue to pass unchanged.

## Testing Expectations
`uv run pytest tests/db/test_db_recovery.py -v`; add the `-wal`/`-shm`-specific test cases
described above; manual verification with a real WAL-mode SQLite file is recommended given the
difficulty of mocking SQLite's WAL replay behavior meaningfully.

## Documentation Impact
If a canonical recovery specification under `docs/` describes the restore procedure, add the
WAL/SHM handling decision there once implemented.

## Out of Scope
- Do not decide whether the restored database is logically usable (that is
  `_run_logical_verification()`'s existing role).
- Do not change `scripts/db/rotation.py`'s backup-creation mechanism unless the investigation
  in Required Changes shows it is currently incapable of supporting a correct restore — see
  Constraints.
- Do not enable Workflow/EventBus automatic restoration.

## Dependencies
Depends on `issues/done/20260903-110304_h0701_define-recovery-policy-per-sqlite-persistence-domain.md`
(H-07-01) and this batch's structured-classification and backup-domain-identity issues
(reliable integrity classification and domain-identity validation feeding into the same
restore path this issue modifies).

## Unresolved Questions
Whether `scripts/db/rotation.py`'s `rotate_all_dbs()` currently checkpoints WAL content before
backup, or backs up `-wal`/`-shm` sidecars alongside the main file — must be confirmed by
direct read of `rotation.py` before implementation, not assumed from this issue's text.

## AI Implementation Instruction
Read `scripts/db/rotation.py`'s actual backup implementation first — do not assume
WAL-consistency behavior. If backups are not WAL-consistent, report this as a finding rather
than silently expanding scope to fix backup creation. Keep the atomic-replace mechanism for
the main file (`os.replace`) unchanged; only add `-wal`/`-shm` handling around it.
