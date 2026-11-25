## Goal
Add the `args_hash` (new) column to the canonical `tool_call_state` DDL so the persisted
tool-call row carries the canonical argument hash that replay-directive reconstruction needs.

## Scope
**Release unit**: persisted directive store

## Assumptions
- `args_hash` is `NOT NULL` with no default; the sole writer of the table populates it in the
  same release unit (`rules/persisted-schema-change.md` item 4).
- Current-schema-only policy (compatrm001): no migration step is registered for this column.

## Design decisions
- Plain column addition to the existing DDL string; `tool_call_state` has no foreign keys, so no
  rebuild is required (`rules/persisted-schema-change.md` item 3).

## Alternatives considered
- Nullable column with a default — rejected: `rules/persisted-schema-change.md` item 4 requires the
  writer to populate a `NOT NULL` column in the same unit, and a default would let rows carry an
  empty hash that directive matching cannot use.

## Implementation
### Target file
`scripts/db/schema_sql.py`

### Procedure
Add one column to the `tool_call_state` DDL emitted by `build_workflow_schema_sql()`.

### Method
Insert `args_hash TEXT NOT NULL` in the column list, after `retry_class`, keeping the existing
column alignment style of the DDL string.

### Details
- The DDL header comment above the table states that this file is the single canonical definition;
  extend it to name `args_hash` as the field directive reconstruction reads.
- No index change: directive reconstruction queries by `(task_id, state)`, already covered by
  `idx_tool_call_state_task_state`.

## Compatibility considerations
The shape gate compares databases against the canonical DDL by exact fingerprint, so existing
databases with the old column set are refused and must be archived and recreated by the operator.
`tests/db/test_create_schema.py` asserts only `snapshot_id` absence on this table, so it is not
broken by the addition (reference row).

## Security considerations
N/A: no trust boundary changes; the column stores a hash already computed at preparation.

## Rollback considerations
Revert the commit; databases created after it carry the column and must be recreated to match the
rolled-back DDL.

## Validation plan
- `uv run pytest tests/db/test_create_schema.py` — fresh scratch database carries `args_hash`.
- `uv run python tools/check_db_separation.py` — table ownership unchanged (`rules/tool-gates.md`).
- `uv run python tools/check_module_size.py` — `scripts/db/schema_sql.py` stays under the gate.

## Completion criteria
A freshly created workflow database exposes `args_hash` as a `NOT NULL` column, and the existing
shape-gate tests still refuse the pre-change shape.

## Out of Scope
No migration or version-store step; no change to `mcp_dedup.sqlite` tables.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the `args_hash` column to the canonical DDL | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 3 | Run the path-keyed gates (`rules/tool-gates.md`) | Pending | — | — | check_db_separation, check_module_size |

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
- **Requirement ID**: `REQ-006` (directives survive a restart through the persisted row)
- **Source issue**: `issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261125-105505_mcpai004_logical-idempotency-key-replay.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-112546
- **Related target files**: `scripts/db/schema_sql.py`
