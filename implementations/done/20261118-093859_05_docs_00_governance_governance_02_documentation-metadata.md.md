## Goal
State that front matter `status` is independent of the ADR `## Status` values (REQ-006).

## Scope
**Release unit**: N/A: not part of a release unit
- One sentence under `### status`.

## Assumptions
- D3 keeps Withdrawn as a governed ADR status; with removal (UNK-02) this row is dropped through a Plan amendment.
- Confirm that the maintainer decision this document needs (D1 to D4 and UNK-01 to UNK-03 of the Source plan) is recorded as a maintainer comment on the Source plan; stop and ask when it is not. Write no approval text.

## Design decisions
- The existing rule removes deprecated or superseded documents from the active set rather than marking them; the sentence scopes that rule to the front matter field.

## Alternatives considered
N/A: single sentence.

## Implementation
### Target file
`docs/00_governance/governance_02_documentation-metadata.md`
### Procedure
Add to `### status` one sentence: ADR `## Status` values are defined in the policy governance document and are independent of this field.
### Method
Edit in place; keep the allowed values `stable` and `draft` unchanged.
### Details
- Reference the policy document by its title, not by section number.

## Compatibility considerations
N/A: wording-only.

## Security considerations
N/A: documentation-only change.

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_japanese.py`

## Completion criteria
- The sentence exists and `### status` still lists only `stable` and `draft`.

## Out of Scope
- Changing the allowed front matter values.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm the maintainer sign-off for D3 | Completed | 20261118-103727 | 20261118-103727 | Maintainer sign-off D3 recorded in session 2026-11-18 |
| 2 | Add the sentence under `### status` | Completed | 20261118-103727 | 20261118-103727 | One sentence added under ### status |
| 3 | Run the documentation checkers listed in Validation plan | Completed | 20261118-103727 | 20261118-103727 | docs checkers: pass |

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
- **Requirement ID**: `REQ-006`: Withdrawn status
- **Source issue**: issues/20261117-123011_adrchk011_adr-approval-governance.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-092611_adrchk011_adr-approval-governance.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-093859
- **Related target files**: `docs/00_governance/governance_02_documentation-metadata.md`
