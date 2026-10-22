## Goal
Remove the remaining EventBus migration references from ADR-008 as a reference-only edit with no Decision change (REQ-008).

## Scope
- The sentence stating that `eventbus.sqlite` applies incremental additive migrations and the `_migrate()` / section 8b pointer in the `schema-repair` definition.
- The workflow-related references are edited by the workflow-migration procedure; apply sequentially and re-read the lines first.

## Assumptions
- Owner approval for a reference-only ADR edit is recorded before editing (Plan UNK-02); if refused, stop and report and adjust the acceptance command instead.
- After both removal Plans land, no database in the four-database set has a migration mechanism.

## Design decisions
- Migration sentence (Context constraints): `workflow.sqlite` still has its incremental migration mechanism (out of scope here), so keep its `db_03` section 8a reference; move `eventbus.sqlite` into the recreate-on-schema-change group (create-only, no migration). Keeps "Migration design is out of scope for this ADR."
- `schema-repair` definition (Decision > Recovery Category Glossary): remove only the eventbus `_migrate()` and section 8b pointer; keep `apply_workflow_migrations()` and section 8a. The "approved migration or initialization path" wording stays because `workflow.sqlite` still uses migration. Editing this definition changes the `## Decision` section text, so `check_adr_preservation.py` emits one WARNING (expected); the sentence-level mapping is: only the eventbus `_migrate()` reference was removed, no decision, invariant, or approval text changed.

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
- `rg "apply_eventbus_migrations|_EVENTBUS_MIGRATIONS|_migrate\b" docs/10_adr` returns no match (workflow's `apply_workflow_migrations` reference is intentionally retained; `workflow.sqlite` still has its migration mechanism, out of scope here).

## Completion criteria
- The ADR names no removed function and says no database has a migration mechanism; the preservation checker reports no ERROR.

## Out of Scope
- Decision text and all other ADRs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Obtain the owner's approval for the reference-only edit (Plan UNK-02) | Done | 20261022-101015 | 20261022-101015 | Owner approval granted for a reference-only edit with no Decision change. |
| 2 | Edit the two references | Done | 20261022-101015 | 20261022-101015 | Eventbus-only adaptation: removed the eventbus `_migrate()`/section 8b references from the constraints bullet and the schema-repair definition; kept workflow's `apply_workflow_migrations()`/section 8a reference (workflow.sqlite still migrates, out of scope). |
| 3 | Run the ADR and documentation checkers | Done | 20261022-101015 | 20261022-101015 | check_adr_structure clean; check_adr_preservation: no ERROR, one expected WARNING (schema-repair is inside ## Decision, so removing the eventbus ref changes that section text); check_docs_quality/structure/content_policy pass. |

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
