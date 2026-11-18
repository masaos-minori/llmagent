## Goal
Make the session data-layer guide state the ADR-008 mismatch, retention, and canonical-store rules for `session.sqlite` and memory (`REQ-005`, `REQ-006`, `REQ-007`).

## Scope
**Release unit**: N/A: not part of a release unit
- In scope: `Session Retention Policy`, `Memory Table Ownership`, and one new sentence on the schema-mismatch rule.

## Assumptions
- The guide already names SQLite `memories` canonical, JSONL an append-only archive, and `memories_fts`/`memories_vec` derived indexes (checked in Step 3a); `memory_links` is not named canonical.
- Procedure 02 has landed: ADR-008 Decision Details #22 to #24 exist.

## Design decisions
- Add pointers to ADR-008 instead of repeating its rules.

## Alternatives considered
N/A: the maintainer's decisions are recorded in the Plan's Design section.

## Implementation
### Target file
`docs/23_agent/agent_09_01_data-layer-session-db.md`

### Procedure
1. `Memory Table Ownership`: state that `memories` and `memory_links` are canonical and name the ADR-008 Decision Detail #24 classification.
2. After the retention paragraphs add: a `session.sqlite` file that does not match the current schema is archived and recreated (ADR-008 Decision Detail #22); export conversations with `/session export` first, recover memory from the JSONL archive with `/memory rebuild`; session history is not restored.
3. State that session retention is `purge_old_sessions()` (on demand), the diagnostics `retention_days` purge, and `/memory prune` for memory, as ADR-008 Decision Detail #23 records.

### Method
- Keep existing wording; add at most three sentences.

### Details
- The file is 7720 bytes; the limit is 32768.

## Compatibility considerations
N/A: documentation or comment text only.

## Security considerations
N/A: no approval statement is written or simulated; pending bullets only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- the checkers `routing.md` Tools lists for a `docs/` edit (`uv run python tools/run_validation_gates.py` runs the ones the changed files trigger).

## Completion criteria
- The guide names `memory_links` canonical and cites ADR-008 #22 to #24 for mismatch, retention, and canonical store; the checkers report no finding.

## Out of Scope
- ADR-008 text, code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the three statements (Implementation > Procedure) | Pending | — | — | |
| 2 | Run the documentation checkers (Validation plan) | Pending | — | — | |

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
- **Requirement ID**: REQ-005, REQ-006, REQ-007
- **Source issue**: issues/20261117-123008_adrchk008_db-data-lifecycle.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-142957_adrchk008_db-data-lifecycle.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-143801
- **Related target files**: `docs/23_agent/agent_09_01_data-layer-session-db.md`
