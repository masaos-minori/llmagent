## Goal
Create the `workflow.sqlite` migration registry `scripts/db/migrations_workflow.py` (new): the domain-specific home where future workflow version steps register, built on the shared framework, and decide the string-version to integer-code mapping the Plan defers (REQ-001 migration framework, REQ-009 registered paths preserve rows).

## Scope
- In scope: registry construction for the `workflow` domain — a `REGISTRY` (new) collection of `MigrationSpec` entries from row 01's framework, the version-code map for `WORKFLOW_SCHEMA_VERSION`, and a ledger-bootstrap step (new) that adds the `schema_migrations` table to an existing workflow database that only has the legacy `workflow_schema_version` string log.
- Out of scope: ledger DDL in the workflow DDL set (row 09), create-path baseline (row 08), CLI (row 07).

## Assumptions
- `workflow.sqlite` has no `PRAGMA user_version` stamp today: its version marker is the `workflow_schema_version` TEXT table (`scripts/db/schema_sql.py:214-217`) written by `_record_workflow_schema_version` (`scripts/db/create_schema.py:53-78`), and a string mismatch raises the "recreate the database" refusal (`create_schema.py:75-78`). The integer ledger therefore maps string versions to codes; the Plan's ledger contract (`schema_migrations(id, applied_at, from_version, to_version)`) stays integer-keyed for both domains.
- Version-code mapping (Plan UNK-02, decided here): `WORKFLOW_VERSION_CODES = {"1.1.0": 0}` (new). The integer ledger code is a namespace separate from the string marker: a legacy database with no ledger is code 0 and after bootstrap it is code 1, so the bootstrap step moves `0 -> 1` (the framework rejects a `from == to` step as a cycle). A string absent from this map cannot be migrated (refusal), keeping today's fail-closed semantics. Mirrors `WORKFLOW_SCHEMA_VERSION = "1.1.0"` (`scripts/db/schema_sql.py:25`). Needs confirmation: none — this reserves only the baseline code; a future workflow schema change registers its step here. Confirm against the current workflow backlog before implementation.
- Backup verification for the gate is a callable wrapping `scripts/db/recovery.py::_backup_is_usable` (row 10 exposes it) plus the workflow domain-identity check (required table `tasks`; `_REQUIRED_TABLE_BY_DOMAIN` in `recovery.py:136-139` has no `workflow` entry today, so this registry supplies the workflow-specific check).

## Design decisions
- Registry is a module-level ordered spec collection consumed by the create path (row 08) and the CLI (row 07); same shape as row 02's eventbus registry.
- The bootstrap step `workflow_ledger_baseline` (new) is itself a registered, gate-gated migration `0 → 1`: precondition — `PRAGMA user_version` is at the pre-ledger baseline (0) and the latest `workflow_schema_version.version` maps to a known code; mutation — ledger DDL (identical to row 01/09 contract) plus `PRAGMA user_version = 1`; the runner records the baseline row `(id='workflow_ledger_baseline', from_version=0, to_version=1)` via `record_applied` (the mutation inserts no row itself); postcondition — `user_version` is at the target (1) and the baseline row landed. The string log stays as the compatibility marker (Plan Assumption: `WORKFLOW_SCHEMA_VERSION` remains the baseline marker). The ledger code is `0 → 1` rather than the originally-planned `1 → 1` because the shared runner rejects a `from == to` step as a cycle; the logical version (1.1.0) is unchanged, only the ledger position moves from absent to present.

## Alternatives considered
- Using `PRAGMA user_version` for workflow as eventbus does — originally rejected (existing workflow databases have `user_version 0` and the string table is the deployed marker; introducing a second marker would fork the source of truth, Plan Risk "version fragmentation"). Adopted in a bounded form here: the bootstrap stamps `user_version` to the ledger code (0 → 1) so the shared runner's version tracking works, while the `workflow_schema_version` string remains the sole schema-version marker. The two markers serve distinct purposes (ledger position vs schema version), so they do not conflict.

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261030-110000 | 20261030-110000 | Created scripts/db/migrations_workflow.py: REGISTRY with workflow_ledger_baseline step (0 -> 1), WORKFLOW_VERSION_CODES map (fail-closed), verify_backup + ensure_baseline. NOTE: implemented 0 -> 1, not the planned 1 -> 1, because the shared runner rejects a from==to step as a cycle. The logical schema version (1.1.0) is unchanged; only the ledger position moves absent -> present. Bootstrap stamps PRAGMA user_version=1 so the runner's version tracking works; the string log stays the schema marker. |
| 2 | Add or update tests per Validation plan | Completed | 20261030-110000 | 20261030-110000 | Tests come from row 17 Formal coverage is row 17 (tests/db/test_migrations_workflow.py), not yet generated. Hand smoke test validated: legacy -> migrated bootstrap writes schema_migrations + baseline row (0->1) + stamps user_version=1 while preserving the 1.1.0 string marker and tasks rows; re-apply resolves to [] (idempotent); unmapped string (9.9.9) refused; ensure_baseline (create path) stamps user_version=1. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261030-110000 | 20261030-110000 | ruff format+check clean; mypy(445) clean; lint-imports 6/6 KEPT; check_db_separation no violations; check_docstrings OK (268 grandfathered). Formal pytest suite from row 17 pending. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261030-110000 | 20261030-110000 | N/A for this row N/A: no docs/00_index.md task-scope mapping for migrations_workflow.py. |

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