## Goal
- Correct the `dlq_outbox` comment so it names the right direction, without changing any DDL (REQ-005: comment-only fix).

## Scope
**Release unit**: eventbus-supervision-and-cleanup

- In scope: the comment block above `CREATE TABLE IF NOT EXISTS dlq_outbox` in `scripts/eventbus/schema.sql`.

## Assumptions
- The comment says "DLQ->replay promotion requests", but `insert_outbox_row` runs inside the transaction that sets `dlq_at`, so the rows request DLQ artifact generation for events promoted into the DLQ (verified in Step 3a).
- `shared/schema_fingerprint.py` strips `--` comments before comparing, so the structural fingerprint and the shape checks are unchanged; `content_hash` in `db_schema_versions.yaml` hashes the whole file and changes, which the seq 13 document regenerates (verified in Step 3a).
- ADR-008 Decision Details 23 is the recorded lifecycle decision; this edit touches no DDL, so the issue's constraint on DDL changes is respected.

## Design decisions
- Change only the wording of the first comment sentence; keep the worker and retention sentences as they are.

## Alternatives considered
N/A: a one-sentence comment fix.

## Implementation
### Target file
`scripts/eventbus/schema.sql`

### Procedure
1. Replace "durable generation record for DLQ->replay promotion requests" with wording that says the table is the durable record of requests to generate DLQ artifacts for events promoted into the DLQ.
2. Leave every SQL statement and the other comments unchanged.

### Method
- Keep each comment line within the existing line width; the comment uses `--` lines only.

### Details
- `git diff` of the file MUST show comment lines only.

## Compatibility considerations
- No DDL change: existing databases still match the canonical shape.

## Security considerations
N/A: comment only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `git diff scripts/eventbus/schema.sql` shows comment lines only.
- `uv run pytest tests/eventbus/test_eventbus_schema_version.py tests/eventbus/test_eventbus_db_tools.py -q`; `uv run python tools/check_db_separation.py`.

## Completion criteria
- The comment states the correct direction, no statement changed, and the shape tests pass unchanged.

## Out of Scope
- The schema task (a dedicated idempotency column, a foreign key, dropping `idx_events_seq`); any DDL change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the outbox comment | Completed | 20261119-120143 | 20261119-120211 | Step 2 stale check clean; Step 3a: outbox rows are inserted in the promotion transaction (insert_outbox_row) so the direction is replay to DLQ; file clean at baseline Changed: scripts/eventbus/schema.sql (comment only, 2 lines replaced by 3). Structural fingerprint of old and new DDL is equal; content_hash changed (expected, regenerated in seq 13) |
| 2 | Run the shape tests and `check_db_separation.py` | Completed | 20261119-120211 | 20261119-120211 | test_eventbus_schema_version and test_eventbus_db_tools 25 passed; check_db_separation: no violations |

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
- **Requirement ID**: `REQ-005` (correct the outbox comment)
- **Source issue**: issues/20261117-123017_adrchk017_eventbus-task-supervision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-113711_adrchk017_eventbus-task-supervision.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-114620
- **Related target files**: `scripts/eventbus/schema.sql`