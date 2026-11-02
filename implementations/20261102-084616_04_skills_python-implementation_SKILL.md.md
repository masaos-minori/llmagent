## Goal
- Add a pointer in `skills/python-implementation/SKILL.md` to `rules/persisted-schema-change.md` when the change touches DDL (`REQ-002`: skills point to the rule).

## Scope
- Modify `skills/python-implementation/SKILL.md` only (Medium blast radius: entry skill for code changes, so keep the edit to one bullet or sentence).

## Assumptions
- A1: `rules/persisted-schema-change.md` exists by the time this document runs (`seq` 01).
- A2: Step 3a: the "Composition rules" section lists composed skills and has no schema pointer (verified with rg).
- A3: Overlap judgment (Step 2, `check_plan_target_overlaps.py`, 2026-11-02): `routing.md` is targeted by six Frozen Plans (flowimp001, 003, 004, 005, 010, 011). Judged compatible: the others add rows to "When to run which tool" or a different section; this Plan only adds one entry to the "Conditional load" list. No conflict or sequencing dependency. Other Plans' judgments (A5-A7 in their Assumptions) agree.

## Design decisions
- One bullet in "Composition rules" (or a one-line note under it): when the change touches DDL, a schema version, or a migration, read `rules/persisted-schema-change.md` before Phase 5.
- Not a skill composition; the rule is a file, so wording says "load", not "call".

## Alternatives considered
- N/A: pointer form fixed by the Plan.

## Implementation
### Target file
`skills/python-implementation/SKILL.md`

### Procedure
1. Read the "Composition rules" section.
2. Add the bullet at the end of the list.

### Method
- Match the existing bullet format (name, dash, condition).

### Details
- Do not restate checklist items.

## Compatibility considerations
- N/A: additive pointer.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py`: no findings.

## Completion criteria
- The file points to the rule for DDL changes (AC-2); both checkers pass.

## Out of Scope
- Other skills, `routing.md`, the rule content.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the DDL pointer to `skills/python-implementation/SKILL.md` | Pending | — | — | |
| 2 | Run `check_skills_references.py` and `check_skills_heading_cycles.py` | Pending | — | — | |

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
- **Related target files**: skills/python-implementation/SKILL.md
