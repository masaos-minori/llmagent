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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Gated: issues/20261119-145303_cliplc005_staged-reload-transaction.md phase all - the typed-candidate model is defined by that Issue; coordination dependency, either order works |
| 2 | Add or update tests per Validation plan | Pending | — | — | Gated: same - assertions live in Plan row 26 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Gated: same - shared surface must be re-verified after that Issue lands |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Gated: same - the maintenance documentation row is Plan row 30 |

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
