## Goal

Make the Agent-side maintenance service the configuration owner: it builds the typed maintenance configuration from Agent-owned settings and passes it to `scripts/db/`, instead of letting `db/` read `agent.toml` (REQ-004, AC-004, AC-005).

## Scope
**Release unit**: RU-2

## Assumptions
- No test file exists for this module; tests run per the Validation plan are the affected tests listed by the Plan's row.
- The typed maintenance configuration type is defined by Plan row 9 in `scripts/db/maintenance.py`; this module constructs it, it does not define it.

## Design decisions
- The service is the boundary where Agent-owned configuration becomes the typed configuration `db/` consumes, which is what the owner/reader map in the Plan's Design D1 requires.
- `checkpoint()` keeps its explicit-mode behaviour; when no mode is given, the mode now comes from the typed configuration it constructs rather than from a `db/`-side load.

## Alternatives considered
- N/A: this module already imports the maintenance dataclasses, so passing the constructed values is the smallest change that satisfies AC-004.

## Implementation
### Target file
`scripts/agent/services/db_maintenance_service.py`
### Procedure
- Construct the typed maintenance configuration (Plan row 9's `DbMaintenanceConfig` (new)) from the Agent configuration this service already has access to.
- Pass it to `RetentionConfig` construction, `purge_old_sessions`, and `checkpoint_wal` instead of relying on their config read.
- Keep the result models (`DbStats`, `DbHealth`, `DbCheckpointResult`) unchanged.
### Method
- Construction at the service boundary; no new validation here — the dataclass validation in Plan row 9 is the single place values are checked.
### Details
- Verified 2026-11-21: `checkpoint()` passes `mode` directly to `checkpoint_wal(db, mode)`, and `mode or "TRUNCATE"` is used only for the reported value; after this row the reported value must match the mode actually used, so the effective mode is resolved once.
- `tests/db/test_db_maintenance.py` line 384 asserts the default mode comes from configuration through a `lambda self, key:` lookup; that assertion is rewritten in Plan row 26, not here.

## Compatibility considerations
- `RetentionConfig.from_config()` disappears per Plan row 9; every call in this module must move to the typed construction, otherwise the module fails at import.

## Security considerations
- N/A: no trust-boundary change.

## Rollback considerations
- N/A: revert the commit within release unit RU-2.

## Validation plan
- `uv run pytest tests/agent/services/ -v` (affected tests)
- `uv run python tools/check_db_separation.py`
- `uv run ruff check scripts/agent/services/db_maintenance_service.py`, `uv run mypy scripts/agent/services/db_maintenance_service.py`
- `PYTHONPATH=scripts uv run lint-imports` (the `agent` → `db` direction is allowed by the import-layer contract)

## Completion criteria
- `scripts/db/` receives the maintenance values from this service; no `from_config()` call and no `agent.toml` read remains reachable through this module.

## Out of Scope
- Definition of the typed configuration (Plan row 9), test changes (Plan row 26), documentation updates (Plan row 30).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method | Pending | — | — | Gated: issues/20261119-145303_cliplc005_staged-reload-transaction.md phase all - the typed-candidate model is defined by that Issue; coordination dependency, either order works |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: no test file exists for this module; covered by Plan row 26. Gated: same as step 1 |
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
- **Requirement ID**: REQ-004 (the configuration owner constructs the typed configuration and injects it)
- **Source issue**: issues/20261120-114212_agentcfg004_config-ownership-split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-140444_agentcfg004_config-ownership-split.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-144837
- **Related target files**: `scripts/agent/services/db_maintenance_service.py`
