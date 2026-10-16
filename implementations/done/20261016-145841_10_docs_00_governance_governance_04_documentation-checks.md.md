## Goal
- Remove the exemption wording from the `GV-023` row of the Governance Verification Matrix.

## Scope
- The last column of the `GV-023` row in `docs/00_governance/governance_04_documentation-checks.md`.

## Assumptions
- Other rows use `None` in that column when there is no note.
- The row's check description and tool stay the same.

## Design decisions
- Replace the note `/memory is exempt until AGENT-013 is resolved` with `None`.

## Alternatives considered
N/A: a one-cell change.

## Implementation
### Target file
`docs/00_governance/governance_04_documentation-checks.md`

### Procedure
- Change the final cell of the `GV-023` row from the exemption note to `None`.

### Method
- Edit only that cell; keep the table alignment of the other cells.

### Details
- Apply together with the `AGENT-013` removal so no citation of the removed ID remains.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py`, `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/00_governance/governance_04_documentation-checks.md`, `uv run python tools/check_docs_content_policy.py --strict`
- `rg AGENT-013 docs`

## Completion criteria
- The `GV-023` row has no exemption wording and the docs checkers report no new finding.

## Out of scope
- Other matrix rows and the check implementation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the GV-023 note | Pending | — | — | |
| 2 | Run the docs checkers | Pending | — | — | |

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
- **Requirement ID**: REQ-007 (GV-023 text)
- **Source issue**: issues/20261014-155503_mem001_implement-memory-command-spec.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261016-143248_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-145841
- **Related target files**: docs/00_governance/governance_04_documentation-checks.md
