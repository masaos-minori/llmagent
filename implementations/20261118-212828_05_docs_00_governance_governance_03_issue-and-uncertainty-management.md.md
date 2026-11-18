## Goal
- Add the `AAL-030` entry to the governance_03 approval-amendment ledger for the ADR-002
  INV-04 pending amendment, the ledger half of the pending-amendment form (Plan Phase 2,
  gated; REQ-005; AC-005).

## Scope
**Release unit**: N/A: not part of a release unit
- **In-Scope**: one new ledger entry `AAL-030` (ADR-002, INV-04 amendment, Approver/Date
  `Not recorded`) in `docs/00_governance/governance_03_issue-and-uncertainty-management.md`.
- **Out-of-Scope**: the Part 5 ledger rules themselves, every existing entry
  (AAL-001..AAL-029), the ADR-002 side of the form (owned by the seq 01 procedure).

## Assumptions
- Gate: execute only after the user acknowledges the governance_03 scope amendment (Plan
  Scope) and the maintainer authorizes filing the proposal (Plan Phase 2 gate).
- Verified this cycle: ledger entries run AAL-001..AAL-029, so the next ID is `AAL-030`
  (Part 5 requires every cited ID to have an entry).

## Design decisions
- Register the ledger entry before the ADR-002 pending bullet: `tools/check_adr_structure.py`
  enforces that a pending-amendment citation resolves to an existing ledger entry, so this
  procedure must complete before the seq 01 procedure runs.

## Alternatives considered
- Reusing an existing AAL ID — rejected: Part 5 assigns one entry per amendment proposal;
  reusing an ID would corrupt the ledger.

## Implementation
### Target file
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (Modify)
### Procedure
1. Confirm the Phase 2 gate is open (user acknowledgement + maintainer authorization).
2. Append the `AAL-030` entry to the ledger: target ADR-002, subject INV-04 amendment,
   Approver `Not recorded`, Date `Not recorded`.
### Method
- Docs-only edit; one appended ledger entry following the existing entry format.
### Details
- Never write maintainer approval text, Approver names, or dates (AC-005); `Not recorded`
  until the maintainer approves (UNK-01).

## Compatibility considerations
- This entry is cited by the seq 01 procedure's pending bullet; the two edits belong to one
  change so citation and entry stay consistent.
- Existing entries AAL-001..AAL-029 are not touched; ordering by ID is preserved.

## Security considerations
- N/A: ledger metadata only; no credentials or token values are recorded.

## Rollback considerations
- Remove the `AAL-030` entry and the ADR-002 pending bullet together (revert both commits or
  one combined revert); leaving the bullet without the entry fails `tools/check_adr_structure.py`.

## Validation plan
- `uv run python tools/check_adr_structure.py` (ledger-citation rule)
- `rg -n "AAL-030" docs/00_governance/governance_03_issue-and-uncertainty-management.md`
  shows exactly one entry with Approver/Date `Not recorded`
- N/A: no pytest or code targets (docs-only row)

## Completion criteria
- AC-005: `AAL-030` exists with Approver/Date `Not recorded`, no approval text is authored,
  and `tools/check_adr_structure.py` passes with 0 findings.

## Out of Scope
- Recording any approval; amending Part 5 rules; editing ADR-002 itself (seq 01 procedure).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Gated: Plan Phase 2 (user acknowledgement of the governance_03 scope amendment + maintainer authorization); see Assumptions; runs before the seq 01 procedure |
| 2 | Add or update tests per Validation plan | N/A | — | — | Docs-only row; no test changes |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Docs checkers only; ruff/mypy/pytest N/A |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | The target file is the documentation itself (Step 1) |

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
- **Requirement ID**: REQ-005 (AC-005)
- **Source issue**: issues/20261117-123001_adrchk001_mcp-auth-contract.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-210631_adrchk001_mcp-auth-contract.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-212828
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md
