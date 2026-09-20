## Goal
Mark REQ-001's `Status` field `resolved` in the governance inventory, citing the
2026-09-17 code fix and the new test/log evidence this Plan's Row 1 and Row 2 add.

## Scope
In scope: the REQ-001 entry (lines 499-516) only — its `Status` field and a new
`Resolution` field/line.
Out of scope: any other entry in this document (REQ-002, REQ-003, CI-*, etc.) — REQ-003
of `plans/20260920-203022_plan.md`.

## Assumptions
- Row 1 (`scripts/shared/runtime_tool_registry.py`) and Row 2
  (`tests/shared/test_runtime_tool_registry.py`) are implemented before this row, since
  the `Resolution` note cites their new test names as evidence — if implemented out of
  order, the citation still describes work that will exist once the Plan's full
  Execution Status reaches Completed for all three rows, consistent with how other
  `Resolution Target` entries in this same document already cite forward-looking or
  batched work (e.g. the CI-008–CI-016 batching note, confirmed via Read).
- The document's existing entry format (`- **Field**: value` bullet list under a `####
  {ID}` heading) has no separate "Resolution" field defined elsewhere in the file for
  a resolved entry — checked via `rg -n "Resolution" docs/00_governance_03_issue-and-uncertainty-management.md`
  before implementation to confirm whether to add a new `- **Resolution**:` bullet or
  follow an existing resolved-entry convention (e.g. CI-002's/CI-004's prose-paragraph
  style, confirmed present in the same file at lines 239-245).

## Design decisions
- Follow the existing resolved-entry precedent already in this same file for CI-002/
  CI-004 (lines 239-245, confirmed via Read during the source Plan's Step 3
  investigation): a short paragraph appended after the entry (or a `Resolution` bullet
  within it) that states the resolution date, the evidence, and an explicit note that
  the entry stays removed from future active-list confusion — rather than deleting the
  entry outright, since `docs/00_governance_03_issue-and-uncertainty-management.md`'s
  own convention (confirmed by CI-002/CI-004) is to keep a resolved entry's record in
  place with its status changed, not to delete the heading.
- Cite commit `520c9b39f9` (the actual code fix date, 2026-09-17) separately from this
  Plan's own generated-at date (2026-09-20), so a future reader can distinguish "when
  the code was actually fixed" from "when the governance record caught up" — consistent
  with how CI-004's resolution paragraph (lines 243) cites the specific commit/file
  evidence it verified against, not just a generic "resolved" stamp.

### Non-blocking discrepancy: CI-003's `Related` field is stale
The REQ-001 entry's own `Impact` line says "violating the security boundary
established by REQ-001" (self-referential — likely meant "CI-003" or a different
predecessor entry, confirmed by re-reading the entry's own `Related: CI-003` field
just above it). This appears to be a pre-existing copy-paste artifact from when the
entry was first filed, not something this Plan's own Requirements ask to fix (REQ-003
of `plans/20260920-203022_plan.md` only asks to change `Status` and add a
`Resolution` note). Per `rules/coding.md`'s "Documentation notes — Current behavior
classification", this is an "Issue already tracked"-adjacent case (the fix belongs
with whichever future edit next touches this exact prose), not blocking for this row —
leave the `Impact` line's wording as-is; do not silently rewrite it as an unscoped
extra edit while making the `Status`/`Resolution` change.

## Alternatives considered
- Deleting the REQ-001 heading entirely instead of marking it resolved in place:
  rejected — inconsistent with this same document's own CI-002/CI-004 precedent
  (resolved entries stay, with status changed and a resolution note added, explicitly
  to avoid "recreate the heading" confusion per those entries' own closing sentences).

## Implementation
### Target file
`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure
1. Re-run `rg -n "Resolution" docs/00_governance_03_issue-and-uncertainty-management.md`
   to confirm the exact resolved-entry format convention in current use (a `-
   **Resolution**:` bullet vs. a following prose paragraph) before choosing which
   shape to add — do not assume the Design decisions section's CI-002/CI-004 precedent
   is the only shape without this direct re-check, since the document may have
   accumulated other conventions since that Plan-time investigation.
2. Change the REQ-001 entry's `- **Status**: open` line (currently at the line
   confirmed via Read) to `- **Status**: resolved`.
