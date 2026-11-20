## Goal

Add the `AAL-037` entry to the ADR Approval Ledger so that ADR-006's pending
delivery-guarantee amendment has a ledger entry to cite.

## Scope
**Release unit**: N/A: not part of a release unit

- One new entry in Part 5; no other ledger entry is edited.

## Assumptions

- `AAL-036` is the highest existing id at the time of writing (re-confirmed immediately before the
  insertion, per the Plan's risk mitigation).

## Design decisions

- Entry text describes the change without asserting that anyone approved it: Approver and Date are
  "Not recorded".

## Alternatives considered

- N/A: the ledger entry form is fixed by the Part 5 Entry Fields section of this file.

## Implementation
### Target file
`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure
Insert one `#### AAL-037` entry after `#### AAL-036` and before `## Resolution Rules`.

### Method
Follow the field order of the Part 5 Entry Fields section, as used by `AAL-035` and `AAL-036`.

### Details

- `**ID:** AAL-037`, `**ADR:** ADR-006`, `**Decision:**` states the start position of the
  At-Least-Once delivery guarantee as a start position the Consumer itself selected (`since_seq`
  greater than zero or a `Last-Event-ID` header); `**Approver:** Not recorded`;
  `**Date:** Not recorded`; `**Scope:** Decision Detail 9 and INV-07 delivery-guarantee text`.
- The Scope names both statements because procedure
  `20261120-162706_01_docs_10_adr_adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md.md`
  changes both: `INV-07` restates Decision Detail 9 in the Invariants section.

## Compatibility considerations

- `tools/check_adr_structure.py` resolves ADR-006's new pending bullet only when this entry exists,
  so the two edits are one change unit.

## Security considerations

- N/A: ledger text only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_adr_structure.py` reports no finding about an unresolved pending bullet.
- `uv run python tools/check_known_deviation_sync.py` and
  `uv run python tools/check_needs_confirmation_inventory.py` report no findings: no new NC or UNK
  token is introduced.

## Completion criteria

- `AAL-037` exists exactly once, in id order, with Approver and Date "Not recorded".
- ADR-006's pending bullet resolves to it.

## Out of Scope

- Editing any other Part 5 entry, Part 1, or Part 2.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Insert `AAL-037` after `AAL-036` | Completed | 20261120-163733 | 20261120-163733 | Max id re-confirmed before insertion |
| 2 | Run the ledger and ADR checkers in the Validation plan | Completed | 20261120-163733 | 20261120-163733 | `check_adr_structure.py` reports only the pre-existing ADR-015 warning |

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
- **Requirement ID**: `REQ-003` (delivery-guarantee condition ledger entry)
- **Source issue**: issues/20261117-123016_adrchk016_adr006-boilerplate-fixes.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-155214_adrchk016_adr006-boilerplate-fixes.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-162706
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`