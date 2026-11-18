## Goal
Cite the ADR approval ledger entry on each pending approval bullet of ADR-005 so the pending amendment is shown in the defined form (REQ-008: apply the forms to every ADR in the inventory).

## Scope
**Release unit**: N/A: not part of a release unit
- Edit only the `### Approval Record` pending bullets of this ADR; ledger IDs: AAL-004, AAL-005.
- The ADR decision text is not edited, reverted, or approved here.

## Assumptions
- Confirm that the maintainer decision this document needs (D1 to D4 and UNK-01 to UNK-03 of the Source plan) is recorded as a maintainer comment on the Source plan; stop and ask when it is not. Write no approval text.
- The ledger ID prefix `AAL-` and the ledger location (a new part of `docs/00_governance/governance_03_issue-and-uncertainty-management.md`) are the Source plan's proposed defaults (UNK-01); a different maintainer decision changes the cited IDs only.
- The IDs follow the assignment rule of the procedure for the ledger part of the issue-management governance document: ADR number order, then bullet order in the file. Re-run `rg -n "Current Decision Approval \(pending\)" docs/10_adr/` first; if the bullets differ from this list, stop and report a Plan Gap.

## Design decisions
- Keep each bullet's description and add only the ledger citation required by the pending-amendment form in the policy governance document.

## Alternatives considered
N/A: the form is fixed by the governance change; this row only applies it.

## Implementation
### Target file
`docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md`
### Procedure
1. Confirm the governance definition (ledger part and pending form) is merged and the sign-off exists.
2. For each pending bullet below, add the ledger citation in the wording the pending-amendment form defines (default: replace the phrase naming the ledger with the entry ID, or append `Ledger: AAL-NNN.` when the bullet has no such phrase).
3. Leave the `Status` line and every non-approval section unchanged.
### Method
Edit the existing bullets in place under `### Approval Record`; no new heading, no reordering.
### Details
- Entries for this ADR:
  - AAL-004: Decision 10 remediation for orphan_vec_count
  - AAL-005: Decision 8 rewrite referencing ADR-009

## Compatibility considerations
N/A: wording-only edit to the Approval section; the decision text and the `Accepted` Status line are unchanged.

## Security considerations
N/A: documentation-only change; no approval text is written.

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run python tools/check_adr_structure.py`, `uv run python tools/check_adr_authority.py`, `uv run python tools/check_adr_invariant_matrix.py`, `uv run python tools/check_adr_preservation.py` (its Approval-section reports are reviewed and justified, not suppressed)
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_japanese.py`
- `uv run python tools/check_canonical_source_registry.py`

## Completion criteria
- Every `Current Decision Approval (pending)` bullet of this ADR cites its ledger ID.
- No decision, invariant, or Status text changed.
- The ADR checkers report no ERROR apart from reviewed `check_adr_preservation.py` Approval-section reports.

## Out of Scope
- Approving or reverting any pending decision.
- Editing any other ADR or `docs/10_adr/adr_01_index.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm the governance definition and the maintainer sign-off exist | Pending | — | — | Stop and ask if absent |
| 2 | Add ledger IDs (AAL-004, AAL-005) to the pending bullets | Pending | — | — |  |
| 3 | Run the ADR and documentation checkers listed in Validation plan | Pending | — | — |  |

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
- **Requirement ID**: `REQ-008`: apply the defined forms to every ADR in the inventory
- **Source issue**: issues/20261117-123011_adrchk011_adr-approval-governance.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-092611_adrchk011_adr-approval-governance.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-093859
- **Related target files**: `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md`
