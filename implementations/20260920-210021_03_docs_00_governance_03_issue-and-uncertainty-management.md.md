## Goal
Mark CI-007's `Status` field `resolved` in the governance inventory, citing the
verified INV-07 code correctness, the new tests, and the ADR-009 documentation fixes
this Plan's Rows 1 and 2 add.

## Scope
In scope: the CI-007 entry (lines 257-274) only — its `Status` field and a new
`Resolution` field/line.
Out of scope: any other entry in this document, including CI-014 and the CI-008
through CI-016 batching note (explicitly out of scope per the source Plan's own Scope
> Out-of-Scope) — REQ-005 of `plans/20260920-203952_plan.md`.

## Assumptions
- Rows 1 (`tests/rag/test_fts_sync.py`) and 2
  (`docs/adr/ADR-009-rag-ft5-text-separation.md`) are implemented before this row,
  since the `Resolution` note cites their new/corrected content.
- This entry does not share a `Resolution Target: ADR-invariant test suite initiative
  — tracked as one cross-area effort` framing with the CI-008-016 batch (confirmed via
  Read: CI-007 has no `Resolution Target` field at all, and is not listed among the
  batch's cited IDs in the batching note at line 457) — so resolving it individually,
  without touching the batching note, is consistent with the document's own existing
  categorization, not a deviation from it.

## Design decisions
- **Correction (carried forward from the REQ-001/REQ-002 sibling rows' own Step 4a
  adversarial re-verification):** this document's line 22 states resolved items are
  removed from the active inventory, not retained with a closed-out status. Both
  sibling rows
  (`implementations/done/20260920-205403_03_docs_00_governance_03_issue-and-uncertainty-management.md.md`,
  `implementations/done/20260920-205732_02_docs_00_governance_03_issue-and-uncertainty-management.md.md`)
  already corrected this same mistaken assumption and removed their headings
  entirely. This row follows the same, now-confirmed convention for CI-007.

## Alternatives considered
- Keeping the `#### CI-007` heading and only changing its `Status` field: rejected —
  same correction as the sibling REQ-001/REQ-002 rows; contradicts this document's own
  explicit rule (line 22) and existing resolved-entry precedent (CI-001 through
  CI-004).

## Implementation
### Target file
`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure
1. Re-read the current state of this file around CI-007 (line range may have shifted
   if the REQ-001/REQ-002 sibling rows already landed and shortened the document).
2. Remove the entire `#### CI-007` heading and its 17-field list.
3. In its place, add a single short paragraph — matching CI-001/CI-002/CI-003/CI-004's
   prose style and position — stating: CI-007 ("ADR-009 INV-09 — FTS5 rebuild rules
   not verified") was resolved; INV-07's trigger-vs-manual-rebuild text selection was
   confirmed identical by direct code reading (both apply
   `COALESCE(normalized_content, content)`); the previously-named INV-07 test was
   non-functional and has been rewritten to actually exercise
   `RagMaintenanceService.rebuild_fts()` against trigger-populated data
   (`tests/rag/test_fts_sync.py::test_fts_trigger_and_manual_rebuild_use_same_text_selection_rule`);
   INV-09's behavior is documented in ADR-009; DESIGN-2 now has a static-analysis
   guard test (`tests/rag/test_fts_sync.py::test_no_unsanctioned_direct_chunks_fts_write`);
   resolved per `plans/20260920-203952_plan.md`. End with: "Its absence from the
   active list is the correct, policy-compliant state — do not create a `#### CI-007`
   heading."
4. Leave every other entry in the document unchanged.

### Method
Direct file edit (`Edit` tool) — two localized changes to an existing entry.

### Details
Current entry (confirmed via Read, lines 257-274):
```
#### CI-007

- **ID**: CI-007
- **Title**: ADR-009 INV-09 — FTS5 rebuild rules not verified
- **Status**: open
- **Severity**: Low
- **Area**: RAG
- **Type**: ambiguous-behavior
- **Source**: `scripts/rag/`
- **Owner**: @data-eng
- **First Found**: 2026-09-03
- **Target**: `docs/adr/ADR-009-rag-ft5-text-separation.md`
- **Related**: ADR-009, DESIGN-2
- **Summary**: ADR-009 defines specific FTS5 rebuild rules that must be followed.
- **Current Description**: These rules have not been validated against the actual implementation.
- **Observed Implementation**: Not verified.
- **Impact**: Incorrect FTS5 rebuild could lead to inconsistent search results.
- **Recommended Action**: Validate FTS5 rebuild logic against documented rules.
```

Target shape after this change (illustrative — the heading and field list are removed
entirely, replaced by a plain paragraph in CI-001/CI-002/CI-003's style):
```
CI-007 ("ADR-009 INV-09 — FTS5 rebuild rules not verified") was resolved 2026-09-20.
INV-07's trigger-vs-manual-rebuild text selection confirmed identical by direct code
reading (both apply `COALESCE(normalized_content, content)`). The previously-named
INV-07 test was non-functional and has been rewritten to exercise the real
`RagMaintenanceService.rebuild_fts()`
(`tests/rag/test_fts_sync.py::test_fts_trigger_and_manual_rebuild_use_same_text_selection_rule`).
INV-09's behavior documented in ADR-009. DESIGN-2 now has a static-analysis guard
(`tests/rag/test_fts_sync.py::test_no_unsanctioned_direct_chunks_fts_write`). Resolved
per `plans/20260920-203952_plan.md`. Its absence from the active list is the correct,
policy-compliant state — do not create a `#### CI-007` heading.
```

## Compatibility considerations
N/A: documentation-only change.

## Security considerations
N/A: no security-relevant behavior change.

## Rollback considerations
Trivially revertable: restoring the removed `#### CI-007` heading and its field list,
and removing the new resolved-paragraph, restores the prior text exactly.

## Validation plan
- `uv run python tools/check_needs_confirmation_inventory.py` — structural check
  (REQ-005, AC-6 of `plans/20260920-203952_plan.md`).
- Manual re-read of the surrounding entries to confirm no other entry (including
  REQ-001/REQ-002, whose own edits are separate rows) was accidentally altered.

## Completion criteria
- The `#### CI-007` heading and its 17-field list no longer exist in the document.
- A short paragraph in CI-001/CI-002/CI-003's style exists in their place, citing the
  corrected INV-07 test, the ADR-009 INV-09 documentation, and the DESIGN-2 guard
  test, ending with "do not create a `#### CI-007` heading."
- No other entry in the document is changed by this row.

## Out of scope
- REQ-001/REQ-002 entries — handled by sibling Plans' own separate implementation
  procedure documents.
- CI-014 and the CI-008-016 batching note — explicitly out of scope per the source
  Plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm Resolution format convention (reuse REQ-001/REQ-002's if already landed) | Completed | 20260920-212657 | 20260920-212657 | Reused REQ-001/REQ-002's corrected heading-removal convention |
| 2 | Change `Status` to `resolved` and add `Resolution` bullet/paragraph | Completed | 20260920-212657 | 20260920-212657 |  |
| 3 | Run `tools/check_needs_confirmation_inventory.py` and manually re-verify | Completed | 20260920-212657 | 20260920-212657 | Same pre-existing/unrelated doc-checker warnings as REQ-001/REQ-002's rows |

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
- **Requirement ID**: REQ-005 (mark CI-007 resolved in the governance inventory)
- **Source issue**: issues/20260920-191952_ci007_validate-fts5-rebuild-rules-from-adr-009-against-implementation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-203952_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-210021
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md