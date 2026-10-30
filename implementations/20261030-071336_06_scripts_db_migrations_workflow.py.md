## Goal
Create the `workflow.sqlite` migration registry `scripts/db/migrations_workflow.py` (new): the domain-specific home where future workflow version steps register, built on the shared framework, and decide the string-version to integer-code mapping the Plan defers (REQ-001 migration framework, REQ-009 registered paths preserve rows).

## Scope
- In scope: registry construction for the `workflow` domain — a `REGISTRY` (new) collection of `MigrationSpec` entries from row 01's framework, the version-code map for `WORKFLOW_SCHEMA_VERSION`, and a ledger-bootstrap step (new) that adds the `schema_migrations` (new) table to an existing workflow database that only has the legacy `workflow_schema_version` string log.
- Out of scope: ledger DDL in the workflow DDL set (row 09), create-path baseline (row 08), CLI (row 07).

## Assumptions
- `workflow.sqlite` has no `PRAGMA user_version` stamp today: its version marker is the `workflow_schema_version` TEXT table (`scripts/db/schema_sql.py:214-217`) written by `_record_workflow_schema_version` (`scripts/db/create_schema.py:53-78`), and a string mismatch raises the "recreate the database" refusal (`create_schema.py:75-78`). The integer ledger therefore maps string versions to codes; the Plan's ledger contract (`schema_migrations(id, applied_at, from_version, to_version)`) stays integer-keyed for both domains.
- Version-code mapping (Plan UNK-02, decided here): `WORKFLOW_VERSION_CODES = {"1.1.0": 1}` (new) and `WORKFLOW_TARGET_VERSION = 1`, mirroring `WORKFLOW_SCHEMA_VERSION = "1.1.0"` (`scripts/db/schema_sql.py:25`). A string not in the map cannot be migrated (refusal), keeping today's fail-closed semantics. Needs confirmation: this row reserves only baseline code 1; if a workflow schema change is pending, its step must register here (planned registry contents: baseline step only). Confirm against the current workflow backlog before implementation.
- Backup verification for the gate is a callable wrapping `scripts/db/recovery.py::_backup_is_usable` (row 10 exposes it) plus the workflow domain-identity check (required table `tasks`; `_REQUIRED_TABLE_BY_DOMAIN` in `recovery.py:136-139` has no `workflow` entry today, so this registry supplies the workflow-specific check).

## Design decisions
- Registry is a module-level ordered spec collection consumed by the create path (row 08) and the CLI (row 07); same shape as row 02's eventbus registry.
- The bootstrap step `workflow_ledger_baseline` (new) is itself a registered, gate-gated migration `1 → 1`: precondition — latest `workflow_schema_version.version` maps to a known code and no ledger exists; mutation — ledger DDL following the Plan's column contract, in the shape row 09 appends to `_WORKFLOW_SCHEMA` and row 01's `ensure_ledger` (new) creates, plus a baseline row `(id='workflow_ledger_baseline', from_version=1, to_version=1)`; postcondition — ledger present and latest string maps to `WORKFLOW_TARGET_VERSION`. The string log stays as the compatibility marker (Plan Assumption: `WORKFLOW_SCHEMA_VERSION` remains the baseline marker).

## Alternatives considered
- Using `PRAGMA user_version` for workflow as eventbus does — rejected: existing workflow databases have `user_version 0` and the string table is the deployed marker; introducing a second marker would fork the source of truth (Plan Risk "version fragmentation").

## Implementation
### Target file
- `scripts/db/migrations_workflow.py` (new)

### Procedure
1. Import `MigrationSpec` from `shared.db_migrations`; define `REGISTRY` (new), `WORKFLOW_VERSION_CODES` (new), `WORKFLOW_TARGET_VERSION` (new).
2. Register `workflow_ledger_baseline` per Design.
3. Export `verify_backup(backup_path, target)` (new): wraps `db.recovery._backup_is_usable(backup_path, "workflow")` and adds the `tasks`-table domain check.
4. Export `ensure_baseline(conn)` (new) used by row 08's create path: creates the ledger if absent and inserts the baseline row idempotently.

### Method
New module inside the `db` layer; may import `shared` and sibling `db` modules (`.importlinter` `db-only-uses-shared` contract family). SQL text mirrors row 09's ledger DDL so baseline-created and migrated databases are shape-identical; land after rows 01 and 09 in `seq` order.

### Details
- `MigrationSpec`/`MigrationRunner` are created by row 01; this document assumes they exist when executed in `seq` order.
- No content steps beyond baseline; future workflow steps (e.g. dlqbox001 outbox lands in eventbus, not here) append to `REGISTRY`.
- `current_version` for the runner is derived by the caller (row 07 CLI): the latest `workflow_schema_version.version` string mapped through `WORKFLOW_VERSION_CODES` (new); an unmapped string is an UNKNOWN_PATH refusal raised before the gate.
- Needs confirmation: row 01's `plan` resolves forward paths and refusal classes but does not define same-version semantics; the `workflow_ledger_baseline` `1 → 1` step must resolve as a registered path when the ledger is absent (not as a no-op or self-cycle refusal). Pin this down with row 01 during implementation.

## Compatibility considerations
- Existing workflow databases keep working through `_record_workflow_schema_version` unchanged; the ledger is additive. `create_schema.py` refusal semantics (row 08 keeps them intact) must keep refusing unmapped strings.

## Security considerations
- Static SQL authored in-repo only; no user input paths.

## Rollback considerations
- Revert the commit; nothing references this module until rows 07/08 land.

## Validation plan
- `uv run pytest tests/db/test_migrations_workflow.py` (row 17 writes these tests first).
- `lint-imports`; `uv run mypy --no-namespace-packages scripts/`.

## Completion criteria
- A workflow database with only the legacy string log ends with a `schema_migrations` table, a `workflow_ledger_baseline` row, and the unchanged `workflow_schema_version` marker; an unmapped or mismatched string version is refused, never migrated.

## Out of Scope
- Ledger DDL in the workflow DDL set (row 09), create-path wiring (row 08), CLI (row 07), eventbus domain (rows 02/04/05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Tests come from row 17 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A for this row |

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
- **Requirement ID**: `REQ-001` (migration framework), `REQ-009` (registered paths preserve rows)
- **Source issue**: `issues/20261029-104500_dbmig001_forward-only-db-migrations.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-214108_dbmig001_forward-only-db-migrations.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-071336
- **Related target files**: `scripts/db/migrations_workflow.py`
