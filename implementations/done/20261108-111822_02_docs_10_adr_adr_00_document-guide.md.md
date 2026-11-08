## Goal
Add a one-sentence pointer in the ADR document guide to the new `governance_01` rule (REQ-006).

## Scope
**Release unit**: N/A: not part of a release unit
Edits `docs/10_adr/adr_00_document-guide.md` only.

## Assumptions
- Phase 2 of the Plan: runs after the `governance_01` rule exists (seq 01).
- Verified now: the guide has no responsibility or historical-content statement.

## Design decisions
- One sentence pointing to the rule; no restatement.

## Alternatives considered
N/A: one-sentence change

## Implementation
### Target file
`docs/10_adr/adr_00_document-guide.md`

### Procedure
1. Add one sentence to the guide section about ADR conventions (or the nearest fitting section) pointing to the `governance_01` rule on ADR responsibilities and historical content.

### Method
Documentation edit.

### Details
- Do not duplicate the rule text.

## Compatibility considerations
Documentation only.

## Security considerations
N/A: documentation-only change

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_japanese.py`: no findings

## Completion criteria
- The guide contains one pointer sentence and no copy of the rule.

## Out of Scope
- Other guide sections.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the document as described in Implementation > Procedure | Completed | 20261108-122020 | 20261108-122020 | Gated: owner decision on UNK-01 (policy versus retained amendments) and approval check UNK-03 - do not start the policy edit until both are resolved |
| 2 | Run the documentation checkers named in the Validation plan | Completed | 20261108-122020 | 20261108-122020 | owner decided: ADR Amendment is an explicit exception, marked in force or superseded; docs checkers pass; ADR-010 at 24561 bytes (ceiling 24576) |

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
- **Requirement ID**: `REQ-006` (guide pointer)
- **Source issue**: issues/20261107-050707_adrdoc001_separate-adr-current-history.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-093000_adrdoc001_separate-adr-current-history.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-111822
- **Related target files**: `docs/10_adr/adr_00_document-guide.md`
