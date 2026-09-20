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
- **Correction (Step 4a adversarial re-verification during code-implementation):**
  the Plan's original Design decisions here misread the CI-002/CI-004 precedent. Line
  22 of this same document states explicitly: "An item is removed from this active
  inventory once it is resolved or no longer applies to the current system; it is not
  retained here with a closed-out status." Direct re-reading of CI-001 (line 236),
  CI-002 (line 239), CI-003 (line 237), and CI-004 (line 243) confirms every one of
  them **removes the `#### {ID}` heading and all 17 template fields**, replacing them
  with a single short paragraph in the surrounding prose — not a `Status: resolved`
  field change with the heading retained. Each resolved paragraph ends with an
  explicit `Its absence from the active list is the correct, policy-compliant state —
  do not create a #### {ID} heading.` sentence. This document's own `## Resolution
  Rules` section (line 955) independently confirms the *substantive* resolution
  criterion ("Known Issue resolved only when implementation and design agree") is
  satisfied here, but says nothing about retaining a closed-out heading — line 22's
  rule is the controlling one for *how* to record it.
- Therefore this row implements: remove the `#### REQ-001` heading and its entire
  field list (lines 499-516), and add a short paragraph — in the same prose style and
  position as CI-001/CI-002/CI-003/CI-004 — stating the resolution, citing commit
  `520c9b39f9` and the two new tests, ending with the standard "do not create a ####
  REQ-001 heading" sentence.
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
- Keeping the `#### REQ-001` heading and only changing its `Status` field to
  `resolved` (the Plan's original approach): rejected after Step 4a's adversarial
  re-verification found this contradicts this document's own explicit rule (line 22)
  and every existing resolved-entry precedent (CI-001 through CI-004) — see Design
  decisions above.

## Implementation
### Target file
`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure
1. Remove the entire `#### REQ-001` heading and its 17-field list (lines 499-516).
2. In its place, add a single short paragraph — matching CI-001/CI-002/CI-003/CI-004's
   prose style and position — stating: REQ-001 ("Immutable discovery-time visibility
   field (`llm_visibility_base`) not enforced during config reload") was resolved;
   enforcement was implemented in commit `520c9b39f9` (2026-09-17); regression
   coverage was added by
   `tests/shared/test_runtime_tool_registry.py::test_apply_policy_keeps_hidden_tool_disabled_when_allowed`
   and `::test_apply_policy_logs_warning_when_hidden_tool_would_otherwise_be_enabled`;
   a diagnostic warning log was added to
   `scripts/shared/runtime_tool_registry.py::apply_policy()`; resolved per
   `plans/20260920-203022_plan.md`. End with: "Its absence from the active list is the
   correct, policy-compliant state — do not create a `#### REQ-001` heading."
3. Leave every other entry in the document unchanged.

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

Target shape after this change (illustrative — match CI-001/CI-003's exact prose
cadence when finalizing wording; the heading and field list are removed entirely):
```
CI-004 ("ADR-010 INV-02 ...") was resolved and removed from this active inventory
2026-09-14. ...

REQ-001 ("Immutable discovery-time visibility field (`llm_visibility_base`) not
enforced during config reload") was resolved 2026-09-20. Enforcement was implemented
in commit `520c9b39f9` (2026-09-17), three days before this entry was filed.
Regression coverage added by
`tests/shared/test_runtime_tool_registry.py::test_apply_policy_keeps_hidden_tool_disabled_when_allowed`
and `::test_apply_policy_logs_warning_when_hidden_tool_would_otherwise_be_enabled`; a
diagnostic warning log added to
`scripts/shared/runtime_tool_registry.py::apply_policy()`. Resolved per
`plans/20260920-203022_plan.md`. Its absence from the active list is the correct,
policy-compliant state — do not create a `#### REQ-001` heading.

#### REQ-002
...
```
(The surrounding CI-004/REQ-002 headings above are shown only to illustrate REQ-001's
new paragraph fits between them in document order — CI-004 and REQ-002 themselves are
untouched by this row.)

## Compatibility considerations
N/A: documentation-only change, no code/API surface affected.

## Security considerations
N/A: no security-relevant behavior change — this row only updates a governance record
to reflect already-implemented, already-verified enforcement.

## Rollback considerations
Trivially revertable: restoring the removed `#### REQ-001` heading and its 17-field
list, and removing the new resolved-paragraph, restores the prior text exactly (the
removed block is fully captured in this document's own "Current entry" quote above).

## Validation plan
- `uv run python tools/check_needs_confirmation_inventory.py` — structural check
  confirming the edit does not break the governance inventory's structure (REQ-003,
  AC-4 of `plans/20260920-203022_plan.md`).
- Manual re-read of the surrounding entries (CI-004, REQ-002) to confirm neither was
  accidentally altered, and that the new paragraph reads consistently with
  CI-001/CI-002/CI-003's own prose style.

## Completion criteria
- The `#### REQ-001` heading and its 17-field list no longer exist in the document.
- A short paragraph in CI-001/CI-002/CI-003's style exists in their place, citing
  commit `520c9b39f9`, the two new test names from Row 2, this Plan's path, and ending
  with "do not create a `#### REQ-001` heading."
- No other entry in the document (CI-004, REQ-002, etc.) is changed.

## Out of scope
- REQ-001's own former `Impact` field's self-referential wording discrepancy (see
  Design decisions "Non-blocking discrepancy" note) — moot once the field list is
  removed per this row's corrected approach; not re-introduced elsewhere.
- Any other governance entry (REQ-002, REQ-003, CI-*) — REQ-002's sibling Plan
  (`plans/20260920-203342_plan.md`) has its own separate implementation procedure
  document for REQ-002's entry.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm resolved-entry format convention via `rg -n "Resolution"` | Completed | 20260920-211348 | 20260920-211348 | Adversarial verification found the Plan's Design decisions misread CI-002/CI-004's actual format (heading removal, not Status-field change) — corrected in this procedure document before implementing; see corrected Design decisions section |
| 2 | Change `Status` to `resolved` and add `Resolution` bullet/paragraph | Completed | 20260920-211348 | 20260920-211348 |  |
| 3 | Run `tools/check_needs_confirmation_inventory.py` and manually re-verify | Completed | 20260920-211348 | 20260920-211348 | check_needs_confirmation_inventory.py, check_docs_quality.py, check_docs_structure.py warnings all pre-existing/unrelated (confirmed via git diff --stat and file-size comparison: 70451 to 69473 bytes, decreased) |

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