3. Add a `- **Resolution**: ...` bullet (or a following short paragraph, per step 1's
   confirmed convention) stating: the enforcement was implemented in commit
   `520c9b39f9` (2026-09-17); regression coverage was added by
   `tests/shared/test_runtime_tool_registry.py::test_apply_policy_keeps_hidden_tool_disabled_when_allowed`
   and `::test_apply_policy_logs_warning_when_hidden_tool_would_otherwise_be_enabled`;
   a diagnostic warning log was added to
   `scripts/shared/runtime_tool_registry.py::apply_policy()`; resolved per
   `plans/20260920-203022_plan.md`.
4. Leave every other field of the REQ-001 entry (`Title`, `Severity`, `Area`, `Type`,
   `Source`, `Owner`, `First Found`, `Target`, `Related`, `Summary`, `Current
   Description`, `Observed Implementation`, `Impact`, `Recommended Action`) unchanged —
   this row's scope is `Status` + `Resolution` only.

### Method
Direct file edit (`Edit` tool) — two localized changes (one field value, one new
bullet/paragraph) to an existing entry; no restructuring of the surrounding document.

### Details
Current entry (confirmed via Read, lines 499-516):
```
#### REQ-001

- **ID**: REQ-001
- **Title**: Immutable discovery-time visibility field (`llm_visibility_base`) not enforced during config reload
- **Status**: open
- **Severity**: High
...
- **Recommended Action**: Enforce immutability of `llm_visibility_base` in the config reload path; add tests to verify this invariant.
```

Target shape after this change (illustrative — confirm exact bullet-vs-paragraph
convention per Procedure step 1 before finalizing wording):
```
#### REQ-001

- **ID**: REQ-001
- **Title**: Immutable discovery-time visibility field (`llm_visibility_base`) not enforced during config reload
- **Status**: resolved
- **Severity**: High
...
- **Recommended Action**: Enforce immutability of `llm_visibility_base` in the config reload path; add tests to verify this invariant.
- **Resolution**: Enforcement was implemented in commit `520c9b39f9` (2026-09-17),
  three days before this entry was filed. Regression coverage added by
  `tests/shared/test_runtime_tool_registry.py::test_apply_policy_keeps_hidden_tool_disabled_when_allowed`
  and `::test_apply_policy_logs_warning_when_hidden_tool_would_otherwise_be_enabled`;
  a diagnostic warning log added to
  `scripts/shared/runtime_tool_registry.py::apply_policy()`. Resolved per
  `plans/20260920-203022_plan.md`.
```

## Compatibility considerations
N/A: documentation-only change, no code/API surface affected.

## Security considerations
N/A: no security-relevant behavior change — this row only updates a governance record
to reflect already-implemented, already-verified enforcement.

## Rollback considerations
Trivially revertable: reverting the `Status` field to `open` and removing the
`Resolution` bullet/paragraph restores the prior text exactly.

## Validation plan
- `uv run python tools/check_needs_confirmation_inventory.py` — structural check
  confirming the edit does not break the governance inventory's structure (REQ-003,
  AC-4 of `plans/20260920-203022_plan.md`).
- Manual re-read of the edited entry to confirm no other field was accidentally
  changed.

## Completion criteria
- REQ-001's `Status` field reads `resolved`.
- A `Resolution` bullet/paragraph exists citing commit `520c9b39f9`, the two new test
  names from Row 2, and this Plan's path.
- No other field of the REQ-001 entry, and no other entry in the document, is changed.

## Out of scope
- REQ-001's own `Impact` field's self-referential wording discrepancy (see Design
  decisions "Non-blocking discrepancy" note) — not part of this row's Requirement.
- Any other governance entry (REQ-002, REQ-003, CI-*) — REQ-002's sibling Plan
  (`plans/20260920-203342_plan.md`) has its own separate implementation procedure
  document for REQ-002's entry.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm resolved-entry format convention via `rg -n "Resolution"` | Pending | — | — | |
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
- **Requirement ID**: REQ-003 (mark REQ-001 resolved in the governance inventory)
- **Source issue**: issues/20260920-190713_req001_enforce-immutability-of-llm_visibility_base-during-config-reload.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-203022_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-205403
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md
