## Goal

Verify each archived file in `scripts/db/rotation.py` so an archive becomes a verified recovery point (`REQ-002`, verified backups; `REQ-007`, drills depend on it).

## Scope

- Modify only `scripts/db/rotation.py`.

## Assumptions

- Verified (Step 3a): `_archive_db_file` creates the copy with the SQLite backup API and returns the path without checking it; `rotate_all_dbs`, `rotate_session_db`, `rotate_workflow_db`, and `rotate_eventbus_db` all go through it (`tests/db/test_db_maintenance.py` covers them, about 8 references).
- `rotation.py` already imports from `db.config`; importing `check_db_integrity` from `db.recovery` must not create an import cycle (`recovery.py` imports `db.helper`, not `rotation`; confirm with `rg "rotation" scripts/db/recovery*.py`). Execution order follows the Plan's `Implementation steps` phases (this row is in Phase 4, after row 10), not necessarily the table `seq`.
- Names that `tools/stale_detector.py` flags in this document are created by other rows of this Plan (the framework row 01 and the domain, drill, and schema rows it names) and exist when `code-implementation` executes the rows in Plan phase order.

## Design decisions

- After the backup copy, run `check_db_integrity` on the archive; a non-healthy result raises `RuntimeError` naming the archive and the detail, and the bad archive file is removed (it is this call's own file) so no unverified file stays in the archive directory.

## Alternatives considered

- Verify inside the drill only: rejected, the Plan wants every archive to be a verified recovery point, not only drill archives.

## Implementation

### Target file

`scripts/db/rotation.py`

### Procedure

1. Call the verification at the end of `_archive_db_file`, using the target name derived from the database file stem.

### Method

- Keep the function signature and return value; only add the check and its error.

### Details

- A failed verification now raises where it used to silently keep a corrupt archive: callers in `scripts/db/maintenance.py` and the tests must be read for `except` handling before the change.

## Compatibility considerations

- Behavior change is limited to a corrupt archive, which was a latent defect.

## Security considerations

- Deletes only the file created by this call.

## Rollback considerations

- Revert the commit.

## Validation plan

- `uv run pytest tests/db/test_db_maintenance.py tests/db/test_db_recovery.py -v`
- `uv run ruff format scripts/db/rotation.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`

## Completion criteria

- Every archive returned by `rotate_*` has passed `PRAGMA integrity_check`; a corrupt archive raises and is not left behind.

## Out of Scope

- Retention, scheduling, and the drill (row 11).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add post-archive verification | Pending | — | — | Plan Phase 4; after row 10 |
| 2 | Add or update tests per Validation plan | Pending | — | — | Existing `tests/db/test_db_maintenance.py` must pass unmodified; the corrupt-archive case is covered in the row 19 document (a target file) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — |  |

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
- **Requirement ID**: REQ-002, REQ-007
- **Source issue**: issues/20261029-104500_dbmig001_forward-only-db-migrations.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261029-214108_dbmig001_forward-only-db-migrations.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-151746
- **Related target files**: scripts/db/rotation.py
