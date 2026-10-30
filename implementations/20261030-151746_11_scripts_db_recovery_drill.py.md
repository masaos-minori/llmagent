## Goal

Create the recovery-drill harness in `scripts/db/recovery_drill.py` for all four SQLite domains (`REQ-007`, measured restore time and data-loss window as retained audit artifacts).

## Scope

- Create only `scripts/db/recovery_drill.py`.

## Assumptions

- Depends on rows 10 and 12 (`check_db_integrity`, `verify_backup`, and post-archive verification). Execution order follows the Plan's `Implementation steps` phases (this row is in Phase 4), not necessarily the table `seq`.
- RPO and RTO numeric targets stay open (Plan UNK-01): the drill measures, it does not compare against a target.
- Domain identity for workflow and eventbus is checked here with required tables `tasks` and `events` because `_REQUIRED_TABLE_BY_DOMAIN` in `scripts/db/recovery.py` covers rag and session only (see row 10).
- `DbConfig` (`scripts/db/config.py`) resolves all four paths; `rotate_all_dbs` (`scripts/db/rotation.py`) returns the four archive paths; `scripts/db/recovery_restore.py` has the existing restore staging that the drill must not duplicate.
- Names that `tools/stale_detector.py` flags in this document are created by other rows of this Plan (the framework row 01 and the domain, drill, and schema rows it names) and exist when `code-implementation` executes the rows in Plan phase order.

## Design decisions

- The drill restores into an isolated temporary copy, never the live file (Plan failure-path invariant).
- One JSON artifact per drill run, written under the archive directory, with per-domain `restore_seconds` (new), `data_loss_window_seconds` (new) (drill start time minus the archive file timestamp), `integrity`, `domain_identity` (new), `archive_path` (new), and `ok`.

## Alternatives considered

- Restore through `recover_corruption` against a scratch target: rejected, it is tied to configured live paths.

## Implementation

### Target file

`scripts/db/recovery_drill.py` (new)

### Procedure

1. Add `run_drill` (new)(archive_dir=None, domains=None) returning a result mapping per domain, and `write_artifact` (new)(result, archive_dir).
2. Per domain: rotate to an archive (rotation row 12 verifies it), verify with `check_db_integrity` and `verify_backup`, apply the workflow/eventbus required-table check, copy to a temporary directory and open it read-only, time the copy-and-open, and record the measurements.
3. Add a `main` (new)() CLI entry printing the artifact path.

### Method

- Use `time.monotonic()` for durations and the archive file's embedded timestamp (`format_timestamp` in `scripts/db/config.py`) for the loss window.
- Any domain failure is recorded as `ok: false` with the reason; the run continues to the other domains and the CLI exits non-zero when any domain failed.

### Details

- Archives are produced by `rotate_all_dbs`, which touches all four live databases read-only through the SQLite backup API; the drill therefore runs safely against production files but must be scheduled outside heavy writes (note in the db_07 row 23).

## Compatibility considerations

- New module; no caller until deployment wiring (row 13).

## Security considerations

- Temporary copies are created with `tempfile` in a private directory and removed afterwards; the artifact contains paths and timings only, no row data.

## Rollback considerations

- N/A: revert the commit; retained artifacts are inert files.

## Validation plan

- `uv run pytest tests/db/test_recovery_drill.py -v` (row 19 document)
- `uv run ruff format scripts/db/recovery_drill.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`

## Completion criteria

- `run_drill` (new) produces a verified artifact for each of the four domains with the required measurement fields, restores only into temporary copies, and the CLI exit code reflects failures.

## Out of Scope

- Numeric RPO/RTO targets, drill scheduling, and retention ownership (UNK-01).
- Automatic restore of live databases.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the drill per Procedure | Pending | — | — | Plan Phase 4; after rows 10 and 12 |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by the row 19 document |
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
- **Requirement ID**: REQ-007
- **Source issue**: issues/20261029-104500_dbmig001_forward-only-db-migrations.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261029-214108_dbmig001_forward-only-db-migrations.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-151746
- **Related target files**: scripts/db/recovery_drill.py
