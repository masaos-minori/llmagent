## Goal

Resolve the archive directory from the injected typed maintenance configuration instead of loading `agent.toml` inside `scripts/db/` (REQ-004, AC-004, AC-005).

## Scope
**Release unit**: RU-2

## Assumptions
- `tests/db/test_db_maintenance.py` is not a companion of this row (it is named by three rows) and keeps its own document (Plan row 26); `tests/db/test_recovery_drill.py` is run as an affected test and is not a target row.
- The hardcoded fallback for an absent `sqlite_archive_dir` stays, because the behaviour is preserved per the Issue's AI Implementation Instruction.

## Design decisions
- `_resolve_archive_dir()` takes the typed maintenance configuration defined by Plan row 9 as its argument; the hardcoded default remains the documented fallback for an absent key.

## Alternatives considered
- N/A: single-function change, no alternative that keeps the import-layer contract.

## Implementation
### Target file
`scripts/db/rotation.py`
### Procedure
- Remove the `ConfigLoader().load("agent.toml")` call (line 18) and the `shared.config_loader` import.
- `_resolve_archive_dir()` reads `sqlite_archive_dir` from the injected typed configuration (Plan row 9's `DbMaintenanceConfig` (new)).
- Keep the `build_db_config()` call sites working with the new signature defined by Plan row 8.
### Method
- Argument-based read, no new module-level state; `rotate_all_dbs()` scope is unchanged (Session and Workflow only; RAG is not rotated) per the Plan's Design D5 and UNK-03.
### Details
- Verified 2026-11-21: `scripts/db/artifact_retention.py` and `scripts/db/recovery_drill.py` import `_resolve_archive_dir` from this module; they are separate procedure rows.
- Finding (2026-11-21, execution): `_archive_db_file()` needs the typed configuration to apply the fallback, so it gained a `maintenance: DbMaintenanceConfig` keyword argument; the procedure did not state this because it only covered `_resolve_archive_dir()`. The four `rotate_*` entry points take `db_cfg` (row 8's `DbConfig`) and `maintenance` as arguments, matching the release unit's injected-configuration contract.
- Finding (2026-11-21, execution): the `build_db_config()` patch targets in `tests/db/test_db_maintenance.py` (lines 783, 1377, 1509) become invalid because this module no longer calls `build_db_config`; the tests supply `DbConfig` directly. Recorded in Plan row 26.

## Compatibility considerations
- The function is used by CLI entry points; those receive the typed configuration at their entry boundary (Plan rows 13, 14).

## Security considerations
- N/A: no trust-boundary change.

## Rollback considerations
- N/A: revert the commit within release unit RU-2.

## Validation plan
- `uv run pytest tests/db/test_db_maintenance.py tests/db/test_recovery_drill.py -v`
- `uv run python tools/check_db_separation.py`
- `uv run ruff check scripts/db/rotation.py`, `uv run mypy scripts/db/rotation.py`

## Completion criteria
- No `ConfigLoader` use remains in `scripts/db/rotation.py`; the archive directory for the same configured value is unchanged.

## Out of Scope
- Definition of the typed maintenance configuration (Plan row 9), the CLI entry boundary (Plan row 13), test changes (Plan row 26).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-21 | 2026-11-21 | Implemented; _resolve_archive_dir(maintenance) plus _archive_db_file(maintenance=) keyword argument; rotate_* take db_cfg+maintenance. ruff/mypy clean. Tests are row 26. |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-22 | 2026-11-22 | Assertions landed with Plan row 26. _resolve_archive_dir(maintenance) is also covered through the entry boundary by tests/deploy/test_init_db_schema_gate.py. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-22 | 2026-11-22 | Gate (issue not landed) - execution proceeded under the plan scope. Batch-end validation: ruff and mypy clean on scripts/, lint-imports 6 contracts kept, docs checkers pass for the touched domains, full suite green (13258 passed). |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-11-22 | 2026-11-22 | Documentation landed with Plan row 30. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|---|---|---|---|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-004 (the archive directory comes from the injected typed configuration)
- **Source issue**: issues/20261120-114212_agentcfg004_config-ownership-split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-140444_agentcfg004_config-ownership-split.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-144837
- **Related target files**: `scripts/db/rotation.py`
