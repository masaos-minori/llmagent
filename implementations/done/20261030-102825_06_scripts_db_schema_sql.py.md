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

- Baseline stamp (verified 2026-10-31 against landed dbmig001 code): the workflow ledger
  head is 1 — `WORKFLOW_TARGET_VERSION = 1` and a single registered step
  `workflow_ledger_baseline` (0 -> 1) in `scripts/db/migrations_workflow.py:40-46,139-148`.
  This row's migration step registers 1 -> 2 with a new string code, mirroring the
  dbmig001 row-06 rule "a future workflow schema change registers its step here"
  (`implementations/done/20261030-071336_06_scripts_db_migrations_workflow.py.md`).
- Scope finding (verified 2026-10-31): the 1 -> 2 registration edits
  `scripts/db/migrations_workflow.py` (REGISTRY, WORKFLOW_VERSION_CODES,
  WORKFLOW_TARGET_VERSION), table ownership registration edits
  `tools/check_db_separation.py` `TABLE_OWNERSHIP["workflow"]` (`:68-77`), and the step-2
  test extension edits `tests/db/test_migrations_workflow.py`. All three are outside this
  procedure's target file and outside the plan's 21-row target table. Owner approved
  2026-10-31: all three edits (plus bumping `WORKFLOW_SCHEMA_VERSION` to `"1.2.0"` in
  this row) are authorized additional targets of the row 06 cycle.
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

- Fresh `workflow.sqlite` contains both tables + index; a v-1 (post-bootstrap) baseline DB
  migrates 1 -> 2 with rows preserved; fingerprint equivalence passes; checker green.

## Out of Scope

- Turn-entry semantics (rows 07-09); `mcp_dedup.sqlite` (row 02, UNK-02 standalone).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the DDL additions | Completed | 20261031-165500 | 20261031-171452 | `execution_snapshots` + `tool_call_state` + `idx_tool_call_state_task_state` appended to the workflow template (columns exactly per Design decisions; `snapshot_id` FK inside workflow.sqlite, no FK on `task_id` per the design enumeration); `WORKFLOW_SCHEMA_VERSION` bumped to `"1.2.0"` (owner-approved). Registered step `workflow_tool_call_state` (1 -> 2) in `migrations_workflow.py` with the DDL duplicated byte-identically (dlqbox001 precedent) + marker replacement (`DELETE` + `INSERT`: the marker readers resolve "latest" by `applied_at` at one-second granularity, so a same-second second row would be ambiguous; delete+insert keeps a single latest row and the create path's fail-closed check accepts migrated DBs) + `PRAGMA user_version = 2`. Ledger constants restructured to the eventbus pattern (`_LEDGER_VERSION=1` for the bootstrap stamp, `_TOOL_STATE_VERSION=2` head, `WORKFLOW_VERSION_CODES` gains `"1.2.0": 2`). Fresh-create stamp moved to head code 2 (ensure_baseline), matching `dlq_outbox` fresh-stamp-5 precedent. `check_db_separation.py` `TABLE_OWNERSHIP["workflow"]` extended (owner-approved) |
| 2 | Confirm migration-step tests exist in the dbmig001 harness (extension, not this file) | Completed | 20261031-165500 | 20261031-171452 | Test-first extension of `tests/db/test_migrations_workflow.py` (owner-approved): new `TestWorkflowToolCallStateStep` class (migrate+preserve+marker, resume-empty, forged-stamp refusal via missing baseline row, already-present-tables refusal, fresh-vs-migrated convergence incl. `PRAGMA table_info` equality); bootstrap-isolated existing tests via `target_version=1`; `_legacy_workflow_db` drops the lifecycle tables to reproduce the pre-step shape; CLI asserts updated to head version 2. Out-of-table characterization adjustments recorded here: `tests/db/test_create_schema.py` fresh-create stamp assert 1 -> 2; `tests/deploy/test_init_db_eventbus_schema.py` sandbox pinning bug fixed — the appended `workflow_db_path` landed inside the trailing `[tool_definitions.*]` table section so the subprocess had been falling back to the production workflow DB (silent until the 1.2.0 refusal exposed it; key is now prepended top-level) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261031-171452 | 20261031-171452 | Gates fast-mode all Pass (after `generate_reference_table.py --manifests` refreshed the stale `db_schema_versions.yaml` manifest from the version bump); lint-imports 6 kept (new sibling import `db.schema_sql` in `migrations_workflow.py` stays inside the db contract family); ruff format/check clean; mypy green on the 3 touched scripts files; bandit: 1 new Medium B608 from the step's f-string SQL suppressed with `# nosec B608 - fixed module constants, no user input`, back to the 3-issue master baseline; targeted 106 passed; full suite 10728 passed / 8 skipped; diff-cover 92% >= 90. Production note: `/opt/llm/db/workflow.sqlite` is at ledger 1 (marker 1.1.0); the next deploy must run `db/migrate_db.py --apply` to reach 2 (forward-only, rows preserved) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | dbmig001 Phases 1-2 not yet implemented (plan Blocker Log dependency) | Yes | 2026-10-31 |
| 1 | Additional-target-file finding (migrations_workflow.py / check_db_separation.py / test_migrations_workflow.py edits outside scope) | Yes | 2026-10-31 |
| 1 | `scripts/db/migrate_db.py` CLI preflight evaluated every step's precondition against the current DB state, so a multi-step chain always refused at the second step. Owner decision 2026-10-31 (live approval): authorized as a fourth additional target; minimal fix = preflight evaluates only the chain-first step, later steps delegate to `apply()`'s per-step preconditions (same behavior as the eventbus CLI) | Yes | 2026-10-31 |

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
