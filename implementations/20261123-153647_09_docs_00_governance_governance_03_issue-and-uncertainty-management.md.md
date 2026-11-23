## Goal

Remove Known Issue AGENT-001 now that the two modules are retired, leaving NC-003 and ADR-006 item 14 unchanged.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: the `#### AGENT-001` entry only. No other entry, the ledger, or the Needs Confirmation inventory changes.

## Assumptions

- Verified: AGENT-001 asks for a keep-or-retire decision; the maintainer decided to retire (2026-11-23) and the retirement is the evidence; the entry's Resolution Target says retirement runs through a follow-up Plan, which is this Plan.
- Verified: no other entry or tool references AGENT-001 except a size-budget comment in `tools/check_docs_structure.py`, whose ceiling stays an upper bound after the removal.
- NC-003 stays open by the maintainer's decision (UNK-02).

## Design decisions

- Remove the whole entry including its heading; keep the surrounding blank-line structure.

## Alternatives considered

N/A: documentation only.

## Implementation
### Target file
`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure
1. Delete the AGENT-001 entry (from its `####` heading to the line before the next entry).

### Method
One Edit; check the conformance tool afterwards.

### Details
- Do not edit NC-003 or add approval text.

## Compatibility considerations

N/A: no behavior change.

## Security considerations

N/A: documentation only; no approval text, approver, or date is written.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_issue_inventory_conformance.py`
- `uv run python tools/check_needs_confirmation_inventory.py`
- `uv run python tools/check_docs_structure.py`
- `uv run python tools/run_validation_gates.py`

## Completion criteria

- AGENT-001 is gone, NC-003 is unchanged, and the checkers pass.

## Out of Scope

NC-003, ADR-006, ADR-013.

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
- **Requirement ID**: `REQ-004` (close AGENT-001)
- **Source issue**: issues/20261123-104603_gov004_eventbus-client-decision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-111218_gov004_eventbus-client-decision.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-153647
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
