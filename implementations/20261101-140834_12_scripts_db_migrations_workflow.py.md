## Goal

Register the `tasks.idempotency_key` → `task_nonce` (new) rename as a new `workflow.sqlite` migration step in `scripts/db/migrations_workflow.py` (Plan REQ-004, AC-4).

## Scope

- New `MigrationSpec` entry `workflow_task_nonce` (new) appended to `REGISTRY` (currently `migrations_workflow.py:246-263`): `from_version=2`, `to_version=3`.
- `WORKFLOW_VERSION_CODES` (`:42`) gains the new string-version → `3` pairing (`{"1.1.0": 0, "1.2.0": 2, "1.3.0": 3}` if this Plan's step lands first) and `WORKFLOW_TARGET_VERSION` (`:48`) becomes `3`.

## Assumptions

- Current ledger head is code `2` (`workflow_tool_call_state`, landed 2026-11-01); the code string pairing follows landing order, exactly as done for code 2 (`1.2.0`) — the paired `WORKFLOW_SCHEMA_VERSION` string comes from row 04 and must match `schema_sql.py` at commit time.
- Plan overlap judgment (re-recorded): wflease001/wfrecovery001 each plan to add their own registry step and will take code 4+ at their landing time; only one Plan at a time may occupy code 3 (Plan Risks: version-string collision).

## Design decisions

- Mirror the `workflow_tool_call_state` spec shape (`:255-262`): `preconditions` guard the source state, `mutation_sql` performs the schema change plus version restamp, `postcondition` asserts the end state — the registry is the only sanctioned mutation path (shared `MigrationRunner`, `shared.db_migrations`).

## Alternatives considered

- Editing the baseline `tasks` DDL only and letting `create_schema.py` handle existing databases: rejected — `create_schema.py:54-77` refuses version mismatch on an existing database; a registered step is mandatory (REQ-004).

## Implementation
### Target file
`scripts/db/migrations_workflow.py`

### Procedure
1. Add `_TASK_NONCE_VERSION: int = 3` and `_TASK_NONCE_MUTATION_SQL` (new): `ALTER TABLE tasks RENAME COLUMN idempotency_key TO task_nonce;` followed by `DELETE FROM workflow_schema_version; INSERT INTO workflow_schema_version (version) VALUES ('<new WORKFLOW_SCHEMA_VERSION>'); PRAGMA user_version = 3;` (same fixed-constant f-string pattern as `_TOOL_STATE_MUTATION_SQL` at `:112-117`, with the `# nosec B608` justification comment).
2. Add `_precondition_task_nonce(conn)`: refuse unless `tasks` exists, `tasks` still has `idempotency_key` (idempotent refusal with a clear message if already `task_nonce` (new)), and `PRAGMA user_version == 2` — shape mirrors `_precondition_tool_state` (`:190-214`).
3. Add `_postcondition_task_nonce(conn)`: assert `tasks` has `task_nonce` (new) and not `idempotency_key`, `user_version == 3`, and the `workflow_schema_version` latest row equals the new `WORKFLOW_SCHEMA_VERSION` — mirrors `_postcondition_tool_state` (`:231-242`).
4. Append `"workflow_task_nonce": MigrationSpec(id="workflow_task_nonce", from_version=2, to_version=3, preconditions=(_precondition_task_nonce,), mutation_sql=_TASK_NONCE_MUTATION_SQL, postcondition=_postcondition_task_nonce)` to `REGISTRY` after `workflow_tool_call_state`.
5. Bump `WORKFLOW_VERSION_CODES` and `WORKFLOW_TARGET_VERSION` (`:42,48`).

### Method
One new spec block + registry append + constant bump in a single commit with rows 01-04.

### Details
- Row-count preservation is asserted by the rename step's tests (row 09, AC-4): a database seeded at code 2, migrated to 3, keeps every `tasks` row with identical `task_id`/`task_nonce` (new) values (`RENAME COLUMN` never touches values).
- `ensure_baseline` (`shared.db_migrations` usage in this module) stamps fresh databases at head; a freshly created database at the new `WORKFLOW_SCHEMA_VERSION` must not run this step (precondition refuses `user_version != 2`).

## Compatibility considerations

- `scripts/agent/services/workflow_schema.py:110-118` and `create_schema.py:54-77` accept the new version once `schema_sql.py` (row 04) carries the matching constant; deploy path `deploy/init_db.sh` calls the migration CLI and needs no change.
- Forward-only policy: no downgrade spec is added (Plan Risks).

## Security considerations

- Mutation SQL is built from fixed module constants only; keep the `# nosec B608` suppression with the existing justification format (bandit must stay at 0 findings).

## Rollback considerations

- Reverting this row requires reverting row 04's version constant in the same commit; a deployed database already at code 3 cannot be downgraded by this registry (forward-only), so rollback before deployment only (Plan Rollback).

## Validation plan

- Row 09's added migration test (`tests/db/test_create_schema.py`): migrate a code-2 fixture to head and compare table shapes/values against a fresh-created database (AC-4).
- `uv run pytest tests/db/ -v`; `uv run python tools/check_db_separation.py`; `uv run bandit -r scripts/db -q` (0 findings).

## Completion criteria

- `rg workflow_task_nonce scripts/db/migrations_workflow.py` shows the registered step; migrated and fresh databases converge on identical `tasks` shape at the new version; existing rows preserved (AC-4).

## Out of Scope

- Lease/attempt DDL changes (wflease001) and recovery-state changes (wflease001/wfrecovery001) register their own later registry steps.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan (row 09's migration test) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-004`
- **Source issue**: issues/20261030-105723_wftaskapi001_consolidate-task-persistence.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-113553_wftaskapi001_consolidate-task-persistence.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-140834
- **Related target files**: scripts/db/migrations_workflow.py
