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
| 1 | Obtain the owner's approval for the reference-only edit (Plan UNK-03) | Completed | 20261022-104512 | 20261022-134247 | Owner approved 2026-10-22: deviate from the Implementation References protection for this single stale reference; override recorded in the Blocker Log |
| 2 | Edit the file-list entry | Completed | — | 20261022-134247 | Line 279 (Implementation References list): `workflow migrations` -> `workflow schema DDL`. Line 222 (Implementation Notes prose, same stale descriptor): corrected for consistency |
| 3 | Run the ADR and documentation checkers | Completed | — | 20261022-134247 | check_docs_quality/structure/content_policy clean; AC-1 `rg apply_workflow_migrations|_WORKFLOW_MIGRATIONS` clean. `check_adr_preservation.py` reports 2 ERROR (Implementation References list item changed) — approved owner override (UNK-03); the tool is not a CI/pre-commit gate |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | `check_adr_preservation.py` reports ERROR "Implementation References: removed or changed item" for the file-list entry; the edit was reverted and needs the owner's ADR-change decision | Yes | 20261022 | Owner override (2026-10-22): the `scripts/db/schema_sql.py` entry genuinely describes a removed mechanism (workflow schema is DDL-only since commit 31f8c3be9; no migration code exists per db_03 s8a). Approved to deviate from the Implementation References protection for this one reference; `check_adr_preservation.py` reports 2 ERROR but is not a CI gate. AC-9's "no ERROR for the workflow-engine ADR" is waived for this documented override.

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