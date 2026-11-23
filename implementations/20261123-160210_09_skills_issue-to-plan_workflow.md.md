## Goal

Make `issue-to-plan` load the runtime rule file at Step 0 instead of the whole design document.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: the Step 0 load list (about line 78) and the inline citations of moved sections at about lines 25, 353, 408, and 728. No other text changes.

## Assumptions

- Verified: Step 0 lists `skills/DESIGN.md` (Output language, Change-impact table, Out-of-scope paths, Tool availability guard); the other citations name Analysis-only phase constraint, Output language, Change-impact table.

## Design decisions

- Replace each `skills/DESIGN.md` citation of a moved section with `rules/skill-runtime.md`, keeping the section name; Step 0 lists the file without a section list.

## Alternatives considered

N/A: documentation only.

## Implementation
### Target file
`skills/issue-to-plan/workflow.md`

### Procedure
1. Edit the Step 0 list.
2. Edit the four inline citations.
3. Grep the file for remaining `skills/DESIGN.md` citations of moved sections.

### Method
Targeted Edit operations.

### Details
- Citations of sections that stay in `skills/DESIGN.md` (none expected in this file) are left unchanged.

## Compatibility considerations

Wording of every rule is unchanged.

## Security considerations

N/A: documentation only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_skills_references.py`
- `uv run python tools/check_skills_heading_cycles.py`
- `uv run python tools/run_validation_gates.py`

## Completion criteria

- The workflow names `rules/skill-runtime.md` for the moved sections and the checkers pass.

## Out of Scope

Other skills.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers named in `rules/tool-gates.md` for a changed `docs/` file (`uv run python tools/run_validation_gates.py`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (runtime rule file and pointers)
- **Source issue**: issues/20261123-155457_skillsize001_compress-skill-workflows.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-155813_skillsize001_compress-skill-workflows.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-160210
- **Related target files**: `skills/issue-to-plan/workflow.md`
