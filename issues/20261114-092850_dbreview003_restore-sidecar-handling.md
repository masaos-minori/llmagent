# Restore removes the original -wal/-shm before verification and never restores them on rollback

## Priority
High

## Summary
`db.recovery_restore._stage_restore` moves the live database's `-wal`/`-shm` sidecars into a quarantine directory before the candidate is verified. Failure paths then report `active_db_state="preserved_original"` although the original's sidecars are gone. The rollback paths restore only the main file, and the success path deletes the quarantine copy.

## Background
Found by an adversarial review of `scripts/db` at commit 0fe68d3 (Review finding F-003). The restore documents say a candidate that fails verification "never touches the live database". Evidence label: `Verified by test` (ad hoc reproduction, re-confirmed in the second pass) for the pre-verification removal and the success-path rmtree (by code); `Needs confirmation` for foreign-WAL contamination after rollback. Confidence High and Low respectively. The issue priority rests on the verified WAL removal alone.

## Problem
- Reproduction: a live database with an uncheckpointed `-wal` file, a candidate forced to fail verification. Result `restore_verify_failed` / `preserved_original`, but the live `-wal` no longer existed and a `*_sidecar_quarantine_*` directory held the copy.
- Committed transactions that exist only in the WAL are therefore removed from the live location even though the original is reported as preserved.
- `_rollback_or_non_serviceable` and the `OSError` rollback both do `os.replace(corrupt_archive, db_path)` only. The backup's sidecars already moved to `db_path-wal`/`-shm` remain next to the restored original. Whether SQLite then applies that foreign WAL is NOT established: a second-pass reproduction (a WAL copied from database A next to an unrelated database B, then read) did not change B's contents. Treat stale foreign sidecars as a hygiene risk (Needs confirmation), not as demonstrated corruption.
- On success `_restore_from_backup` runs `shutil.rmtree(quarantine_dir)`, discarding the only copy of the old WAL; `corrupt_archive` is a copy of the main file alone.

## Reason for Change
Recovery must be reversible until the candidate is verified, and its reported state must match reality. Silent loss of WAL-resident data and cross-file WAL contamination are data-integrity risks.

## Implementation Intent
Defer any change to the live path's sidecars until after the candidate is verified, or make every failure path restore them. On rollback, remove sidecars that came from the backup and put back the original's sidecars. Decide explicitly whether the quarantined WAL is retained after a successful restore.

## Target Files or Areas
- `scripts/db/recovery_restore.py` (`_quarantine_sidecar_files`, `_stage_restore`)
- `scripts/db/recovery.py` (`_restore_from_backup`, `_activate_candidate`, `_rollback_or_non_serviceable`)
- `tests/db/test_db_recovery.py`

## Required Changes
- Move the quarantine step after successful candidate verification, or restore the sidecars on every failure branch.
- On rollback, delete backup-origin sidecars at the live path before or while restoring the original.
- Decide and document the retention of the quarantine directory after success; do not delete the only copy silently.
- Add tests asserting live sidecar presence after each failure branch.

## Constraints
- The WAL of a corrupt database may itself be unusable; the chosen behavior must be an explicit decision recorded in ADR-008 terms, not an accident of ordering.
- Do not run the recovery against `/opt/llm/db` in tests.

## Acceptance Criteria
- After any verification failure the live `-wal`/`-shm` files are byte-identical to before the call.
- After a rollback no sidecar originating from the backup remains at the live path.
- The retention decision for the quarantined WAL is covered by a test and stated in the docs.

## Testing Expectations
Unit tests with temporary directories: failure at candidate verification, failure after activation, rollback failure. Assert file sets and contents. `uv run pytest tests/db`.

## Documentation Impact
Update the ADR-008 recovery documentation for the sidecar handling and quarantine retention decision, keeping to behavior and intent rather than implementation detail.

## Out of Scope
- Logical verification and the vec extension (`issues/20261114-092848_dbreview001_logical-verify-vec-extension.md`).
- Retention of leftover quarantine directories (`issues/20261114-092857_dbreview008_artifact-retention-gaps.md`).

## Dependencies
- `issues/20261114-092849_dbreview002_partial-activation-rollback.md` touches the same functions; implement together or in sequence.

## Unresolved Questions
- Is discarding the corrupt database's WAL on success intended by ADR-008? Needs maintainer confirmation.
- Can a backup-origin WAL ever be applied to the restored original? One reproduction attempt said no; the claim stays unconfirmed. Removing backup-origin sidecars on rollback is kept as a precaution, not as a proven fix.

## AI Implementation Instruction
Follow `skills/python-implementation/SKILL.md`. Keep changes inside the listed files. English comments and logs. Do not delete any directory tree during testing outside temporary directories.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261114-092850
- **Related target files**: scripts/db/recovery_restore.py, scripts/db/recovery.py, tests/db/test_db_recovery.py
