## Goal

Rename the `tasks.idempotency_key` column in the workflow DDL and bump `WORKFLOW_SCHEMA_VERSION` in `scripts/db/schema_sql.py` (Plan REQ-003 DDL rename, REQ-004 version bump).

## Scope

- `idempotency_key TEXT UNIQUE NOT NULL` in the `tasks` table DDL (currently `schema_sql.py:191`) becomes `task_nonce TEXT UNIQUE NOT NULL`.
- `WORKFLOW_SCHEMA_VERSION = "1.2.0"` (currently `:27`) becomes the new string version assigned by landing order (row 12 registers the matching ledger code; if this Plan's step lands first it is `"1.3.0"`).

## Assumptions

- Current head state re-verified 2026-11-01: version `1.2.0` at `:27` (the Plan's original cites `:25` / `1.1.0` were pre-toolexec001); the `tasks` DDL key column is at `:191`.
- Plan overlap judgments (re-recorded): compatible with ragcorpus001 (`schema_sql.py` adds `rag_corpus_meta` only) and with toolexec001 (already landed as ledger code 2); the version string must not collide with a later wflease001/wfrecovery001 step — each takes the next code in landing order.

## Design decisions

- The DDL text and the version constant change in the same commit as the migration registration (row 12) and the code rename (rows 01-03): `scripts/db/create_schema.py:54-77` and `scripts/agent/services/workflow_schema.py:110-118` refuse a database whose recorded version differs from the constant (Plan Design: Migration).

## Alternatives considered

- Dropping the redundant unique column instead of renaming: rejected by Plan UNK-03 (SQLite 3.46.1 needs a table rebuild for `DROP COLUMN` of a UNIQUE column); a drop is a later separate change.

## Implementation
### Target file
`scripts/db/schema_sql.py`

### Procedure
1. In the `tasks` table template, rename the column at `:191` to `task_nonce` (new) (keep `TEXT UNIQUE NOT NULL`).
2. Bump `WORKFLOW_SCHEMA_VERSION` at `:27` to the version string paired with row 12's ledger code.
3. Reword the REQ-010 comment at `:227` — it currently reads
   `REQ-010: tasks.idempotency_key stays as-is` and names the task key, so it
   must drop the tasks reference and keep only the `tool_call_state`
   `idempotency_key` statement (the `tool_call_state` DDL at `:237` stays
   untouched). The historical `TASKS_DDL_V1` block (from the
   `workflow_tool_call_state` migration era) stays as-is.

### Method
Two-text edit in one commit with rows 01-03 and 12.

### Details
- The fresh-database path (`create_schema.py`) must create the renamed column; a fresh database is stamped at the new version.
- The migrated-database path is row 12; both must end in identical table shapes (the registry's postcondition fingerprint compares them).

## Compatibility considerations

- `tests/db/test_create_schema.py` carries a copy of the DDL (row 09) and `deploy/init_db.sh` checks tables by name only (unaffected, Plan Reference Files).
- `tools/check_db_separation.py` table ownership is by name, unaffected by a column rename.

## Security considerations

- N/A: constraint semantics unchanged (UNIQUE NOT NULL preserved by `RENAME COLUMN`).

## Rollback considerations

- A version bump without a registered migration breaks a retained `workflow.sqlite` at startup — revert of this row must be paired with row 12's registry revert (Plan Risks); forward-only policy means deployed databases are migrated forward, never downgraded.

## Validation plan

- `uv run pytest tests/db/ -v` (row 09 adds the migration test; AC-4).
- `uv run python tools/check_db_separation.py` passes after the DDL change.
- Fresh-create + migrate-existing equivalence is proven by row 12's registry test and row 09.

## Completion criteria

- Fresh databases are created with `task_nonce` (new) at the new version string; the version constant differs from `1.2.0`; `rg task_nonce scripts/db` shows the DDL; no downgrade or unregistered path is accepted (AC-3, AC-4).

## Out of Scope

- Migration step registration (row 12); attempt/lease DDL changes belong to wflease001.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Verification Notes (2026-11-01)
- Passed. `WORKFLOW_SCHEMA_VERSION = "1.2.0"` at `:27`, tasks DDL key column
  at `:191` confirmed. Version string for this batch is `1.3.0` (ledger code
  3, paired with row 12); no other pending batch has landed since.
- Additional edit found during verification: the REQ-010 comment at `:227`
  names `tasks.idempotency_key` and is folded into Procedure step 3.

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-003` (DDL rename), `REQ-004` (version bump with registered migration)
- **Source issue**: issues/20261030-105723_wftaskapi001_consolidate-task-persistence.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-113553_wftaskapi001_consolidate-task-persistence.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-140834
- **Related target files**: scripts/db/schema_sql.py
