## Goal

`ArtifactRetentionConfig` is constructed from the injected typed configuration, and the indirect `agent.toml` import through `db.maintenance` is removed (REQ-004, AC-004, AC-005).

## Scope
**Release unit**: RU-2

## Assumptions
- `tests/db/test_db_maintenance.py` is not a companion of this row: it is named by three rows, so it keeps its own document (Plan row 26).
- This module is the consumer the source Issue did not name; it was found by re-verification and recorded in the Plan's Background.

## Design decisions
- `from_config()` is replaced by typed construction from the injected configuration (the same shape Plan row 9 defines for the retention and corrupt-archive dataclasses), so `scripts/db/` has no config source of its own.

## Alternatives considered
- Keep importing `_load_agent_config` from `db.maintenance`: rejected — that keeps an `agent.toml` read inside `scripts/db/` through an indirect import, which AC-004 forbids.

## Implementation
### Target file
`scripts/db/artifact_retention.py`
### Procedure
- Remove the `_load_agent_config` import from `db.maintenance` (line 27).
- Change `ArtifactRetentionConfig.from_config()` (line 55) to accept the injected typed configuration.
- Keep the `_resolve_archive_dir()` call (line 336) working with the signature defined by Plan row 10.
### Method
- Per-class caps and age rules are read from the injected configuration; the deletion behaviour and the `0 disables the rule` semantics are unchanged.
### Details
- Verified 2026-11-21: `tests/db/test_db_maintenance.py` has drill-artifact boundary tests that call `ArtifactRetentionConfig.from_config()` directly; those move to the injected-configuration shape in Plan row 26.

## Compatibility considerations
- `db.maintenance`'s purge helpers call `ArtifactRetentionConfig.from_config()`; the call sites change together in the same release unit.

## Security considerations
- N/A: no trust-boundary change.

## Rollback considerations
- N/A: revert the commit within release unit RU-2.

## Validation plan
- `uv run pytest tests/db/test_db_maintenance.py -v` (drill-artifact rows)
- `uv run python tools/check_db_separation.py`
- `uv run ruff check scripts/db/artifact_retention.py`, `uv run mypy scripts/db/artifact_retention.py`

## Completion criteria
- No `ConfigLoader` or `_load_agent_config` use remains in this module; the same configured caps produce the same deletions.

## Out of Scope
- Definition of the typed configuration (Plan row 9), the caller-side construction (Plan row 16), test changes (Plan row 26).

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
- **Requirement ID**: REQ-004 (typed maintenance configuration injected by callers)
- **Source issue**: issues/20261120-114212_agentcfg004_config-ownership-split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-140444_agentcfg004_config-ownership-split.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-144837
- **Related target files**: `scripts/db/artifact_retention.py`
