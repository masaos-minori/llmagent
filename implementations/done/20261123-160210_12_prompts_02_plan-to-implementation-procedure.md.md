## Goal

Point the `plan-to-implementation-procedure` prompt's Output language reference at the runtime rule file.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: the line `- Output language: see ...` (about line 27).

## Assumptions

- Verified: the line reads `Output language: see `skills/DESIGN.md` §Output language.`

## Design decisions

- Change the path to `rules/skill-runtime.md`, keeping `§Output language`.

## Alternatives considered

N/A: documentation only.

## Implementation
### Target file
`prompts/02_plan-to-implementation-procedure.md`

### Procedure
1. Edit the one line.

### Method
One Edit.

### Details
- No other change.

## Compatibility considerations

Same meaning.

## Security considerations

N/A: documentation only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_skills_references.py`
- `uv run python tools/check_skills_heading_cycles.py`

## Completion criteria

- The prompt names `rules/skill-runtime.md` and the checkers pass.

## Out of Scope

Other prompt text.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261123-160634 | 20261123-161116 | Edited as described; the five moved sections are verbatim (checked by a before and after comparison) |
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
- **Related target files**: `prompts/02_plan-to-implementation-procedure.md`
