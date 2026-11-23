## Goal

Point the Batch mode citation of the procedure template at the edge file.

## Scope
**Release unit**: code-implementation-edge-split

In scope: the sentence ending `Batch mode reads it.` (line 107).

## Assumptions

- Verified: the sentence reads `\`skills/code-implementation/workflow.md\` Batch mode reads it.`

## Design decisions

- Change the path to `skills/code-implementation/workflow-edge.md`.

## Alternatives considered

N/A: documentation only.

## Implementation
### Target file
`templates/implementation-procedure.md`

### Procedure
1. Edit the one sentence.

### Method
One Edit.

### Details
- No other change.

## Compatibility considerations

N/A: no behavior change.

## Security considerations

N/A: documentation only; no approval text, approver, or date is written.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_skills_references.py`
- `uv run python tools/run_validation_gates.py`

## Completion criteria

- The template names the edge file and the checkers pass.

## Out of Scope

Other template text.

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
- **Requirement ID**: `REQ-003` (outside citations name the edge file)
- **Source issue**: issues/20261123-155940_skillsize002_compress-skill-workflows-structure.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-161734_skillsize002_compress-skill-workflows-structure.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-162003
- **Related target files**: `templates/implementation-procedure.md`
