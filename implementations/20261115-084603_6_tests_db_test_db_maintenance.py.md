## Goal
- Assert that rotation archive verification leaves the archive untouched.

## Scope
**Release unit**: ro-probes-missing-policy (Phase 3 of the plan; lands with `_2`/`_3`)

- In scope: `tests/db/test_db_maintenance.py` — one rotation-archive invariance test (REQ-006).

## Assumptions
- Rotation tests live in this file (`test_rotate_session_db_creates_archive` at `:319`, `test_rotate_all_dbs_archives_all_three` at `:1049`, etc.; no separate rotation test file — grep verified this cycle); `rotation._verify_archive(dest, target)` probes via `run_integrity_check` (`rotation.py:72`) and `verify_domain_identity` (`:78`), both public wrappers that become read-only via companion `20261115-084603_2`.
- The file also carries Plan 006/007/008 test additions later in the batch (006/007 modify existing tests and 008 appends a retention test class — plan overlap record); 004 appends its test near the existing rotation tests and stays disjoint.

## Design decisions
- Probe `_verify_archive` directly instead of a full `rotate_all_dbs` run: the invariance claim is about the probe mutating the archive, so the test isolates the probe on a real archive file without rotation's config/lock surface. The Plan's wording ("after `rotate`...") is satisfied because the archive bytes a rotation leaves behind are exactly the bytes `_verify_archive` sees.

## Alternatives considered
- End-to-end rotate with byte snapshots between copy and verify: rejected — requires a hook inside `rotation.py`; asserting directly on `_verify_archive` proves the same property with no production-code test seams.

## Implementation
### Target file
`tests/db/test_db_maintenance.py`

### Procedure
1. Add `test_verify_archive_leaves_archive_unchanged` (new) in the rotation-test region (near the `:319` class): create a real WAL-mode archive file in `tmp_path`; snapshot `sha256` of its bytes, `os.listdir` of its directory, and `os.stat` mode; call `rotation._verify_archive(archive, "session")` (target matching the fixture's table set); assert sha256, directory listing (no `-wal`/`-shm` entries), and mode are unchanged (REQ-006/AC-1).

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
- **Requirement ID**: REQ-006
- **Source issue**: issues/20261114-092852_dbreview004_integrity-probe-side-effects.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-041859_dbreview004_integrity-probe-side-effects.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-084603
- **Related target files**: tests/db/test_db_maintenance.py
