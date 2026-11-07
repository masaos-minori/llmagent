## Goal

- Strip ledger/baseline/version stamping from `scripts/db/create_schema.py` while keeping its fail-closed rejection and EventBus fingerprint gate, so fresh databases are created with the current schema only (REQ-002: remove ledger/baseline stamping from the schema layer; REQ-003: current-schema-only creation).

## Scope
**Release unit**: current-schema-only-cutover

- Import and call-site removals plus deletion of the `workflow_schema_version` stamping block in this file only; the DDL it stamps into is removed by sibling document 08.

## Assumptions

- `ensure_ledger` / `ensure_baseline` disappear with siblings 01/02 in the same Phase 2 commit; this file must not be left importing deleted modules at any commit boundary.
- Persisted-schema checklist item 4 (Plan Design): ledger DDL and ledger write paths ship in one release unit so no intermediate state writes into removed tables.

## Design decisions

- Keep the `assert_matches` / `validate_canonical` fingerprint gate and existing fail-closed `RuntimeError` behavior unchanged (Plan row: "keep fail-closed rejection and fingerprint gate").
- After deletion, creating a workflow database performs current-shape DDL only: no version row, no ledger row, no baseline call (REQ-002 / AC-002).

## Alternatives considered

- Keeping `WORKFLOW_SCHEMA_VERSION` import for logging: rejected — the constant is deleted from `schema_sql.py` by document 08 (REQ-002).

## Implementation
### Target file
`scripts/db/create_schema.py`

### Procedure
1. Phase 1 sibling (document 18) rewrites `tests/db/test_create_schema.py` expectations; confirm RED against current behavior.
2. In the Phase 2 commit, remove the ledger/baseline imports and call sites and the version-stamping block (steps below); confirm document 18's tests green.

### Method
- Remove the import `from shared.db_migrations import ensure_ledger` (line 25) and `from db.migrations_workflow import ensure_baseline` (line 29), plus their call sites (`ensure_ledger(...)` / `ensure_baseline(...)` in the workflow/eventbus creation paths).
- Remove `WORKFLOW_SCHEMA_VERSION` from the `from db.schema_sql import (...)` block (line 31 group).
- Remove the workflow version-row stamp block in `create_workflow_schema` (currently lines 65-80 region): the `SELECT version FROM workflow_schema_version ORDER BY applied_at DESC LIMIT 1` read, the `INSERT INTO workflow_schema_version (version) VALUES (?)` write, and the mismatch `RuntimeError` branch built on it.

### Details
- Keep the EventBus path: `assert_matches` / `validate_canonical` import (line 26 group) and its fail-closed usage remain; the eventbus stamp comes from canonical `schema.sql` only (sibling document 09).
- No other function signatures change.

## Compatibility considerations

- `deploy/init_db.sh` invokes `create_schema.py`; the deploy gate inversion is sibling document 12 (Phase 3).

## Security considerations

- N/A: no new input handling; removal only reduces write paths.

## Rollback considerations

- Revert the commit restores the ledger/baseline wiring (single-commit change within the release unit).

## Validation plan

- `uv run pytest tests/db/test_create_schema.py` — fresh 4-DB set has no `schema_migrations` / `workflow_schema_version` and no baseline rows; fail-closed paths intact (Plan Validation plan row).
- `uv run python tools/check_db_separation.py` — clean.
- Whole-unit gates run in Plan Phase 5 per `rules/toolchain.md`.

## Completion criteria

- A freshly created workflow/eventbus database contains no marker tables and no version/ledger rows (AC-002), and creation against an incompatible database still refuses without writing (REQ-004).

## Out of Scope

- `schema_sql.py` DDL removal — sibling document 08.
- EventBus startup gate rework — sibling document 07.
- `deploy/init_db.sh` gate inversion — sibling document 12.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm document 18 (companion-side test rewrite) is RED (Plan Phase 1) | Pending | — | — | Release unit "current-schema-only-cutover" |
| 2 | Remove ledger/baseline imports, call sites, and version-stamp block (Plan Phase 2) | Pending | — | — | |
| 3 | Run `uv run pytest tests/db/test_create_schema.py` green | Pending | — | — | |
| 4 | Run the validation sequence (`rules/toolchain.md`) in the Phase 5 unit pass | Pending | — | — | |

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
- **Requirement ID**: REQ-002 (remove ledger/baseline stamping from the schema layer), REQ-003 (current-schema-only creation)
- **Source issue**: issues/20261106-125142_compatrm001_remove-db-migration-and-enforce-current-schema-startup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-061846_compatrm001_remove-db-migration-and-enforce-current-schema-startup.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-081028
- **Related target files**: `scripts/db/create_schema.py`
