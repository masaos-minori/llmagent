## Goal

Extend the pending scope of ledger entry AAL-013 and remove the resolved CSC-001 entry from the governance inventory (REQ-002, REQ-003, REQ-004).

## Scope
**Release unit**: N/A: not part of a release unit

In scope: Part 3 Active Items and the AAL-013 entry of this document. The ADR-010 edit is the previous procedure and must be applied first.

## Assumptions

- Verified in this cycle: Part 3 holds CSC-001 as its only active item, AAL-013 reads `Withdrawal of the fallback decision` with scope `Status, Withdrawal Approval Record` and approver and date `Not recorded`, and Part 4 uses the empty-part sentence `No active Configuration Drift items remain.`.
- The conflict is closed only after the ADR-010 procedure landed, so the removal is applied second; the Resolution Rules require exactly one normative reading, which the marked passages give.
- SHARED-002 stays: its ADR-008 text is already consistent and only the maintainer's approval of AAL-027 is pending, which an implementer cannot record.

## Design decisions

- Replace the CSC-001 entry with the sentence `No active Canonical Source Conflict items remain.` under Part 3 Active Items, following Part 4's wording.
- Extend the AAL-013 Scope to `Status, Withdrawal Approval Record, historical marking of the corpus-identity passages (Decision Details 11 and 14, the two identity rows of the failure-outcome table, INV-09, one Negative Consequence, one Review Trigger)`; Approver and Date stay `Not recorded`.

## Alternatives considered

Rejected: a new ledger entry for the re-marking (it is the withdrawal's own record-keeping and AAL-013 already covers the withdrawal); rejected: keeping CSC-001 until approval (the Resolution Rules close a conflict when one normative reading remains).

## Implementation
### Target file
`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure
1. Delete the `#### CSC-001` entry, from its heading through its last field, from Part 3 Active Items.
2. Write `No active Canonical Source Conflict items remain.` as the Part 3 Active Items body, in the same position and style as Part 4.
3. Edit only the `Scope` line of `#### AAL-013` as described in Design decisions; leave its other fields untouched.

### Method
Use the Edit tool on exactly these two places; do not renumber or reorder any other entry and do not touch Parts 1, 2, 4, or the other ledger entries.

### Details
- Run the inventory conformance and Needs Confirmation checkers: the Part 3 entry-field rule must accept an empty part.
- Record in the commit message the validation evidence that `rg corpus_identity scripts/ tests/` lists no file.

## Compatibility considerations

N/A: documentation only; Decision Detail numbers, headings, and the failure-outcome table shape are unchanged.

## Security considerations

N/A: documentation only; no approval text, approver, or date is written.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_issue_inventory_conformance.py` and `uv run python tools/check_needs_confirmation_inventory.py` report no findings.
- `uv run python tools/check_known_deviation_sync.py` and `uv run python tools/check_adr_structure.py` report no findings.

## Completion criteria

- CSC-001 is absent and Part 3 states that no active items remain; AAL-013 keeps approver and date `Not recorded` and names the re-marked passages in its Scope.
- SHARED-002 and AAL-024 to AAL-028 are unchanged; the checkers pass.

## Out of Scope

SHARED-002, ledger entries other than AAL-013, and Parts 1, 2, 4 of the document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261123-105344 | 20261123-105344 | Changed: docs/00_governance/governance_03_issue-and-uncertainty-management.md (CSC-001 removed, AAL-013 scope) |
| 2 | Run the documentation checkers named in `rules/tool-gates.md` "When to run which tool" for a changed `docs/` file (`uv run python tools/run_validation_gates.py`) | Completed | 20261123-105344 | 20261123-105344 | N/A: documentation-only; inventory conformance, Needs Confirmation, known-deviation sync checkers and gates pass |

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
- **Requirement ID**: `REQ-002` (AAL-013 stays pending with an extended scope), `REQ-003` (CSC-001 removed), `REQ-004` (SHARED-002 and AAL-024 to AAL-028 unchanged)
- **Source issue**: issues/20261123-104600_gov001_resolve-adr-contradictions.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-104856_gov001_resolve-adr-contradictions.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-105126
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
