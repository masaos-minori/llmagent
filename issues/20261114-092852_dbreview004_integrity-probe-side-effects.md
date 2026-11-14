# Integrity and identity probes write to the files they inspect and report a missing database as healthy

## Priority
Medium

## Summary
`db.recovery._run_integrity_check`, `_verify_domain_identity` and the logical stage open files through `SQLiteHelper.open()`, which runs `PRAGMA journal_mode=WAL` and `sqlite3.connect` (creating a file when absent). The probes therefore modify backups and archives and turn a missing database into an empty "healthy" one.

## Background
Found by an adversarial review of `scripts/db` at commit 0fe68d3 (Review finding F-004). Evidence label: `Verified by test` (ad hoc reproduction), confidence High.

## Problem
- Missing path: `run_integrity_check(<nonexistent>.sqlite, "rag")` returned `(HEALTHY, None)` and the file now existed. In `recover_corruption` a vanished live database therefore takes the `vacuum` branch (also under `dry_run=True`, which then creates the file) instead of a restore or an error.
- Backup mutation: `run_integrity_check` on a rollback-journal backup changed its bytes and left it in WAL mode (`PRAGMA journal_mode` returned `wal` afterwards). `_backup_is_usable`, `rotation._verify_archive` and the drill all call these probes on backups and archives. A fake `-wal` placed next to a backup was also removed during the same check.
- A read-only backup (immutable media, restrictive permissions) fails the pragma and is classified `PERMISSION_FAILURE`, which `_backup_is_usable` reports as `bad_backup`.

## Reason for Change
A verification step that alters its subject undermines forensic value, breaks checksum-based backup validation, and misreports state. Dry-run must be side-effect free.

## Implementation Intent
Open probe targets read-only (`file:...?mode=ro` URI) without applying write pragmas, and check existence explicitly before probing so a missing file is its own condition rather than HEALTHY.

## Target Files or Areas
- `scripts/db/recovery.py` (`_run_integrity_check`, `_verify_domain_identity`, `recover_corruption`)
- `scripts/db/recovery_verification.py`
- `scripts/db/helper.py` (`apply_connection_pragmas` usage for read-only opens)
- `scripts/db/rotation.py` (`_verify_archive`)
- `tests/db/test_db_recovery.py`

## Required Changes
- Add a read-only open mode for probes that skips `journal_mode`/`synchronous` pragmas.
- Return a distinct, non-healthy condition for a missing path and never create the file.
- Ensure `dry_run=True` leaves the filesystem unchanged.
- Add tests that hash the backup before and after verification.

## Constraints
- A candidate under verification may still need write access (WAL recovery); the read-only mode must be chosen per call.
- Keep `DbCondition` consumers (`rotation`, `recovery_drill`) working; document any new enum member.

## Acceptance Criteria
- Verifying a backup leaves its bytes, journal mode and sibling files unchanged.
- A missing live database yields a non-HEALTHY result and no file is created, including with `dry_run=True`.
- A read-only backup verifies successfully.

## Testing Expectations
Unit tests with temporary files: sha256 before/after, directory listing before/after, missing path, read-only file mode. `uv run pytest tests/db`.

## Documentation Impact
Update the recovery condition table in the ADR-008 documentation if a new condition is introduced.

## Out of Scope
- Changing what `PRAGMA integrity_check` verifies.
- The vec extension handling in the logical stage (`issues/20261114-092848_dbreview001_logical-verify-vec-extension.md`).

## Dependencies
N/A: none

## Unresolved Questions
- What should `recover_corruption` do for a missing live database: attempt a restore, or report an error for operator action? Needs a maintainer decision.

## AI Implementation Instruction
Follow `skills/python-implementation/SKILL.md`. Do not alter the production pragma policy for normal connections. English comments and logs.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261114-092852
- **Related target files**: scripts/db/recovery.py, scripts/db/recovery_verification.py, scripts/db/helper.py, scripts/db/rotation.py, tests/db/test_db_recovery.py
