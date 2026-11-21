## Goal

Remove `scripts/db/`'s own `agent.toml` load: the maintenance dataclasses are constructed from caller-injected typed configuration, and the checkpoint-mode default comes from that injected configuration (REQ-004, AC-004, AC-005).

## Scope
**Release unit**: RU-2

## Assumptions
- `tests/db/test_db_maintenance.py` is not a companion of this row: it is named by three rows, so it keeps its own document (Plan row 26).
- The dataclasses stay defined inside `scripts/db/` because the `.importlinter` `db-only-uses-shared` contract forbids importing `agent` types (the Plan's Design D2).
- `DbMaintenanceConfig` (new) is the single typed maintenance configuration this Plan requires (REQ-004): it groups the retention, corrupt-archive, drill-artifact, quarantine, and checkpoint settings that `config/agent.toml` currently exposes as separate top-level keys.

## Design decisions
- `from_config()` factory methods are replaced by explicit typed construction from a supplied mapping; the field-level validation and the key-naming `ValueError` messages stay, because the existing tests assert them and the behaviour is preserved.
- `checkpoint_wal()` keeps its explicit-mode behaviour; when no mode is passed it reads the mode from the injected typed configuration instead of loading `agent.toml`.
- The single `ConfigLoader` import is removed from this module, which is what makes AC-004 true for `scripts/db/`.

## Alternatives considered
- Keep `_load_agent_config()` as a private helper that takes the mapping: rejected — it would keep a config-source dependency inside `db/` and the row's stated responsibility is to remove it.

## Implementation
### Target file
`scripts/db/maintenance.py`
### Procedure
- Delete `_load_agent_config()` (line 95) and the `shared.config_loader.ConfigLoader` import.
- Define `DbMaintenanceConfig` (new) here and change `RetentionConfig.from_config()` and `CorruptArchiveRetentionConfig.from_config()` to take the injected typed configuration.
- `checkpoint_wal()` (line 177) resolves its default mode from the injected configuration when no mode argument is given.
### Method
- `_non_negative_int()` and `_retention_guard()` keep their semantics; they are applied to values from the injected configuration instead of a loaded mapping.
- Validation uses `shared.config_utils.get_typed`, the pattern the Plan's Reference Files require to be preserved.
### Details
- Verified 2026-11-21: `checkpoint_wal()` loads `agent.toml` through `_load_agent_config()` when the mode is absent, and `tests/db/test_db_maintenance.py` patches `db.maintenance.ConfigLoader` for that behaviour — those assertions move with Plan row 26.
- The pre-existing `nosec` warning in this module is unchanged by this row.

## Compatibility considerations
- `scripts/db/artifact_retention.py` imports `_load_agent_config` from this module (Plan row 14); removing it here requires that row to land in the same release unit.
- Config-load failures propagate in both BEST_EFFORT and strict modes per `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md`; with injection there is no load failure in `db/`, so the documented exception applies to the caller that constructs the typed configuration (Plan row 16).

## Security considerations
- N/A: no trust-boundary change.

## Rollback considerations
- N/A: revert the commit within release unit RU-2 (the factory contract is shared with its call sites and tests).

## Validation plan
- `uv run pytest tests/db/test_db_maintenance.py -v`
- `uv run python tools/check_db_separation.py`
- `uv run ruff check scripts/db/maintenance.py`, `uv run mypy scripts/db/maintenance.py`
- `PYTHONPATH=scripts uv run lint-imports`

## Completion criteria
- No `ConfigLoader` use remains in `scripts/db/maintenance.py`; every maintenance value used by the module comes from the injected typed configuration; retention and checkpoint behaviour is unchanged for the same values.

## Out of Scope
- Who constructs the typed configuration (Plan row 16), the call-site updates (Plan rows 8, 13, 14, 17, 18), the test rewrite (Plan row 26).

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
- **Requirement ID**: REQ-004 (typed maintenance configuration injected by callers)
- **Source issue**: issues/20261120-114212_agentcfg004_config-ownership-split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-140444_agentcfg004_config-ownership-split.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-144837
- **Related target files**: `scripts/db/maintenance.py`
