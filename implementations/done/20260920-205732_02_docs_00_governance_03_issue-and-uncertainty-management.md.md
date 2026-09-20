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
- **Correction (Step 4a adversarial re-verification during code-implementation,
  carried forward from the sibling REQ-001 row):** this document's own line 22 states
  "An item is removed from this active inventory once it is resolved ...; it is not
  retained here with a closed-out status." REQ-001's sibling row
  (`implementations/done/20260920-205403_03_docs_00_governance_03_issue-and-uncertainty-management.md.md`)
  already corrected the same mistaken assumption and removed REQ-001's heading
  entirely, replacing it with a short prose paragraph matching CI-001/CI-002/CI-003/
  CI-004's style. This row follows the same, now-confirmed convention for REQ-002.

## Alternatives considered
- Keeping the `#### REQ-002` heading and only changing its `Status` field: rejected —
  same correction as REQ-002's sibling REQ-001 row; contradicts this document's own
  explicit rule (line 22) and existing resolved-entry precedent.

## Implementation
### Target file
`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure
1. Re-read the current state of this file around REQ-002 (line range may have shifted
   if REQ-001's sibling row already landed and shortened the document) to confirm the
   exact current line numbers before editing.
2. Remove the entire `#### REQ-002` heading and its 17-field list.
3. In its place, add a single short paragraph — matching CI-001/CI-002/CI-003/CI-004's
   (and REQ-001's, once its own row lands) prose style and position — stating: REQ-002
   ("Atomic registry swap invariant not verified during config reload") was resolved;
   the build-then-swap structure that already provides rollback and atomicity was
   implemented in commit `520c9b39f9` (2026-09-17); regression coverage added by
   `tests/shared/test_runtime_tool_registry.py::test_apply_policy_leaves_tools_unchanged_when_build_raises`
   and
   `::test_apply_policy_swap_never_exposes_mixed_state_to_concurrent_reader`; resolved
   per `plans/20260920-203342_plan.md`. End with: "Its absence from the active list is
   the correct, policy-compliant state — do not create a `#### REQ-002` heading."
4. Leave every other entry in the document unchanged.

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

Target shape after this change (illustrative — the heading and field list are removed
entirely, replaced by a plain paragraph in CI-001/CI-002/CI-003's style):
```
REQ-002 ("Atomic registry swap invariant not verified during config reload") was
resolved 2026-09-20. The build-then-swap structure providing rollback-on-failure and
atomic-swap-to-concurrent-readers was already implemented in commit `520c9b39f9`
(2026-09-17). Regression coverage added by
`tests/shared/test_runtime_tool_registry.py::test_apply_policy_leaves_tools_unchanged_when_build_raises`
and `::test_apply_policy_swap_never_exposes_mixed_state_to_concurrent_reader`.
Resolved per `plans/20260920-203342_plan.md`. Its absence from the active list is the
correct, policy-compliant state — do not create a `#### REQ-002` heading.
```

## Compatibility considerations
N/A: documentation-only change.

## Security considerations
N/A: no security-relevant behavior change.

## Rollback considerations
Trivially revertable: restoring the removed `#### REQ-002` heading and its field list,
and removing the new resolved-paragraph, restores the prior text exactly.

## Validation plan
- `uv run python tools/check_needs_confirmation_inventory.py` — structural check
  (REQ-003, AC-4 of `plans/20260920-203342_plan.md`).
- Manual re-read of the surrounding entries to confirm no other entry (including
  REQ-001, whose own edit is a separate row) was accidentally altered.

## Completion criteria
- The `#### REQ-002` heading and its 17-field list no longer exist in the document.
- A short paragraph in CI-001/CI-002/CI-003's style exists in their place, citing
  commit `520c9b39f9` and the two new test names from Row 1, ending with "do not
  create a `#### REQ-002` heading."
- No other entry in the document is changed by this row.

## Out of scope
- REQ-001's entry — handled by the sibling Plan's own separate implementation
  procedure document.
- Any other governance entry.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm Resolution format convention (reuse REQ-001's if already landed) | Completed | 20260920-211834 | 20260920-211834 | Reused REQ-001's corrected heading-removal convention (see sibling row); same pre-existing/unrelated doc-checker warnings as REQ-001's row |
| 2 | Change `Status` to `resolved` and add `Resolution` bullet/paragraph | Completed | 20260920-211834 | 20260920-211834 |  |
| 3 | Run `tools/check_needs_confirmation_inventory.py` and manually re-verify | Completed | 20260920-211834 | 20260920-211834 |  |

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