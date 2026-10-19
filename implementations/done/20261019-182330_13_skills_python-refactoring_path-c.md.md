## Goal
- Make the new-ADR file name rule in `skills/python-refactoring/path-c.md` match the grouped shape (`REQ-005` (state the naming rule and registry)).

## Scope
- In scope: `skills/python-refactoring/path-c.md` only.
- Out of scope: every other file (they have their own procedure documents), ADR content, and historical archives.

## Assumptions
- The Plan's group registry and new names are accepted (Plan Assumptions, UNK-02).
- The 14 renames happen in this one change, so no intermediate state is published.

## Design decisions
- Point to the registry instead of copying it, so the skill cannot drift.

## Alternatives considered
- Copy the registry into the skill: rejected, duplication.

## Implementation
### Target file

`skills/python-refactoring/path-c.md`

### Procedure
1. Replace the new-ADR naming rule (the sentence that cites the old pattern) with `adr_02_{group}_{next-number}_{group-word}-{slug}.md` and point to the group registry in `docs/10_adr/adr_00_document-guide.md`.
### Method
- Edit the single rule; keep the surrounding wording.
### Details
- The group registry lives in the document guide (REQ-005); this file only points to it.

## Compatibility considerations
- N/A: instruction text only.

## Security considerations
- N/A: no security impact.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py`

## Completion criteria
- The rule states the new shape and refers to the registry.

## Out of Scope
- Modifying any file other than the target file; ADR decisions, IDs, status, and invariants; `issues/done/`, `plans/done/`, `implementations/done/`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the rule | Completed | 20261019-205118 | 20261019-205118 |  |
| 2 | Run the documentation checkers | Completed | 20261019-205118 | 20261019-205118 | Stale clean; rule updated with group registry pointer. check_skills_references and check_skills_heading_cycles pass. Skill doc only: no code tests. |

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
- **Requirement ID**: `REQ-005`
- **Source issue**: issues/done/20261019-170548_adrname001_group-adr-file-names-by-theme.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261019-173513_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-182330
- **Related target files**: skills/python-refactoring/path-c.md