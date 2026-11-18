## Goal
State the EventBus retention rule in the schema comments (`REQ-006`); comment only.

## Scope
**Release unit**: N/A: not part of a release unit
- In scope: standalone `--` comment lines before the `events`, `consumer_delivery`, and `dlq_outbox` statements; no DDL.

## Assumptions
- Comments are stripped before the shared fingerprint is computed, so the fingerprint does not change (checked in Step 3a).
- The `dlq_outbox` comment already says `done` rows are retained as the durable generation record.
- Procedure 02 has landed: ADR-008 Decision Detail #23 exists.

## Design decisions
- One comment line per table, placed on its own line above the statement, never inside a statement.

## Alternatives considered
N/A: the maintainer's decisions are recorded in the Plan's Design section.

## Implementation
### Target file
`scripts/eventbus/schema.sql`

### Procedure
1. Above `CREATE TABLE IF NOT EXISTS events` add: `-- Retention: no row is deleted automatically; growth is an accepted risk (ADR-008 Decision Detail #23).`
2. Add the same one-line statement above `consumer_delivery`; extend the existing `dlq_outbox` comment with the same sentence.
3. Compare the three fingerprints recorded by procedure 11 with the values computed now.

### Method
- Use the existing comment style of the file; English only.

### Details
- Run `uv run python tools/check_db_separation.py`; `scripts/eventbus/schema.sql` is read at runtime by `build_eventbus_schema_sql()`.

## Compatibility considerations
N/A: documentation or comment text only.

## Security considerations
N/A: no approval statement is written or simulated; pending bullets only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_db_separation.py`, `uv run pytest tests/eventbus/ tests/db/test_create_schema.py tests/tools/test_check_db_separation.py`, and the fingerprint comparison.

## Completion criteria
- The comments state the retention rule; the three fingerprints equal the recorded ones; the checks pass.

## Out of Scope
- Any DDL, the `dlq_outbox` behavior.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the retention comments and compare the fingerprints (Implementation > Procedure) | Pending | — | — | |
| 2 | Add or update tests per Validation plan: no test change needed; run the existing tests | Pending | — | — | |
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
- **Requirement ID**: REQ-006
- **Source issue**: issues/20261117-123008_adrchk008_db-data-lifecycle.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-142957_adrchk008_db-data-lifecycle.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-143801
- **Related target files**: `scripts/eventbus/schema.sql`
