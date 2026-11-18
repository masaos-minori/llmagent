## Goal
Define the allowed ADR Status values including Withdrawn, the pending-amendment form, and the ledger citation format (REQ-004, REQ-005, REQ-006).

## Scope
**Release unit**: N/A: not part of a release unit
- `## ADR Status Definitions` and a new subsection after `### ADR Acceptance Evidence Standard`.
- Proposal only until the maintainer approves the governance change.

## Assumptions
- Confirm that the maintainer decision this document needs (D1 to D4 and UNK-01 to UNK-03 of the Source plan) is recorded as a maintainer comment on the Source plan; stop and ask when it is not. Write no approval text.
- The ledger ID prefix `AAL-` and the ledger location (a new part of `docs/00_governance/governance_03_issue-and-uncertainty-management.md`) are the Source plan's proposed defaults (UNK-01); a different maintainer decision changes the cited IDs only.
- Withdrawn is defined as a governed status (D3); removal of ADR-010 is UNK-02.

## Design decisions
- The pending form stays a bullet under `### Approval Record` and the Status line stays `Accepted`, because `tools/check_canonical_source_registry.py` requires the first Status line to equal `Accepted` for an ADR-sourced entry.
- The ledger fields are defined once in the issue-management governance document; this document states only the citation format and points there.

## Alternatives considered
A Status variant such as `Accepted (Amendment pending)` was rejected: it fails the registry check for ADR-004.

## Implementation
### Target file
`docs/00_governance/governance_01_documentation-policy.md`
### Procedure
1. Add Withdrawn to `## ADR Status Definitions`: the decision no longer applies; the record is kept; the Status first line is exactly the word Withdrawn; a `### Withdrawal Approval Record` is required; surviving present-tense wording is tracked as a Canonical Source Conflict.
2. After `### ADR Acceptance Evidence Standard` add `### ADR Pending Amendment Form`: the bullet `- **Current Decision Approval (pending)**:` under `### Approval Record`, the content it states (the changed text, that approver, date, and scope are not recorded, the ledger ID `AAL-NNN`), the rule that the Status line is unchanged, and that the bullet is removed when the approval is recorded.
3. State that an ADR edit changing a decision either carries an approval record or is shown in this form (consistent with `### Blocking Conditions (Prevent Merge)`; do not edit Merge Conditions).
### Method
Edit in place with the document's heading style; use MUST and MUST NOT wording for rules; name items instead of counting them.
### Details
- Keep `## ADR Status Definitions` bullet style (one bullet per value).

## Compatibility considerations
N/A: additive; `Proposed` and `Accepted` keep their meaning.

## Security considerations
N/A: documentation-only change; the implementer writes no approval text.

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_japanese.py`
- `uv run python tools/check_adr_structure.py`, `uv run python tools/check_adr_authority.py`, `uv run python tools/check_adr_invariant_matrix.py`, `uv run python tools/check_adr_preservation.py` (its Approval-section reports are reviewed and justified, not suppressed)

## Completion criteria
- The allowed Status set, the Withdrawn rules, the pending form, and the citation format are defined once.
- The change is merged only with the maintainer's approval.

## Out of Scope
- Approving any pending decision.
- Editing Merge Conditions or the ADR template.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm the maintainer sign-off for D2 and D3 | Completed | 20261118-103727 | 20261118-103727 | Maintainer sign-off D2 (pending form, Status line stays Accepted) and D3 (governed Withdrawn) recorded in session 2026-11-18 via AskUserQuestion |
| 2 | Edit ADR Status Definitions and add the pending amendment form | Completed | 20261118-103727 | 20261118-103727 | Withdrawn added to ADR Status Definitions; ADR Pending Amendment Form subsection added after the Acceptance Evidence Standard; 23721 B under the 24576 B gate |
| 3 | Run the documentation checkers listed in Validation plan | Completed | 20261118-103727 | 20261118-103727 | docs quality/structure/content-policy/japanese, canonical-source registry/conflicts, adr_structure, known_deviation_sync: pass |

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
- **Requirement ID**: `REQ-004`: ledger citation; `REQ-005`: pending form; `REQ-006`: Withdrawn status
- **Source issue**: issues/20261117-123011_adrchk011_adr-approval-governance.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-092611_adrchk011_adr-approval-governance.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-093859
- **Related target files**: `docs/00_governance/governance_01_documentation-policy.md`
