## Goal
Make `scripts/db/rotation.py` archives verified recovery points: after each SQLite backup-API copy, run the exposed integrity and domain-identity checks and abort the rotation when an archive fails them (REQ-002 verified recovery points, REQ-007 drill precondition).

## Scope
- In scope: `_archive_db_file` in `scripts/db/rotation.py` and the verification it performs on every archive produced by `rotate_session_db`, `rotate_workflow_db`, `rotate_eventbus_db`, `rotate_db`, `rotate_all_dbs` (`rotation.py:51-86`).
- Out of scope: archive destination/timestamp conventions, recovery flow (row 10 exposes the helpers), drill harness (row 11).

## Current shape (facts)
- `_archive_db_file` (`rotation.py:24-48`) opens source and destination with `sqlite3.connect`, calls `src.backup(dst)`, logs size, and returns the path. No integrity or domain check runs on the produced file — the Plan's "archives without verification" anchor.
- All four databases are archived through this one function, so the verification belongs inside it, not in each `rotate_*` wrapper.

## Assumptions
- Verification uses row 10's exposed helpers: `recovery.run_integrity_check(dest, target)` plus `recovery.verify_domain_identity(dest, target)`; same-layer import (`db` → `db`) is allowed by `.importlinter`.
- Failure semantics: a failed check raises with the helper's detail (the rotation aborts, remaining archives are not produced by `rotate_all_dbs`). The failed archive file is left in place for forensics; the exception names its path. This is the intended new failure mode (Plan Design: unverified recovery points are a defect, not a warning).
- Domain identity today constrains only `rag`/`session` (required tables in `recovery.py:136-139`); `workflow`/`eventbus` pass through identity and are covered by their integrity result plus, for `eventbus`, no fingerprint gate here — the deeper shape gates live in rows 02/03/04/11. Adding new identity tables would change recovery semantics, out of this row.

## Design decisions
- Add a `target: str` keyword to `_archive_db_file` supplied by every wrapper (`"rag"`, `"session"`, `"workflow"`, `"eventbus"`) so the helpers receive the correct domain; public `rotate_*` signatures stay unchanged.
- Verification runs after `dst.close()`/`src.close()` (the backup API copy is only queryable once closed) and before the success log line.

## Alternatives considered
- Verifying only on drill time (row 11) and leaving archives unchecked — rejected: the Plan makes the archive itself the verified recovery point; a drill discovering a bad archive weeks later is too late.

## Implementation
### Target file
- `scripts/db/rotation.py`

### Procedure
1. Add `target` keyword to `_archive_db_file`; pass it from all five public callers.
2. After closing the backup handles, run `run_integrity_check` and `verify_domain_identity`; on failure raise `RuntimeError(f"archive verification failed for {dest}: {detail}")`.
3. Keep the success log; extend it with "verified".

### Method
Narrow in-function addition plus a keyword threading through existing wrappers.

### Details
- Import the row-10 public wrappers at module top (`from db.recovery import ...`); this creates a `rotation` → `recovery` dependency inside the `db` layer — allowed, and it is the reuse the issue asked for.

## Compatibility considerations
- Callers gain a new failure mode: previously a corrupt archive silently "succeeded". `tests/db/test_db_maintenance.py` is the Plan's named regression file for this row and is extended there (that file is an existing test module, not a separate Plan target row — the extension is part of this row's landing).
- `rotate_db`/`rotate_all_dbs` return shapes unchanged.

## Security considerations
- No new input surface; archive paths come from config (`agent.toml sqlite_archive_dir`, `rotation.py:15-21`).

## Rollback considerations
- Revert the commit; archives produced under the verified path remain valid inputs for restore either way.

## Validation plan
- `uv run pytest tests/db/test_db_maintenance.py` extended with: archive verification success, corrupt-source injection (tmp fixture) aborts with detail, and `rotate_all_dbs` ordering behavior on failure.
- `uv run mypy --no-namespace-packages scripts/`; `lint-imports`.

## Completion criteria
- Every produced archive path has passed `PRAGMA integrity_check` (and domain identity where defined) before the function returns; a failing archive raises before any later archive is attempted.

## Out of Scope
- Ledger/fingerprint gates on archives (rows 02/04/11), drill artifacts (row 11), deploy wiring (row 13).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261030-140000 | 20261030-140000 | Added keyword-only `target: str` to `_archive_db_file`; runs `_verify_archive` (integrity + domain identity) after the backup handles close and before the success log; extended the log with "verified". Threaded `target` through all five public callers (`rotate_session_db`, `rotate_workflow_db`, `rotate_eventbus_db`, `rotate_all_dbs`, `rotate_db`) plus the row-11 drill caller. New `target` is keyword-only so callers must name the domain. |
| 2 | Add or update tests per Validation plan | Completed | 20261030-140000 | 20261030-140000 | Extended existing tests/db/test_db_maintenance.py: `_make_real_sqlite` now emits the rag/session required tables so archives pass identity; added TestArchiveVerification (5 tests) covering healthy-archive integrity, missing-required-table abort, injected integrity abort, and rotate_all_dbs mid-sequence abort with ordering assertion. 59/59 pass. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261030-140000 | 20261030-140000 | ruff format+check clean; mypy clean; lint-imports 6/6 KEPT; check_db_separation no violations; check_docstrings OK (268 grandfathered). |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261030-140000 | 20261030-140000 | N/A: rotation prose lives in rows 22/23, outside this row's scope. This row only adds runtime verification; no doc update required here. |

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
- **Requirement ID**: `REQ-002` (verified recovery points), `REQ-007` (drill)
- **Source issue**: `issues/20261029-104500_dbmig001_forward-only-db-migrations.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-214108_dbmig001_forward-only-db-migrations.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-071336
- **Related target files**: `scripts/db/rotation.py`
