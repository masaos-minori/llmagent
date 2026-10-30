## Goal

Expose the integrity-check and backup-usability helpers of `scripts/db/recovery.py` for reuse by the drills without changing recovery behavior (`REQ-002`, verified recovery points; `REQ-007`, drills).

## Scope

- Modify only `scripts/db/recovery.py`.

## Assumptions

- Verified (Step 3a): `_run_integrity_check` (`:90`), `_verify_domain_identity` (`:142`), and `_backup_is_usable` (`:165`) are private, and about 65 test sites patch `db.recovery._run_integrity_check` or `_verify_domain_identity`; renaming them would break those patch targets, so they stay.
- Plan caveat found (Step 3a, non-blocking `Needs confirmation`): the Plan says the domain-identity helper supports all four targets, but `_REQUIRED_TABLE_BY_DOMAIN` maps only `rag` and `session`; `workflow` and `eventbus` pass through unconstrained and `tests/db/test_db_recovery.py` pins that. This row does not extend the map (that would change behavior); the drill (row 11) checks workflow and eventbus identity by its own required-table check.
- Planned compatibility with `tools/check_compat_shims.py`: the new public functions are first-class API for a second caller, not aliases kept for old callers. Execution order follows the Plan's `Implementation steps` phases (this row is in Phase 4), not necessarily the table `seq`.
- Names that `tools/stale_detector.py` flags in this document are created by other rows of this Plan (the framework row 01 and the domain, drill, and schema rows it names) and exist when `code-implementation` executes the rows in Plan phase order.

## Design decisions

- Add two small public functions that call the existing private helpers: `check_db_integrity` (new)(db_path, target) and `verify_backup` (new)(backup, target) returning `_backup_is_usable`'s result.
- Leave every private helper and every existing call site unchanged.

## Alternatives considered

- Rename the helpers to public names: rejected, about 65 patch sites would change for no behavior gain.
- Import the private helpers from the drill: rejected, cross-module access to underscore names.

## Implementation

### Target file

`scripts/db/recovery.py`

### Procedure

1. Add the two functions near the helpers they wrap, each with a one-line docstring.

### Method

- The wrappers resolve the private helper at call time (module global lookup), so existing `patch("db.recovery._run_integrity_check")` still reaches them.

### Details

- `db.recovery` is already imported by `db.maintenance`; check `rg "recovery import" scripts` before adding names to `__all__` if one exists.

## Compatibility considerations

- No behavior change: only additions.

## Security considerations

- N/A: wrappers add no input boundary.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/db/test_db_recovery.py tests/db/test_db_maintenance.py -v` (unchanged behavior)
- `uv run ruff format scripts/db/recovery.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`

## Completion criteria

- Both wrappers exist, every existing recovery test passes unmodified, and `check_compat_shims.py` reports clean.

## Out of Scope

- Extending `_REQUIRED_TABLE_BY_DOMAIN`, renaming helpers, and drill logic.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the public wrappers | Pending | — | — | Plan Phase 4 |
| 2 | Add or update tests per Validation plan | Pending | — | — | Existing `tests/db/test_db_recovery.py` regression; wrapper coverage in the row 19 document |
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
- **Related target files**: scripts/db/recovery.py
