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
- Finding (2026-11-22, execution): Procedure 1 was not carried out as written. The service does not construct `DbMaintenanceConfig`; construction happens at the single ownership point in `agent.config_builders.build_agent_config()`, and `DbMaintenanceService.__init__(db_config, maintenance)` receives the already-built typed objects. The row's Goal is still met — `scripts/db/` receives the values from the Agent side — but through injection at the ownership point rather than construction in this module.
- Finding (2026-11-22, execution): the per-call retention override is resolved by `_resolve_retention()`, which keeps the caller-supplied `RetentionConfig` when one is given and otherwise projects the effective policy from the injected typed configuration. `checkpoint()` resolves the effective mode once and reports that same value, which is the behaviour the Details section required. `recover_corruption()` is called as `recover_corruption(self._db_config, backup_path, target="session")`; `db_config` is the first positional parameter, so call sites must use the keyword form for `target`.

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
| 1 | Implement the change described in Implementation > Procedure/Method | Completed | 2026-11-22 | 2026-11-22 | Implemented under the gate: the constructor takes DbConfig and DbMaintenanceConfig from the owning process and reads no configuration file. |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-22 | 2026-11-22 | N/A: no test file for this module; covered by the affected tests (tests/agent/services/test_rag_maintenance_persistence.py, test_agent_factory.py), which are green. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-22 | 2026-11-22 | $V |
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
- **Requirement ID**: REQ-004 (the configuration owner constructs the typed configuration and injects it)
- **Source issue**: issues/20261120-114212_agentcfg004_config-ownership-split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-140444_agentcfg004_config-ownership-split.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-144837
- **Related target files**: `scripts/agent/services/db_maintenance_service.py`
