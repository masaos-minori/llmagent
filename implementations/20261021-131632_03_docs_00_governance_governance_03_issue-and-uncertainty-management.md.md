## Goal

Record the owner decision (reclassify or restore) in the NC-041 inventory entry in
`docs/00_governance/governance_03_issue-and-uncertainty-management.md`, mark NC-041
resolved, and complete REQ-004.

## Scope

Only the NC-041 entry in the Needs Confirmation Inventory of `governance_03`. No other
file is modified by this document.

## Assumptions

- The owner decision is recorded (external gate, UNK-01).
- The decision text and assigned owner are captured verbatim.

## Design decisions

- The inventory entry records the chosen outcome (reclassify or restore), its Decision
  Group 3 item 10 basis, and the assigned owner, then marks the entry resolved.
- Removing the inline Needs-confirmation marker from `agent_08_04` is a verification
  dependency enforced by `check_needs_confirmation_inventory.py`; this document does not
  issue modification instructions for that file.

## Alternatives considered

N/A: single documented path — close the NC-041 entry once the decision is recorded.

## Implementation

### Target file

`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure

Update the NC-041 entry with the decision record and assigned owner, then mark it
resolved.

### Method

Edit the NC-041 entry (lines 126-127 region) in the Needs Confirmation Inventory.

### Details

- Current state (evidence: `governance_03` lines 126-127): NC-041 is an active item whose
  Evidence notes the disagreement between `config/agent.toml` (`required = false`) and the
  classification table (`github` = required), with no owner decision.
- In the NC-041 entry, add a decision record stating the chosen outcome (reclassify or
  restore), the item 10 basis, and the assigned owner; set the entry status to resolved.
- Confirm the inline Needs-confirmation marker is removed from `agent_08_04` (verification
  dependency; enforced by the checker).
- Run `uv run python tools/check_needs_confirmation_inventory.py` and confirm no issues
  and NC-041 closed.

## Compatibility considerations

The Needs Confirmation Inventory format is enforced by
`check_needs_confirmation_inventory.py`. Keep the fifteen Inventory Entry Fields intact
and register the resolved entry per `routing.md` Tools "When to run which tool".

## Security considerations

N/A: governance inventory record.

## Rollback considerations

Restore the entry to pending status if the decision is withdrawn before implementation.

## Validation plan

- `check_needs_confirmation_inventory.py` — no issues found; NC-041 closed; no
  unregistered inline marker remains.

## Completion criteria

NC-041 records the decision and owner and is marked resolved;
`check_needs_confirmation_inventory.py` reports no issues.

## Out of Scope

Applying the reclassify/restore config or table changes (handled by the other two rows);
any other NC item.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Record the owner decision and assigned owner in the NC-041 entry, mark it resolved | Pending | — | — | |
| 2 | Run `check_needs_confirmation_inventory.py` — NC-041 closed, no unregistered inline marker | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Owner decision (reclassify vs restore) not available to the planning agent | N/A: pending external governance decision | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-004`
- **Source issue**: `issues/20261021-100235_nc041_resolve-the-github-mcp-server-required-classification-disagreement.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261021-121020_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261021-131632
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
