# Implementation Procedure: scripts/db/schema_sql.py

## Goal

Add the `tool_call_state` (new) and `execution_snapshots` (new) tables to the workflow schema so
interrupted tool calls have durable per-task lifecycle state (REQ-007 workflow lifecycle
tables; input to REQ-008 replay detection).

## Scope

**In scope:**
- `scripts/db/schema_sql.py`: two new `CREATE TABLE` statements in the workflow schema
  section (`:172-214` region) and the version bump handled through the dbmig001 ledger.

**Out of scope:**
- The migration step registration lives in the dbmig001 registry wiring — this plan's
  Phase 4 is gated on dbmig001 Phases 1-2 landing (`plans/done/20261029-214108_dbmig001_forward-only-db-migrations.md` rows 01-02); row 06 writes the DDL into the canonical
  schema template only.
- State read/write helpers (row 07).

## Assumptions

- Baseline stamp: dbmig001 registry head after its own steps is expected to be 4; this
  step takes 5. Needs Confirmation of the actual head at implementation time (read the
  registry, do not assume).
- `WORKFLOW_SCHEMA_VERSION = "1.1.0"` (`:25`) is the create-fresh constant; the plan's
  ledger rule (dbmig001) governs whether this constant is bumped for additive tables —
  follow the dbmig001 procedure docs (rows 01/06 of that plan), which this plan sequences
  before this row.
- `tasks.idempotency_key` UNIQUE (`:179` region) stays as-is (REQ-010): the new tables
  key on the tool-call idempotency key, not the task key.

## Design decisions

- `tool_call_state` (new): `idempotency_key TEXT PRIMARY KEY`, `task_id TEXT NOT NULL`,
  `tool TEXT NOT NULL`, `state TEXT NOT NULL CHECK(state IN
  ('pending','completed','failed','interrupted'))`, `retry_class TEXT NOT NULL`,
  `snapshot_id TEXT`, `created_at REAL NOT NULL`, `updated_at REAL NOT NULL`; index on
  `(task_id, state)` for the turn-entry pending query (row 07).
- `execution_snapshots` (new): `snapshot_id TEXT PRIMARY KEY` (hash of the canonical snapshot
  JSON), `snapshot_json TEXT NOT NULL`, `recorded_at REAL NOT NULL`. FK:
  `tool_call_state.snapshot_id REFERENCES execution_snapshots(snapshot_id)` stays inside
  `workflow.sqlite` (ADR-008 cross-DB FK rule respected — both tables live here).
- DDL goes into the same workflow schema template string the existing `tasks`/`attempts`
  tables use so fresh-create and migrated DBs converge (dbmig001 equivalence test guards
  this).

## Alternatives considered

- Storing tool-call state inside `tasks`/`attempts` columns — rejected: one task spans
  many tool calls; REQ-008 needs per-call pending detection without task-row churn.
- Putting the tables in `mcp_dedup.sqlite` — rejected: pending detection is task-scoped
  and lives with workflow persistence (UNK-02 keeps the dedup store standalone).

## Implementation
### Target file
`scripts/db/schema_sql.py`

### Procedure
1. Append the two `CREATE TABLE IF NOT EXISTS` statements (plus the index) to the workflow
  schema template after the existing tables (`:172-214` region).
2. Handle the version/ledger stamp via the dbmig001 registry wiring (reference, not a
  second edit target of this document).

### Method
DDL-only edit; no Python logic changes in this module beyond any constant the dbmig001
framework requires at the same landing (per its procedure docs, followed verbatim).

### Details
- Column names/vocabulary mirror `scripts/shared/mcp_dedup.py` states (row 02) so the
  row-07 helpers map 1:1 between the stores.

## Compatibility considerations

- Existing workflow DBs gain tables only through the registered forward migration
  (dbmig001 harness); no destructive change; `tests/db/test_create_schema.py` (dbmig001
  row 18) and the equivalence harness confirm fresh-vs-migrated identity.

## Security considerations

- `snapshot_json` (new) holds hashes + hashes of hashes only; no tool payloads stored here.

## Rollback considerations

- Forward-only policy (dbmig001): a rolled-back deployment leaves the tables present but
  unused (row 07/08 gone); no DROP path is provided or needed.

## Validation plan

- `uv run pytest tests/db/test_migrations_workflow.py tests/db/test_create_schema.py`
  (dbmig001-owned harness extended by its rows 17/18 with the step-5 case).
- `uv run python tools/check_db_separation.py` — new tables must be registered in its
  `TABLE_OWNERSHIP` under `workflow` per that tool's "update together with the ADR"
  instruction; the registration edit belongs to the dbmig001-owned rows, not this file
  (Needs Confirmation at implementation time).

## Completion criteria

- Fresh `workflow.sqlite` contains both tables + index; a v-4 baseline DB migrates to the
  new stamp with rows preserved; fingerprint equivalence passes; checker green.

## Out of Scope

- Turn-entry semantics (rows 07-09); `mcp_dedup.sqlite` (row 02, UNK-02 standalone).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the DDL additions | Pending | — | — | Gated: dbmig001 rows 01-02 landed first |
| 2 | Confirm migration-step tests exist in the dbmig001 harness (extension, not this file) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | dbmig001 Phases 1-2 not yet implemented (plan Blocker Log dependency) | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-007` (workflow lifecycle tables), `REQ-008` (persistence input)
- **Source issue**: `issues/20261029-104503_toolexec001_idempotent-tool-call-snapshot.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-233524_toolexec001_idempotent-tool-call-snapshot.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-102825
- **Related target files**: scripts/db/schema_sql.py
