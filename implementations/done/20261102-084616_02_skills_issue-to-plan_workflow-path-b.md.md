## Goal
- Make Path B planning load and apply `rules/persisted-schema-change.md` when a change touches DDL, schema versions, or migrations (`REQ-002`: skills load the rule).

## Scope
- Modify `skills/issue-to-plan/workflow-path-b.md` only.

## Assumptions
- A1: `rules/persisted-schema-change.md` is created by the `seq` 01 document of this Plan; it will exist when this document is executed in order.
- A2: Step 3a: the file has sections Architecture analysis, Dependency graphing, Historical analysis, and Operational dependency inspection and no storage check (verified with rg).
- A3: Overlap judgment (Step 2, `check_plan_target_overlaps.py`, 2026-11-02): `routing.md` is targeted by six Frozen Plans (flowimp001, 003, 004, 005, 010, 011). Judged compatible: the others add rows to "When to run which tool" or a different section; this Plan only adds one entry to the "Conditional load" list. No conflict or sequencing dependency. Other Plans' judgments (A5-A7 in their Assumptions) agree.
- A5: Step 3a correction (code-implementation, 2026-11-02): the file ends with "once all four analyses above are complete"; the new section is conditional, so that closing line is extended with "(and the persisted schema check, when it applies)" in the same edit. Scope stays this one file.
- A4: The rule file must not link back to this section; this file links to the rule, not the reverse.

## Design decisions
- Add one short section (for example "Persisted schema check") after "Operational dependency inspection": when the change touches DDL, a schema version, or a migration, load `rules/persisted-schema-change.md` and record its checklist outcome in the Plan's Risks or Design.
- State that the checklist is guidance, not a gate.

## Alternatives considered
- N/A: placement decided in the Plan (A2); a heading inside an existing section was not preferred because the check is a separate analysis.

## Implementation
### Target file
`skills/issue-to-plan/workflow-path-b.md`

### Procedure
1. Read the end of the "Operational dependency inspection" section to choose the insertion point.
2. Add the section with a plain path reference to the rule file.

### Method
- Use a path reference without a heading anchor; follow the file's existing section style.

### Details
- Do not restate checklist items; the rule owns them (`skills/DESIGN.md` single-source rule).

## Compatibility considerations
- N/A: additive guidance for Path B plans only.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py`: no findings.

## Completion criteria
- The file loads and applies the rule for schema changes (AC-2) and both checkers pass.

## Out of Scope
- Other skills, `routing.md`, and the rule content.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the load-and-apply section to `skills/issue-to-plan/workflow-path-b.md` | Completed | 20261102-094909 | 20261102-094909 | full suite deferred to plan end; docs-only change, no source/test file changed, targeted pytest N/A; check_skills_references and check_skills_heading_cycles: no findings; run_validation_gates fast and drift OK |
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
- **Related target files**: skills/issue-to-plan/workflow-path-b.md