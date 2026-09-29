## Goal

Remove CI-016 from Known Issues Part 1 in `docs/00_governance/governance_03_issue-and-uncertainty-management.md` and update the batching note to reflect one fewer remaining member (REQ-001 acceptance criterion).

## Scope

Removes the CI-016 subsection and updates the single batching-note paragraph. No other file is modified.

## Assumptions

- The REQ-001 test covering INV-14's `required=True` default has landed (this plan's Row 1), which is the condition for closing CI-016.
- Line numbers below are current as of freeze; re-locate with grep if the file has shifted.

## Design decisions

- Delete the CI-016 Known Issues entry entirely (it is resolved, not deferred), matching how sibling members were removed once their test coverage landed.
- Update the batching note to stay internally consistent (member count, area enumeration, removed-set list) rather than leaving a dangling CI-016 reference.

## Alternatives considered

- Marking CI-016 "closed" in place without deleting: rejected — the note groups these as removed-once-tested entries; CI-016 belongs in the removed set, not the active list.
- Editing only the count but not the area enumeration: rejected — would leave "and Agent (CI-016)" referencing a now-removed member.

## Implementation

### Target file

`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure

1. Locate the CI-016 subsection under Known Issues Part 1 via grep for `#### CI-016`.
2. Delete the entire CI-016 subsection (from its `#### CI-016` heading through its last field, currently lines ~193-211).
3. Update the batching note (currently line ~213) to reflect four remaining members instead of five.
4. Grep the whole file for "CI-016" to confirm zero remaining occurrences.

### Method

- Delete the CI-016 block starting at `#### CI-016` (line ~193) through the `- **Resolution Target**: ...` line just before the batching note (line ~211).
- Update the batching note (line ~213) from:
  "Note on CI-009, CI-010, CI-012, CI-014, CI-016 batching: These five structurally identical "ADR invariant verified by code inspection, no automated test" entries are treated as one initiative (originally nine members; CI-008, CI-011, CI-013, and CI-015 were removed once test coverage was added). Their Area fields span Shared/DB (CI-009), MCP (CI-010), EventBus (CI-012), RAG (CI-014), and Agent (CI-016) — one member per area — and no single existing RACI role is accountable for a cross-area ADR-invariant-test-suite initiative. This Plan flags the decision for human determination: create a new cross-cutting role vs. revert to per-area ownership."
  to:
  "Note on CI-009, CI-010, CI-012, CI-014 batching: These four structurally identical "ADR invariant verified by code inspection, no automated test" entries are treated as one initiative (originally nine members; CI-008, CI-011, CI-013, CI-015, and CI-016 were removed once test coverage was added). Their Area fields span Shared/DB (CI-009), MCP (CI-010), EventBus (CI-012), and RAG (CI-014) — one member per area — and no single existing RACI role is accountable for a cross-area ADR-invariant-test-suite initiative. This Plan flags the decision for human determination: create a new cross-cutting role vs. revert to per-area ownership."

### Details

- Preserve the surrounding markdown structure and the note's trailing sentence about the ownership decision awaiting human determination.
- Keep the note in English (matches the existing note's language).

## Compatibility considerations

- Documentation-only; does not affect other Known Issues or the Part 2 Needs Confirmation inventory.
- If any index or table of contents references CI-016, update it during the read-back in Validation plan.

## Security considerations

- N/A: governance documentation edit.

## Rollback considerations

- Restore the deleted CI-016 subsection and original batching note from version control.

## Validation plan

- Read back the Known Issues Part 1 region and confirm CI-016 is gone and the batching note reads consistently (four members, no CI-016 reference).
- Grep the whole file for "CI-016" to confirm zero remaining occurrences.

## Completion criteria

- No `#### CI-016` subsection remains in Known Issues Part 1.
- The batching note reflects four remaining members and contains no dangling CI-016 reference.

## Out of scope

- Other CI members (CI-009, CI-010, CI-012, CI-014) — left untouched.
- The cross-cutting ownership-model decision referenced by the note — out of scope for this row.
- ADR-004's CI-016 Known Deviation — handled by that row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260927-211347_ci016_add-unit-test-for-adr-004-undefined-criticality-safe-default.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260928-094534_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260928-133619
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md
