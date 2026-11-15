## Goal
- Assert probe invariance, MISSING policy, and read-only-backup verification at the recovery level.

## Scope
**Release unit**: ro-probes-missing-policy (Phase 3 of the plan; lands with `_2`/`_3`)

- In scope: `tests/db/test_db_recovery.py` — probe byte/dir invariance tests, MISSING tests (incl. dry_run), `0444` backup test, logical-stage invariance test (REQ-002..REQ-006).

## Assumptions
- Every existing `recover_corruption` test in this file patches `_run_integrity_check` directly (checked this cycle: `mock_db_cfg` points at fixed `/tmp/*.db` paths and the `mock_sqlite_helper` fixture only patches helper internals) — the existence-first check and read-only probes are invisible to them, so no existing test is expected to change; any unexpected red is a signal to re-classify, not to patch around.
- Verification correction (2026-11-15 execution): the assumption misses `TestRunIntegrityCheckCharacterization` (`:1663`), which calls `_run_integrity_check` directly with `Path("/tmp/rag.db")`. The new required `read_only` kwarg and the existence-first check make all three cases red: re-classified as contract churn — the class gains explicit `read_only=True` and a real `tmp_path` file placeholder (the `mock_recovery_db` helper mock stays; the placeholder only satisfies the existence gate). See Procedure step 8.
- The file already contains Plan 001/002/003 test additions when this procedure executes; line citations are the pre-landing tree — anchor on test names/sections and append new cases at the end of the file (plan overlap record: 004's additions are disjoint from 001 vec tests, 002 action-flips, 003 quarantine tests).
- Real-file tests follow the `test_recover_dry_run_corrupt_file_unchanged` pattern (`:260`: `tmp_path` database + config patched to it + bytes/directory assertions).

## Design decisions
- Assertions use `hashlib.sha256` of the file bytes plus `os.listdir` snapshots (Plan Tests row): byte- and filesystem-observable effects only, no pragma-mocking shortcuts — this is what AC-1 promises.

## Alternatives considered
- Asserting invariance through `mock_sqlite_helper` call-kwargs only: rejected — kwargs prove intent, not effect; the Issue's complaint is precisely that a nominally-verification call mutated files.

## Implementation
### Target file
`tests/db/test_db_recovery.py`

### Procedure
1. Add `test_run_integrity_check_leaves_backup_unchanged` (new): real `tmp_path` WAL-mode database; sha256 + `listdir` snapshot; `run_integrity_check(path, "rag")` → `(DbCondition.HEALTHY, None)`; sha256 identical, no new `-wal`/`-shm` entries (REQ-006/AC-1).
2. Add `test_run_integrity_check_keeps_rollback_journal_mode` (new): real rollback-journal (`journal_mode=delete`) database; after `run_integrity_check`, `PRAGMA journal_mode` (opened separately read-write) still reports `delete` and the file bytes are unchanged — the ADR-008 "switched to WAL" gap is closed (REQ-003/AC-1).
3. Add `test_backup_is_usable_leaves_backup_unchanged` (new): sha256 + `listdir` unchanged across `_backup_is_usable(backup, "rag")` on a healthy backup (REQ-006/AC-1).
4. Add `test_backup_is_usable_accepts_readonly_backup` (new): `chmod 0o444` backup; `_backup_is_usable` returns `(None, "")` — a read-only media backup verifies successfully instead of failing with `bad_backup` (REQ-003/AC-3).
5. Add `test_recover_missing_live_db_reports_missing_database` (new): tmp-patched config whose `rag_db_path` does not exist (create-then-unlink for realism); `recover_corruption(target="rag")` → `success is False`, `action == "missing_database"`, `active_db_state == "missing"`, detail names the path; `listdir` shows no created database or sidecar files (REQ-002, REQ-004/AC-2).
6. Add `test_recover_missing_live_db_dry_run` (new): same as step 5 with `dry_run=True` — identical result and no file created (REQ-004/AC-2).
7. Add `test_logical_verification_leaves_db_unchanged` (new): real tmp database; `db.recovery_verification._run_logical_verification` with a pure-read `verify` callback; sha256 + `listdir` unchanged afterwards (REQ-005/AC-1; imports already present in the module or added at the top of the test file).
8. Re-classify `TestRunIntegrityCheckCharacterization` (verification churn): pass `read_only=True` explicitly at the three direct `_run_integrity_check` calls (the contract now requires every call site to state the mode) and replace the fixed `/tmp/rag.db` path with a `tmp_path` placeholder file so the existence-first gate is satisfied deterministically; the mocked-helper semantics of each case are unchanged.

### Method
- Append new test functions at the end of the file; reuse existing fixtures (`tmp_path`, config-patch pattern from `test_recover_dry_run_corrupt_file_unchanged`).

### Details
- No edits to existing tests expected (Assumptions row 1); Plan 002/003 landed action assertions stay green — AC-3 regression.
- MISSING tests must not use `mock_sqlite_helper`'s fixed `/tmp` paths: they patch the config to `tmp_path` and let the real helper run (the point is no-creation).

## Compatibility considerations
- Test-only; `check_mock_patch_targets.py` gate applies if new `patch(...)` calls are added (no module-level-import patching of moved symbols).

## Security considerations
- N/A: test-only.

## Rollback considerations
- Inside the ro-probes-missing-policy unit: revert with `_2`/`_3`/`_6`. Checkout revert.

## Validation plan
- `uv run pytest tests/db/test_db_recovery.py -v` → new cases green, whole file green (AC-1..AC-3).
- `uv run pytest tests/db -q` → rotation/drill/helper regressions green.
- `uv run ruff check tests/db/test_db_recovery.py` → clean.

## Completion criteria
- AC-1 (sha256/dir invariance incl. journal-mode preservation), AC-2 (MISSING incl. dry_run, no creation), AC-3 (0444 backup usable) are each asserted by a named test.

## Out of Scope
- Helper unit tests (companion `20261115-084603_4`).
- Rotation archive invariance test (companion `20261115-084603_6`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261115-113615 | 20261115-113615 | test: db: recovery.py: characterization: and: regression: tests |
| 2 | Add or update tests per Validation plan | Completed | 20261115-113615 | 20261115-113615 | covered by companion test procedures |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261115-113615 | 20261115-113615 | targeted gates green (tests/db, ruff, mypy) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261115-113615 | 20261115-113615 | N/A: docs handled by companion procedures _7/_8 |

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
- **Requirement ID**: REQ-002, REQ-003, REQ-004, REQ-005, REQ-006
- **Source issue**: issues/20261114-092852_dbreview004_integrity-probe-side-effects.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-041859_dbreview004_integrity-probe-side-effects.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-084603
- **Related target files**: tests/db/test_db_recovery.py