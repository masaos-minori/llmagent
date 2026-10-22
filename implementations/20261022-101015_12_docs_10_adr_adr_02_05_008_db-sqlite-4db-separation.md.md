## Goal
Remove the remaining EventBus migration references from ADR-008 as a reference-only edit with no Decision change (REQ-008).

## Scope
- The sentence stating that `eventbus.sqlite` applies incremental additive migrations and the `_migrate()` / section 8b pointer in the `schema-repair` definition.
- The workflow-related references are edited by the workflow-migration procedure; apply sequentially and re-read the lines first.

## Assumptions
- Owner approval for a reference-only ADR edit is recorded before editing (Plan UNK-02); if refused, stop and report and adjust the acceptance command instead.
- After both removal Plans land, no database in the four-database set has a migration mechanism.

## Design decisions
- Migration sentence: after the workflow edit it reads "`rag.sqlite`, `session.sqlite`, and `workflow.sqlite` have no migration mechanism ...; `eventbus.sqlite` applies incremental additive migrations (`db_03` section 8b)"; this procedure rewrites it to list all four databases as recreated on a schema change and keeps "Migration design is out of scope for this ADR."
- `schema-repair` definition: remove the `_migrate()` and section 8b pointer and the word "migration" from the path description, leaving the initialization path.

## Alternatives considered
- Leaving the ADR as written: rejected, it describes removed mechanisms and contradicts the code.

## Implementation
### Target file
`docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`

### Procedure
1. Edit the migration sentence as described.
2. Edit the `schema-repair` definition as described.

### Method
- Two minimal in-place edits; run `uv run python tools/check_adr_preservation.py` after each.

### Details
- Do not touch Decision text, invariants, Known Deviations, or the Approval section.

## Compatibility considerations
N/A: documentation only; the preservation checker is the guard.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_preservation.py`, `check_adr_structure.py`, `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`.
- `rg "apply_eventbus_migrations|apply_workflow_migrations|_migrate\b" docs/10_adr` returns no match.

## Completion criteria
- The ADR names no removed function and says no database has a migration mechanism; the preservation checker reports no ERROR.

## Out of Scope
- Decision text and all other ADRs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Obtain the owner's approval for the reference-only edit (Plan UNK-02) | Pending | — | — | |
| 2 | Edit the two references | Pending | — | — | |
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
- **Requirement ID**: `REQ-008` (reference-only ADR-008 edit)
- **Source issue**: `issues/20261021-102130_rmebmig_remove-the-eventbus.sqlite-schema-migrations.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-093935_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-101015
- **Related target files**: docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md
