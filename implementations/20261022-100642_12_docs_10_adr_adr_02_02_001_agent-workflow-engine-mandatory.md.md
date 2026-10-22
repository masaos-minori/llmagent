## Goal
Reword the file-list entry for `scripts/db/schema_sql.py` in the workflow-engine ADR so it no longer says "workflow migrations", as a reference-only edit with no Decision change (REQ-010).

## Scope
- One bullet of the implementation-notes file list.

## Assumptions
- Owner approval for a reference-only ADR edit is recorded before editing (Plan UNK-03).
- After the code change the module holds the workflow schema DDL and its version constant.

## Design decisions
- New entry text: "`scripts/db/schema_sql.py` — workflow schema DDL".

## Alternatives considered
N/A: single-bullet edit.

## Implementation
### Target file
`docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`

### Procedure
1. Replace the bullet "`scripts/db/schema_sql.py` — workflow migrations" with the new entry.

### Method
- One in-place edit; run `uv run python tools/check_adr_preservation.py` afterwards.

### Details
- Do not touch Decision text, invariants, or the Approval section.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_preservation.py`, `check_adr_structure.py`, `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`.

## Completion criteria
- The entry no longer mentions migrations and the preservation checker reports no ERROR.

## Out of Scope
- All other ADR content.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Obtain the owner's approval for the reference-only edit (Plan UNK-03) | Pending | — | — | |
| 2 | Edit the file-list entry | Pending | — | — | |
| 3 | Run the ADR and documentation checkers | Pending | — | — | |

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
- **Requirement ID**: `REQ-010` (reference-only workflow-engine ADR edit)
- **Source issue**: `issues/20261021-102049_rmwfmig_remove-the-workflow.sqlite-incremental-migrations.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-093726_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-100642
- **Related target files**: docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md
