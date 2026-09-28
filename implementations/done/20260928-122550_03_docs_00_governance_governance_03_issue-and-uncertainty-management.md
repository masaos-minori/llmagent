## Goal

Remove CI-012 entry from Known Issues Part 1 in governance_03 and update the batching note to reflect one fewer remaining member.

## Scope

- **In-Scope**: Removing CI-012 from Known Issues Part 1; updating the batching note on line 213 to reflect one fewer remaining member; dropping CI-012 from any `Related` cross-references
- **Out-of-Scope**: Changes to `scripts/eventbus/offsets.py`; additions to `tests/eventbus/test_eventbus_offsets.py`; updates to `docs/10_adr/adr-index.md`

## Assumptions

- The test coverage added in the companion implementation procedure document (for `tests/eventbus/test_eventbus_offsets.py`) will be validated before this documentation update
- CI-012 is listed in Known Issues Part 1 of `governance_03`

## Design decisions

- Remove the entire CI-012 section (lines 153-155) rather than marking it as resolved — the issue is closed once test coverage exists
- Update the batching note to remove CI-012 from the list of remaining members
- Drop CI-012 from any `Related` cross-references in the same document

## Alternatives considered

- Marking CI-012 as "resolved" instead of removing it — rejected because Known Issues Part 1 is for open issues, not resolved ones
- Creating a separate "Resolved Issues" section — rejected because the document structure does not support this

## Implementation

### Target file

`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure

1. Remove the CI-012 section from Known Issues Part 1
2. Update the batching note to remove CI-012 from the list of remaining members
3. Confirm no dangling `Related`/`Target` reference to CI-012 remains

### Method

1. Delete the CI-012 section (header through its last bullet point) so CI-014 follows directly after the preceding paragraph.
2. Edit the batching note: drop CI-012 from the remaining-member list, change "These three" to "These two", add CI-012 to the removed-members list, and drop EventBus (CI-012) from the per-area span.
3. Verify no remaining entry cites CI-012 in a `Related`/`Target` field.

### Details

> Correction applied during adversarial verification (Step 3a): the original procedure described a stale state. CI-009 and CI-010 had already been removed by commit `ae00c05e` ("remove 5 resolved Known Issues"), so the current file lists only three remaining members (CI-012, CI-014, CI-016), not five. Line numbers were also updated to the current file. The intent (remove CI-012, update the batching note) was unchanged.

**Step 1: Remove CI-012 section**

Delete the CI-012 section (current lines 113-131):
```markdown
#### CI-012

- **ID**: CI-012
- **Title**: ADR-006 INV-01 — EventBus offset monotonicity, verified but needs test coverage
- **Status**: open
- **Severity**: Medium
- **Area**: EventBus
- **Type**: operational-gap
- **Source**: `scripts/eventbus/offsets.py::write_offset()`
- **Owner**: TODO(owner) — cross-area initiative, no single RACI role fits (see batching note)
- **First Found**: 2026-09-03
- **Target**: `docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`
- **Related**: ADR-006, EVENTBUS-001
- **Summary**: ADR-006 states that EventBus offsets must be monotonically increasing.
- **Current Description**: This has been verified via code inspection (`seq > current` enforcement confirmed in `write_offset()`), but there is no automated test covering this invariant.
- **Observed Implementation**: Verified by code inspection only.
- **Impact**: Without test coverage, regression of this invariant cannot be caught automatically.
- **Recommended Action**: Add a unit test for offset-monotonicity enforcement.
- **Resolution Target**: ADR-invariant test suite initiative — tracked as one cross-area effort, see batching note below
```

**Step 2: Update batching note**

Change the batching note from:
```
Note on CI-012, CI-014, CI-016 batching: These three structurally identical "ADR invariant verified by code inspection, no automated test" entries are treated as one initiative (originally nine members; CI-008, CI-009, CI-010, CI-011, CI-013, and CI-015 were removed once test coverage was added). Their Area fields span EventBus (CI-012), RAG (CI-014), and Agent (CI-016) — one member per area — and no single existing RACI role is accountable for a cross-area ADR-invariant-test-suite initiative. This Plan flags the decision for human determination: create a new cross-cutting role vs. revert to per-area ownership.
```

To:
```
Note on CI-014, CI-016 batching: These two structurally identical "ADR invariant verified by code inspection, no automated test" entries are treated as one initiative (originally nine members; CI-008, CI-009, CI-010, CI-011, CI-012, CI-013, and CI-015 were removed once test coverage was added). Their Area fields span RAG (CI-014) and Agent (CI-016) — one member per area — and no single existing RACI role is accountable for a cross-area ADR-invariant-test-suite initiative. This Plan flags the decision for human determination: create a new cross-cutting role vs. revert to per-area ownership.
```

**Step 3: Confirm no dangling CI-012 reference**

Verify no remaining entry cites CI-012 in a `Related`/`Target` field. CI-012 appeared only in its own entry (now deleted); no other entry references it. No further action required.

## Compatibility considerations

- No compatibility impact — updating documentation does not change behavior
- Other documents referencing CI-012 may need similar updates (e.g., adr-index.md)

## Security considerations

- This update reflects improved security verification (automated test coverage for offset monotonicity)
- Does not introduce any new security surface

## Rollback considerations

- If the test coverage is later removed, this row should be restored to Known Issues Part 1
- Document the reason for restoring in the commit message

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Manual verification | Read file content | CI-012 removed from Known Issues Part 1; batching note updated |

## Completion criteria

- [ ] CI-012 section removed from Known Issues Part 1
- [ ] Batching note updated to remove CI-012 from the list of remaining members
- [ ] CI-012 dropped from any `Related` cross-references

## Out of scope

- Production code changes (`scripts/eventbus/offsets.py`)
- Test additions (`tests/eventbus/test_eventbus_offsets.py`)
- Updates to other INV rows or CI entries

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260928-222131 | 20260928-222131 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260928-222131 | 20260928-222131 | N/A: docs-only change, no code or tests in scope |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260928-222131 | 20260928-222131 | Doc checkers ran clean vs edited sections (pre-existing size/content warnings in unrelated files) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260928-222131 | 20260928-222131 |  |

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
- **Requirement ID**: REQ-001 (ADR-006 offset-monotonicity invariant test exists and passes)
- **Source issue**: issues/20260927-211345_ci012_add-unit-test-for-adr-006-eventbus-offset-monotonicity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260928-092605_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260928-122550
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md