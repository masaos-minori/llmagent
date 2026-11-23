## Goal

Make `plan-to-implementation-procedure` load the runtime rule file at Step 0 instead of the whole design document.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: the Step 0 load list (about line 82) and the Allowed file operations citation (about line 37). No other text changes.

## Assumptions

- Verified: Step 0 lists `skills/DESIGN.md` (Output language, Out-of-scope paths) and the Allowed file operations cite the Analysis-only phase constraint.

## Design decisions

- Replace the citations with `rules/skill-runtime.md`, keeping the section names.

## Alternatives considered

N/A: documentation only.

## Implementation
### Target file
`skills/plan-to-implementation-procedure/workflow.md`

### Procedure
1. Edit the Step 0 list.
2. Edit the Allowed file operations citation.
3. Grep the file for remaining citations.

### Method
Two Edit operations.

### Details
- The two sentences keep their meaning.

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261123-160633 | 20261123-161116 | Edited as described; the five moved sections are verbatim (checked by a before and after comparison) |
| 2 | Run the documentation checkers named in `rules/tool-gates.md` for a changed `docs/` file (`uv run python tools/run_validation_gates.py`) | Completed | 20261123-161116 | 20261123-161116 | check_skills_references, check_skills_heading_cycles, and the validation gates pass |

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
- **Related target files**: `skills/plan-to-implementation-procedure/workflow.md`
