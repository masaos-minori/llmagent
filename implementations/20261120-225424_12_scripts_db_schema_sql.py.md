## Goal

Extend the canonical `tool_call_state` DDL `CHECK` to the nine-state intent vocabulary and restate the key-semantics comment (`REQ-005` persisted vocabulary, AC-2, `REQ-010` schema lifecycle).

## Scope
**Release unit**: auth-intent

## Assumptions
- UNK-04: production `/opt/llm/db/workflow.sqlite` rows are discarded by archive-and-recreate at deploy; the startup shape gate (compatrm001 policy) rejects the legacy DB — operator action, no migration code (Plan REQ-010).
- The primary-key column name `idempotency_key` stays; the comment documents that its value is now the opaque uuid7 logical call id.

## Design decisions
- Edit the `state` CHECK at :217 in `scripts/db/schema_sql.py` to `('pending','dispatch_starting','dispatched','response_received','completed','failed','interrupted','outcome_unknown','reconciliation_required')` — identical set to `TOOL_CALL_STATES` (row 9), same commit.
- Update the surrounding comment block (:213-215 region) to state the new key semantics; no index (`idx_tool_call_state_task_state`) change.

## Alternatives considered
- Renaming the key column to `call_id`: rejected — the shape pins, `check_db_separation.py`, and every consumer name `idempotency_key`; value semantics carry the change.

## Implementation
### Target file
`scripts/db/schema_sql.py`

### Procedure
Edit the `CREATE TABLE tool_call_state` block (:215-223) in place.

### Method
DDL text edit only; no migration code — legacy databases are rejected at startup and recreated (create_schema policy).

### Details
- Deploy impact is Yes per the Plan's Affected areas: legacy `workflow.sqlite` is rejected until archived and recreated.

### Companion test files
- `tests/db/test_create_schema.py`
  - Procedure: update the workflow-DDL shape pin for the new CHECK text and comment.
  - Validation: `uv run pytest tests/db/test_create_schema.py` passes.
- `tests/db/test_schema_validation_per_database.py`
  - Procedure: update per-database shape expectations to the new canonical DDL.
  - Validation: `uv run pytest tests/db/test_schema_validation_per_database.py` passes.

## Compatibility considerations
Fresh-created databases are the only accepted databases; scratch-DB shape check per `rules/persisted-schema-change.md` recipe.

## Security considerations
N/A: schema vocabulary only; the vocabulary is what makes `outcome_unknown` storable.

## Rollback considerations
Revert together with row 9 (code vocabulary) — and, if deployed, restore the archived `workflow.sqlite` per the runbook.

## Validation plan
`uv run pytest tests/db tests/deploy/test_required_workflow_tables_parity.py && uv run python tools/check_db_separation.py`.

## Completion criteria
Canonical DDL and `TOOL_CALL_STATES` accept exactly the same nine states; `check_db_separation.py` passes; shape pins updated.

## Out of Scope
Transition semantics (row 10); the parity test's own update (row 32).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Deploy runbook note only |

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
- **Requirement ID**: `REQ-005`, `REQ-010`
- **Source issue**: `issues/20261120-115840_mcpdl001_approval-grant-intent.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-222144_mcpdl001_approval-grant-intent.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-225424
- **Related target files**: `scripts/db/schema_sql.py`, `tests/db/test_create_schema.py`, `tests/db/test_schema_validation_per_database.py`
