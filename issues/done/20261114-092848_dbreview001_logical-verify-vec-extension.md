# Recovery logical verification opens the candidate without the sqlite-vec extension, so every rag/session restore is refused

## Priority
High

## Summary
`db.recovery_verification._run_logical_verification` opens the database under verification through `SQLiteHelper(target, db_path=...)` without passing `sqlite_vec_so`. The vec0 virtual tables cannot be read, so a healthy rag or session database is always reported as inconsistent. The outcome is that automatic recovery of rag and session can never reach `restored`.

## Background
Found by an adversarial review of `scripts/db` at commit 0fe68d3 (Review finding F-001, `python-code-review`). `db.recovery_drill._verify_rag_session` already documents this exact failure ("a helper without the extension path cannot read them (`no such module: vec0`)") and threads `sqlite_vec_so` from `DbConfig`; the recovery path does not. Evidence label: `Verified by test` (ad hoc reproduction, not a committed test), confidence High. Second adversarial pass (re-read of code plus new reproductions): claim re-confirmed; the test-coverage statement was narrowed to the directories actually searched.

## Problem
- With an explicit `db_path` and no `sqlite_vec_so`, `SQLiteHelper` sets its default load_vec to `bool("")`, which is False, so the extension is never loaded.
- Reproduction against freshly created, empty, healthy databases built with `/opt/llm/sqlite-vec/vec0.so`:
  - `_run_logical_verification(rag, "rag")` returned `(False, 'embedding_unverified')`
  - `_run_logical_verification(session, "session")` returned `(False, 'read_smoke_fail')`
  - `run_integrity_check(rag, "rag")` returned HEALTHY, so only the logical stage fails.
- `db.recovery._verify_candidate` and `db.recovery._post_restore_failure` both call this function, so `_restore_from_backup` always ends in `logical_verify_failed` for rag and session. The archived original is kept, but the corruption is never repaired.
- `tests/db/test_recovery_drill.py` replaces each vec0 virtual table with a plain-table stand-in, and `tests/db/test_db_recovery.py` has no real vec0 usage (it only sets report fields on mocks), so no test under `tests/db` exercises a real vec0 table through the recovery path. Only `tests/db` was searched; other test directories were not.

## Reason for Change
Recovery is the last-resort path for corrupted rag/session data. A path that deterministically refuses every valid backup gives a false sense of recoverability, and the defect is invisible to the current test suite.

## Implementation Intent
Make the logical-verification stage open the database with the configured sqlite-vec library path, the same way the drill harness does, while keeping the fail-closed behavior for a database that genuinely cannot be opened. Decide at the responsibility level where the path is resolved (`DbConfig` via `build_db_config`) so callers do not each thread it by hand. Add a test that runs against a real vec0 table when the extension is available.

## Target Files or Areas
- `scripts/db/recovery_verification.py` (`_run_logical_verification`)
- `scripts/db/recovery.py` (`_verify_candidate`, `_post_restore_failure`, `_run_integrity_check`)
- `scripts/db/recovery_drill.py` (reference for the existing correct pattern)
- `tests/db/test_db_recovery.py`, `tests/db/test_recovery_drill.py`

## Required Changes
- Resolve `sqlite_vec_so` from `build_db_config()` in the logical-verification stage and pass it to `SQLiteHelper`.
- Make sure `_run_integrity_check` and `_verify_domain_identity` stay consistent with whatever convention is chosen.
- Add a recovery test that restores a backup containing a real `chunks_vec`/`memories_vec` table and asserts `restored` for rag and session.
- Keep a test for the genuine fail-closed case (extension missing or unreadable database gives `verification_unavailable`).

## Constraints
- Fail-closed contract of the logical stage must not weaken: an unreadable database is still `verification_unavailable`.
- Tests must not touch `/opt/llm/db` (see `tests/conftest.py` isolation); use a temporary directory and skip when `vec0.so` is absent.
- `db` must not import from `agent` (import-linter contract).

## Acceptance Criteria
- A healthy rag and a healthy session backup built with real vec0 tables pass `_run_logical_verification`.
- `_restore_from_backup` returns `action="restored"` for both targets in the new tests.
- A database that cannot be opened still returns `(False, "verification_unavailable")`.
- `uv run pytest tests/db` passes; ruff, mypy (CI form), bandit and `lint-imports` are clean.

## Testing Expectations
Regression tests under `tests/db` using a real sqlite-vec extension (skipped with a clear reason when unavailable), plus the existing fail-closed tests. Run the validation sequence in `rules/toolchain.md`.

## Documentation Impact
Check the ADR-008 recovery documentation for any claim that restore verification works for rag/session; update the claim only if it becomes inaccurate. Do not add implementation detail that `skills/DESIGN.md` Docs content policy forbids.

## Out of Scope
- Changing the consistency checks themselves (`check_rag_consistency`, `check_session_consistency`).
- The side-effect behavior of the integrity probe (tracked separately in `issues/20261114-092852_dbreview004_integrity-probe-side-effects.md`).

## Dependencies
- Related: `issues/20261114-092850_dbreview003_restore-sidecar-handling.md` (same restore function; coordinate edits).

## Unresolved Questions
- Should the extension path live in `DbConfig` only, or should `SQLiteHelper` fall back to `build_db_config()` when `db_path` is explicit and `load_vec=True`? Needs a maintainer decision.

## AI Implementation Instruction
Follow `skills/python-implementation/SKILL.md`. Change only the files listed under Target Files or Areas. Do not refactor unrelated code. Write comments and log messages in English.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261114-092848
- **Related target files**: scripts/db/recovery_verification.py, scripts/db/recovery.py, scripts/db/recovery_drill.py, tests/db/test_db_recovery.py, tests/db/test_recovery_drill.py
