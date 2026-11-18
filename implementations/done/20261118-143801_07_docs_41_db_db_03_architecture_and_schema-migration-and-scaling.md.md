## Goal
Make the migration guide agree with ADR-008 on the database set, the mismatch rule, and retention (`REQ-004`, `REQ-005`, `REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit
- In scope: section 8e tables, one sentence in section 8e, and section 11 `Storage Growth`.
- Location of the guide resolved in Step 3: `docs/41_db/`.

## Assumptions
- The section 8e acceptance table lists `workflow`, `eventbus`, `mdq`, and `rag`/`session`, not `mcp_dedup`; the recreation-impact table lists only `workflow` and `eventbus` (checked in Step 3a).
- Section 11 lists cleanup mitigations as strategies although no deletion code exists for the EventBus tables.

## Design decisions
- Reuse the existing table shape; cite ADR-008 Decision Details #22 and #23.

## Alternatives considered
N/A: the maintainer's decisions are recorded in the Plan's Design section.

## Implementation
### Target file
`docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`

### Procedure
1. Section 8e intro and acceptance table: add `mcp_dedup.sqlite` (recreated empty by the dispatcher) and say the six databases follow ADR-008 Decision Detail #22.
2. Recreation-impact table: add rows for `session.sqlite` (sessions are lost; memory is recovered from the JSONL archive with `/memory rebuild`; export first), `rag.sqlite` (corpus is re-ingested), and `mcp_dedup.sqlite` (empty after recreation; non-retryable tools are rejected until the operator resolves the state).
3. Section 11: state that no cleanup is implemented for `events`, `consumer_delivery`, or `dlq_outbox` and that the unbounded growth is an accepted risk (ADR-008 Decision Detail #23); label the listed strategies as options, not behavior.

### Method
- Keep the runbook and the db_07 links unchanged.

### Details
- The file is 13064 bytes; the limit is 32768.

## Compatibility considerations
N/A: documentation or comment text only.

## Security considerations
N/A: no approval statement is written or simulated; pending bullets only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- the checkers `routing.md` Tools lists for a `docs/` edit (`uv run python tools/run_validation_gates.py` runs the ones the changed files trigger).

## Completion criteria
- Section 8e names six databases with the rule; section 11 says the cleanup is not implemented; the checkers report no finding.

## Out of Scope
- ADR text, `db_07`, `db_03_07` (UNK-03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit section 8e and section 11 (Implementation > Procedure) | Completed | 20261118-150735 | 20261118-150735 | Changed: docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md. |
| 2 | Run the documentation checkers (Validation plan) | Completed | 20261118-150735 | 20261118-150735 | — |

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
- **Requirement ID**: REQ-004, REQ-005, REQ-006
- **Source issue**: issues/20261117-123008_adrchk008_db-data-lifecycle.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-142957_adrchk008_db-data-lifecycle.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-143801
- **Related target files**: `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`
