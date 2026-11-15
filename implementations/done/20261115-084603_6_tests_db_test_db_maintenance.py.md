## Goal
- Assert that rotation archive verification leaves the archive untouched.

## Scope
**Release unit**: ro-probes-missing-policy (Phase 3 of the plan; lands with `_2`/`_3`)

- In scope: `tests/db/test_db_maintenance.py` — one rotation-archive invariance test (REQ-006).

## Assumptions
- Rotation tests live in this file (`test_rotate_session_db_creates_archive` at `:319`, `test_rotate_all_dbs_archives_all_three` at `:1049`, etc.; no separate rotation test file — grep verified this cycle); `rotation._verify_archive(dest, target)` probes via `run_integrity_check` (`rotation.py:72`) and `verify_domain_identity` (`:78`), both public wrappers that become read-only via companion `20261115-084603_2`.
- The file also carries Plan 006/007/008 test additions later in the batch (006/007 modify existing tests and 008 appends a retention test class — plan overlap record); 004 appends its test near the existing rotation tests and stays disjoint.
- Verification correction (2026-11-15 execution): six `TestRecoverCorruption` tests (`test_dry_run_returns_recovery_result`, `test_dry_run_integrity_failure`, `test_vacuum_path`, `test_no_backup_path_returns_no_backup`, `test_backup_not_found_returns_no_backup`, `test_open_db_exception_returns_error`) mocked `SQLiteHelper` but never created the `tmp_path/rag.sqlite` file — the old write-mode connect silently created it. The existence-first gate now short-circuits all six into `missing_database`. Re-classified as contract churn: the class's autouse `_patch_build_db_config` fixture creates a placeholder rag file (Procedure step 2); each test's mocked-helper semantics are unchanged. Pre-existing mypy baseline on this test file: 7 errors at HEAD and after — unchanged by 004.

## Design decisions
- Probe `_verify_archive` directly instead of a full `rotate_all_dbs` run: the invariance claim is about the probe mutating the archive, so the test isolates the probe on a real archive file without rotation's config/lock surface. The Plan's wording ("after `rotate`...") is satisfied because the archive bytes a rotation leaves behind are exactly the bytes `_verify_archive` sees.

## Alternatives considered
- End-to-end rotate with byte snapshots between copy and verify: rejected — requires a hook inside `rotation.py`; asserting directly on `_verify_archive` proves the same property with no production-code test seams.

## Implementation
### Target file
`tests/db/test_db_maintenance.py`

### Procedure
1. Add `test_verify_archive_leaves_archive_unchanged` (new) in the rotation-test region (near the `:319` class): create a real WAL-mode archive file in `tmp_path`; snapshot `sha256` of its bytes, `os.listdir` of its directory, and `os.stat` mode; call `rotation._verify_archive(archive, "session")` (target matching the fixture's table set); assert sha256, directory listing (no `-wal`/`-shm` entries), and mode are unchanged (REQ-006/AC-1). Landed as an appended module-level test at the end of the file to stay disjoint from later plans' insertions.
2. Re-classify the six `TestRecoverCorruption` mock tests (verification churn): the autouse `_patch_build_db_config` fixture writes a placeholder `rag.sqlite` so the existence-first gate is satisfied and each test reaches its intended mocked-helper path again; no test body or assertion changes.

### Method
- Append one test; follow the file's existing tmp-path + monkeypatched-config fixture style used by the rotation tests.

### Details
- Do not reuse the `_make_session_db` harness if it conflicts with Plan 007's planned `T/Z` timestamp alignment — create the archive file with plain `sqlite3` calls instead (plan overlap record: 004's rotation tests do not use that harness).
- `_verify_archive` raises on failed verification; success path returns nothing — assert absence of mutation, not a return value.

## Compatibility considerations
- Test-only. If a `patch(...)` is added, `check_mock_patch_targets.py` gate applies.

## Security considerations
- N/A: test-only.

## Rollback considerations
- Inside the ro-probes-missing-policy unit: revert with `_2`/`_3`/`_5`. Checkout revert.

## Validation plan
- `uv run pytest tests/db/test_db_maintenance.py -v` → new test green, rotation tests green (AC-1).
- `uv run ruff check tests/db/test_db_maintenance.py` → clean.

## Completion criteria
- A named test proves `_verify_archive` leaves archive bytes, mode, and directory unchanged.

## Out of Scope
- Rotation code edits — none needed (Reference Files row: public wrapper default covers `rotation.py`).
- Other plans' test additions in this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261115-113615 | 20261115-113615 | test: db: maintenance.py: fixture: placeholder: and: archive: test |
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
- **Requirement ID**: REQ-006
- **Source issue**: issues/20261114-092852_dbreview004_integrity-probe-side-effects.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-041859_dbreview004_integrity-probe-side-effects.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-084603
- **Related target files**: tests/db/test_db_maintenance.py