## Goal
- Make Step 8d of `skills/python-design/workflow.md` load and apply `rules/persisted-schema-change.md` for schema changes (`REQ-002`: skills load the rule).

## Scope
- Modify Step 8d ("Note migration path and documentation update points") of `skills/python-design/workflow.md` only.

## Assumptions
- A1: `rules/persisted-schema-change.md` exists by the time this document runs (`seq` 01).
- A2: Step 3a: Step 8d currently asks only for "the migration path for existing data/callers" (verified with rg).
- A3: Overlap judgment (Step 2, `check_plan_target_overlaps.py`, 2026-11-02): `routing.md` is targeted by six Frozen Plans (flowimp001, 003, 004, 005, 010, 011). Judged compatible: the others add rows to "When to run which tool" or a different section; this Plan only adds one entry to the "Conditional load" list. No conflict or sequencing dependency. Other Plans' judgments (A5-A7 in their Assumptions) agree.
- A4: Rule file does not link back to this step.

## Design decisions
- Add one sentence to Step 8d: if the design changes a persisted SQLite schema (DDL, version, migration), load `rules/persisted-schema-change.md` and state the outcome of each item next to the migration path.
- Leave the "Completed when" line as is; the check is guidance.

## Alternatives considered
- N/A: placement fixed by the Plan.

## Implementation
### Target file
`skills/python-design/workflow.md`

### Procedure
1. Read Step 8d (locate with grep, read a short range).
2. Insert the sentence after the existing migration-path paragraph.

### Method
- Path reference without anchor; keep the surrounding wording.

### Details
- Do not restate checklist items.

## Compatibility considerations
- N/A: additive wording in a skill workflow.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py`: no findings.

## Completion criteria
- Step 8d loads and applies the rule for schema changes (AC-2); both checkers pass.

## Out of Scope
- Other steps of the file, other skills, `routing.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the load-and-apply sentence to Step 8d of `skills/python-design/workflow.md` | Completed | 20261102-094909 | 20261102-094909 | full suite deferred to plan end; docs-only change, no source/test file changed, targeted pytest N/A; check_skills_references and check_skills_heading_cycles: no findings; run_validation_gates fast and drift OK |
| 2 | Run `check_skills_references.py` and `check_skills_heading_cycles.py` | Completed | 20261102-094909 | 20261102-094909 | full suite deferred to plan end; docs-only change, no source/test file changed, targeted pytest N/A; check_skills_references and check_skills_heading_cycles: no findings; run_validation_gates fast and drift OK |

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
- **Requirement ID**: `REQ-002`
- **Source issue**: issues/20261030-191222_flowimp004_schema-change-checklist.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-075753_flowimp004_schema-change-checklist.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-084616
- **Related target files**: skills/python-design/workflow.md