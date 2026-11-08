## Goal
Extend `REQUIRED_WORKFLOW_TABLES` in the startup schema gate to include `tool_call_state` with its
DDL-mirrored required columns, so a workflow database lacking that table is refused at startup
instead of failing at the first tool-call state insert in production (`REQ-001`, `REQ-003`).

## Scope
**Release unit**: wfaudit003-full (Phase 1)

- Covers Plan `plans/20261108-084006_wfaudit003_schema-gate-table-gap.md` row 1 only:
  `scripts/agent/services/workflow_schema.py`, plus its gate tests in
  `tests/agent/test_repl_health.py`.
- No DDL change (`scripts/db/schema_sql.py` is read-only reference), no shell mirrors (procedures
  `144827_02`/`144827_03`), no docs (procedures `144827_04`–`144827_07`).

## Assumptions
- Post-`wfaudit010` table set is final: the workflow DDL creates five tables (`tasks`, `attempts`,
  `processed_events`, `artifacts`, `tool_call_state`); `execution_snapshots` is retired and must not
  enter the required list.
- The gate stays presence-only (missing table/column refusal): extra tables or columns in a live
  database still pass. Legacy databases created since `tool_call_state` was introduced already
  contain it and keep passing (plan `UNK-01` production probe is a Phase 3 rollout gate, not a
  code dependency of this procedure).
- `tool_call_state` DDL is unchanged by `wfaudit002` (its Out-of-Scope row excludes DDL changes to
  the table), so the column list below is stable.

## Design decisions
- Single dict entry addition: `check_workflow_schema()`'s existing loop already validates per-table
  required columns (`workflow_schema.py` L121-135), so no control-flow change is needed.
- Required columns mirror the DDL (`scripts/db/schema_sql.py` L229-237, built by
  `build_workflow_schema_sql()` L267): `idempotency_key` (PRIMARY KEY), `task_id`, `tool`, `state`,
  `retry_class`, `created_at`, `updated_at` — the same all-columns convention the gate already
  applies to `processed_events` and `artifacts`.
- Refusal message templates are reused unchanged (`workflow_schema.py` L125 missing-table, L134
  missing-column), keeping one consistent operator-facing error shape.

## Alternatives considered
- Exact table-set equality in the gate: rejected — it would refuse legacy databases carrying
  harmless extra tables and contradicts the presence-only gate semantics established by the
  no-migration policy (`compatrm001`).
- Requiring `execution_snapshots`: rejected — retired by `wfaudit010` (commit `4e46f5958`); a fresh
  `create_workflow_schema()` database would then be refused by its own gate (`REQ-003` violation).

## Implementation
### Target file
`scripts/agent/services/workflow_schema.py` — `REQUIRED_WORKFLOW_TABLES` dict (L46-58).

### Procedure
Add one entry to `REQUIRED_WORKFLOW_TABLES` after the `"artifacts"` entry. No other edit in the
module; `LEGACY_MARKER_TABLES` (L63) and `LEGACY_MARKER_REFUSAL_MESSAGE` (L65-70) stay as-is.

### Method
Insert into the dict:

```python
"tool_call_state": [
    "idempotency_key",
    "task_id",
    "tool",
    "state",
    "retry_class",
    "created_at",
    "updated_at",
],
```

### Details
- The gate loop (L121-135) then refuses a database missing `tool_call_state` with
  `Workflow schema missing table 'tool_call_state'. Run create_workflow_schema() to initialize.`
  and a database missing any listed column with the existing missing-column message naming
  `tool_call_state.<col>`.
- Caller `scripts/agent/startup_component_init.py` (`_check_workflow_schema` L140-144) raises
  `RuntimeError` on `result.error` unchanged — no caller edit required.

## Compatibility considerations
- Databases built by `create_workflow_schema()` since `tool_call_state` was introduced already
  satisfy the new entry; only gap-shaped databases (the issue's failure mode) newly fail, which is
  the intended behavior.
- The gate remains read-only (opens with `write_mode=False`, L101); no database is ever modified.

## Security considerations
- No new inputs, secrets, or network surface; the gate only reads `sqlite_master` and
  `PRAGMA table_info`.

## Rollback considerations
- Reverting the dict entry fully restores prior behavior; nothing is persisted or migrated. Shell
  mirrors and docs (procedures 02-07) must be reverted together with this entry — the lists are
  pinned equal by `144827_02`'s parity test.

## Validation plan
- Extend `tests/agent/test_repl_health.py` fixture `_create_workflow_db` (L521-568): add a
  `tool_call_state` entry to its `schemas` dict with the seven columns above so existing
  `TestCheckWorkflowSchema` pass-cases keep passing.
- Add tests (new) to `TestCheckWorkflowSchema`:
  - `test_missing_tool_call_state_table_fails` (new) — `_create_workflow_db(tmp_path,
    exclude_table="tool_call_state")`; assert `result.valid is False` and the error names
    `tool_call_state` (`REQ-005`).
  - `test_missing_tool_call_state_column_fails` (new) — `missing_column=("tool_call_state",
    "retry_class")`; assert the error names `tool_call_state.retry_class`.
  - `test_fresh_schema_created_database_passes` (new) — build a DB via
    `sqlite3.executescript(build_workflow_schema_sql())` (import `build_workflow_schema_sql` from
    `db.schema_sql`), then assert `check_workflow_schema(db_path=...).valid is True` (`REQ-003`
    round-trip; fails on HEAD only if the gate list is extended without the fixture being derived
    from the canonical DDL — it pins the post-`wfaudit010` shape).
- New gate tests fail on HEAD (fresh DB missing `tool_call_state` currently passes) and pass after.
- Targeted: `uv run pytest tests/agent/test_repl_health.py tests/agent/test_startup_component_init.py -q`;
  then `uv run pytest tests/agent/ tests/deploy/ -q`; full `uv run pytest tests/ -q` and lint/type
  gates per `rules/toolchain.md`.

## Completion criteria
- `REQUIRED_WORKFLOW_TABLES` contains exactly five entries: `tasks`, `attempts`,
  `processed_events`, `artifacts`, `tool_call_state`.
- The three new tests pass; all pre-existing `TestCheckWorkflowSchema` cases pass unchanged
  (legacy-marker refusal semantics preserved).
- Full suite green; ruff/mypy clean on the changed files.

## Out of Scope
- `deploy/init_db.sh` and `deploy/setup_services.sh` list mirrors (procedures `144827_02`,
  `144827_03`).
- All doc corrections (procedures `144827_04`–`144827_07`).
- DDL changes, version identifiers, migration paths, and the Phase 3 production probe (plan
  operational step).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Docs are covered by procedures 04-07 |

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
- **Requirement ID**: `REQ-001`, `REQ-003`, `REQ-005`
- **Source issue**: `issues/20261107-203216_wfaudit003_schema-gate-table-gap.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084006_wfaudit003_schema-gate-table-gap.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-144827
- **Related target files**: `scripts/agent/services/workflow_schema.py`, `tests/agent/test_repl_health.py`
