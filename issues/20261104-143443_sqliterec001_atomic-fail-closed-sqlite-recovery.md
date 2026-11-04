# Make SQLite database recovery atomic, fail-closed, and rollback-safe

## Priority
High

## Summary
Redesign the SQLite corruption-recovery path so the database file and its `-wal`/`-shm` sidecars are handled as one recovery unit, all verification completes on an isolated candidate before activation, and every failure leaves a known-safe active state that `RecoveryResult` reports truthfully.

## Background
Verified against current source on 2026-11-04 (confirmed by repository evidence):

- `scripts/db/recovery_restore.py` builds sidecar names with `Path.stem` (`f"{stem}{suffix}"` in `_quarantine_sidecar_files`, `_stage_backup_sidecars`, and `_stage_restore` step 4a). For `rag.sqlite` this resolves to `rag-wal` / `rag-shm`, not SQLite's `rag.sqlite-wal` / `rag.sqlite-shm`, so real sidecars are neither quarantined nor staged.
- Sidecar quarantine failure and staged-sidecar move failure are logged as warnings and recovery proceeds ("proceeding without it").
- `_restore_from_backup` in `scripts/db/recovery.py` activates the backup with `os.replace(temp_restore, db_path)` inside `_stage_restore`, and only then runs `_post_restore_failure` (physical re-check, then logical verification). A failed verification returns a failure result but nothing restores the archived corrupt original or the prior state.
- `_run_logical_verification` in `scripts/db/recovery_verification.py` returns `(True, None)` on `sqlite3.Error` ("a verification gap must never block a completed physical restore"), so a verification that could not run is reported as success. Unknown targets also return success.
- `RecoveryResult` (`scripts/db/models.py`) has `logical_ok: bool | None = None`; the success result built in `_restore_from_backup` never sets it.

## Problem
A database can be activated with stale or missing sidecars, fail or skip verification after activation, and still be reported as `restored`. The defects combine into one atomicity problem, so independent cosmetic fixes would leave inconsistent semantics.

## Reason for Change
Data-integrity risk on the recovery path, which runs exactly when the database is already damaged. The result contract also misreports the active state to the CLI and operators.

## Implementation Intent
Establish one fail-closed recovery protocol: build and verify an isolated candidate (database plus sidecars as a unit), activate only a fully verified file set, and either complete successfully or preserve/restore the prior active database. The result must describe the state actually active, not only the last attempted operation. Mandatory verification that cannot run is a failure, not a success.

## Target Files or Areas
- `scripts/db/recovery_restore.py`
- `scripts/db/recovery.py`
- `scripts/db/recovery_verification.py`
- `scripts/db/models.py` (`RecoveryResult`)
- Recovery CLI entry point (exit-code mapping): Unknown, to be located during planning
- `tests/db/test_db_recovery.py`

## Required Changes
- Resolve target and backup sidecar paths with the full database filename (`Path(str(db_path) + "-wal")`, `Path(str(db_path) + "-shm")`).
- Treat quarantine, copy, rename, and placement failures of WAL/SHM files as fatal recovery errors.
- Require service shutdown or a documented exclusive-access mechanism before file operations.
- Restore into a temporary candidate location and run physical and logical verification there; activate only after every mandatory verification succeeds.
- Roll back to the archived original if activation or post-activation verification fails; if rollback fails, report an explicit non-serviceable state.
- Change a `sqlite3.Error` in mandatory logical verification from success to an explicit failure (for example `verification_unavailable`) with a non-zero CLI exit code.
- Populate `RecoveryResult.logical_ok` consistently (or remove it through an explicit API change) and expose the final active-database state.

## Constraints
- Preserve existing public interfaces unless an acceptance criterion requires an explicit contract change.
- Prefer fail-closed behavior for recovery and mandatory integrity verification.
- Dry-run and diagnostic paths must not alter live databases.
- Error messages carry operational detail but no secrets or database row content (REQ-010/AC-7 of the existing verification contract).
- Automatic recovery stays prohibited for `workflow` and `eventbus` (ADR-008).

## Acceptance Criteria
- Recovery handles `rag.sqlite-wal` and `rag.sqlite-shm`; it never looks for `rag-wal` or `rag-shm` for that database.
- No sidecar operation failure produces a successful recovery result.
- A candidate that fails physical or logical verification is never activated.
- A failure after activation begins restores the original database or leaves an explicit non-serviceable state.
- A `sqlite3.Error` during mandatory logical verification returns failure and a non-zero CLI exit code.
- `RecoveryResult` unambiguously reports `logical_ok` and the final active state.

## Testing Expectations
- Unit tests for each changed branch; integration tests in WAL mode with production-equivalent schemas.
- Fault-injection tests for every fail-closed path: permission errors, locked files, corrupt candidates, rollback failure, source and target filenames that differ.
- Cover the recoverable domains (`rag`, `session`) and confirm `workflow`/`eventbus` remain refused.
- Run `uv run pytest tests/db/test_db_recovery.py -q`, ruff, and mypy per `rules/toolchain.md`.

## Documentation Impact
Update the ADR-008 related design and the operations runbook for the new result contract, exit codes, and the exclusive-access requirement (intent, failure behavior, operational notes). Exact documents: Unknown, to be located during planning.

## Out of Scope
- Backup creation, rotation, and retention.
- Migration safety (separate issue).
- Changes to the consistency checks themselves (separate RAG and session issues).

## Dependencies
- `issues/20261104-143443_sessmoke001_atomic-session-smoke-test.md`: recovery verification of the session domain must stay read-only; fix order is independent, but the read-only contract is shared.
- `issues/20261104-143443_ragverify001_complete-fail-closed-rag-consistency.md`: the logical verifier consumes the RAG report; a stricter report changes what this path rejects.

## Unresolved Questions
- Production service-stop or exclusive-lock mechanism: unknown.
- Recovery CLI exit-code contract: unknown.
- RTO/RPO requirements: unknown.

## AI Implementation Instruction
Implement the protocol as one change set. Do not infer unspecified production requirements; record them under Unresolved Questions first. Do not weaken the existing count-only error detail. Keep each failure path covered by a negative test before changing the production branch.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261104-143443
- **Related target files**: `scripts/db/recovery_restore.py`, `scripts/db/recovery.py`, `scripts/db/recovery_verification.py`, `scripts/db/models.py`, `tests/db/test_db_recovery.py`
