## Goal
Mark REQ-002's `Status` field `resolved` in the governance inventory, citing commit
`520c9b39f9` and the new rollback/concurrency regression tests this Plan's Row 1 adds.

## Scope
In scope: the REQ-002 entry (lines 518-527) only — its `Status` field and a new
`Resolution` field/line.
Out of scope: any other entry in this document — REQ-003 of
`plans/20260920-203342_plan.md`. This is a distinct entry from REQ-001, already
handled by the sibling Plan's own separate implementation procedure document
(`implementations/20260920-205403_03_docs_00_governance_03_issue-and-uncertainty-management.md.md`,
from `plans/20260920-203022_plan.md`) — do not duplicate that row's edit here.

## Assumptions
- This row is implemented after Row 1
  (`tests/shared/test_runtime_tool_registry.py`, the sibling implementation procedure
  document from this same Plan), since the `Resolution` note cites its new test names.
- Since this row and Plan1's Row 3 (REQ-001's governance edit) both touch the same
  file, implement whichever lands first, then re-read the file's current state before
  editing (per Step 3a Adversarial Verification) to confirm the other row's edit (if
  already applied) has not shifted this entry's line numbers or introduced a
  conflicting `Resolution` bullet format choice — reuse whatever bullet-vs-paragraph
  convention the other row already established, for consistency within the same
  document, rather than independently re-deciding the format.

## Design decisions
- Follow the same resolved-entry convention as REQ-001's sibling edit (see
  `implementations/20260920-205403_03_docs_00_governance_03_issue-and-uncertainty-management.md.md`
  Design decisions, which itself follows the pre-existing CI-002/CI-004 precedent in
  this same file) — keep the entry in place, change `Status`, add a `Resolution`
  bullet/paragraph. Re-verify the exact convention chosen by whichever of the two rows
  (this one or REQ-001's) is implemented first, rather than deciding independently, so
  both resolved entries in the same document read consistently.

## Alternatives considered
- Deleting the REQ-002 heading instead of marking it resolved: rejected, same
  rationale as REQ-001's sibling document (this document's own CI-002/CI-004
  precedent keeps resolved entries in place).

## Implementation
### Target file
`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure
1. Re-read the current state of this file's REQ-001 entry (lines ~499-520, exact
   range may have shifted if the sibling row already landed) to confirm the
   `Resolution` bullet/paragraph format actually used, if already present — reuse it
   here for consistency; if REQ-001's edit has not landed yet, follow the convention
   confirmed via `rg -n "Resolution"` (same check as the sibling document's Procedure
   step 1).
2. Change the REQ-002 entry's `- **Status**: open` line to `- **Status**: resolved`.
3. Add a `- **Resolution**: ...` bullet (or paragraph, per step 1's confirmed
   convention) stating: the build-then-swap structure that already provides rollback
   and atomicity was implemented in commit `520c9b39f9` (2026-09-17); regression
   coverage added by
   `tests/shared/test_runtime_tool_registry.py::test_apply_policy_leaves_tools_unchanged_when_build_raises`
   and
   `::test_apply_policy_swap_never_exposes_mixed_state_to_concurrent_reader`; resolved
   per `plans/20260920-203342_plan.md`.
4. Leave every other field of the REQ-002 entry unchanged.

### Method
Direct file edit (`Edit` tool) — two localized changes to an existing entry.

### Details
Current entry (confirmed via Read, lines 518-527):
```
#### REQ-002

- **ID**: REQ-002
- **Title**: Atomic registry swap invariant not verified during config reload
- **Status**: open
- **Severity**: Medium
- **Area**: Agent
- **Type**: design-gap
- **Source**: `scripts/shared/runtime_tool_registry.py`
- **Owner**: Unassigned
...
```

Target shape after this change (illustrative — confirm exact bullet-vs-paragraph
convention per Procedure step 1):
```
#### REQ-002

- **ID**: REQ-002
- **Title**: Atomic registry swap invariant not verified during config reload
- **Status**: resolved
- **Severity**: Medium
...
- **Resolution**: The build-then-swap structure providing rollback-on-failure and
  atomic-swap-to-concurrent-readers was already implemented in commit `520c9b39f9`
  (2026-09-17). Regression coverage added by
  `tests/shared/test_runtime_tool_registry.py::test_apply_policy_leaves_tools_unchanged_when_build_raises`
  and `::test_apply_policy_swap_never_exposes_mixed_state_to_concurrent_reader`.
  Resolved per `plans/20260920-203342_plan.md`.
```

## Compatibility considerations
N/A: documentation-only change.

## Security considerations
N/A: no security-relevant behavior change.

## Rollback considerations
Trivially revertable: reverting the `Status` field to `open` and removing the
`Resolution` bullet/paragraph restores the prior text exactly.

## Validation plan
- `uv run python tools/check_needs_confirmation_inventory.py` — structural check
  (REQ-003, AC-4 of `plans/20260920-203342_plan.md`).
- Manual re-read of the edited entry to confirm no other field was accidentally
  changed, and no conflict was introduced with the sibling REQ-001 edit in the same
  file.

## Completion criteria
- REQ-002's `Status` field reads `resolved`.
- A `Resolution` bullet/paragraph exists citing commit `520c9b39f9` and the two new
  test names from Row 1.
- No other field of the REQ-002 entry, and no other entry in the document (including
  REQ-001, whose own edit is a separate row), is changed by this row.

## Out of scope
- REQ-001's entry — handled by the sibling Plan's own separate implementation
  procedure document.
- Any other governance entry.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm Resolution format convention (reuse REQ-001's if already landed) | Pending | — | — | |
| 2 | Change `Status` to `resolved` and add `Resolution` bullet/paragraph | Pending | — | — | |
| 3 | Run `tools/check_needs_confirmation_inventory.py` and manually re-verify | Pending | — | — | |

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
- **Requirement ID**: REQ-003 (mark REQ-002 resolved in the governance inventory)
- **Source issue**: issues/20260920-191138_req002_make-registry-swap-during-config-reload-atomic.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-203342_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-205732
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md
