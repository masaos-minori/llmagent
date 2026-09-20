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
- Follow the same resolved-entry convention already established by REQ-001/REQ-002's
  sibling edits in this same file (see
  `implementations/20260920-205403_03_docs_00_governance_03_issue-and-uncertainty-management.md.md`
  and
  `implementations/20260920-205732_02_docs_00_governance_03_issue-and-uncertainty-management.md.md`)
  — re-verify whichever bullet-vs-paragraph convention those rows actually landed
  with (if implemented first) for consistency across all three resolved entries in
  this session's batch.

## Alternatives considered
- Deleting the CI-007 heading instead of marking it resolved: rejected, same rationale
  as the sibling REQ-001/REQ-002 rows (this document's own CI-002/CI-004 precedent).

## Implementation
### Target file
`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure
1. Re-read the current state of the REQ-001/REQ-002 entries (or `rg -n "Resolution"`
   if neither sibling row has landed yet) to confirm the `Resolution` bullet/paragraph
   format actually used this session — reuse it here for consistency.
2. Change the CI-007 entry's `- **Status**: open` line to `- **Status**: resolved`.
3. Add a `- **Resolution**: ...` bullet (or paragraph, per step 1's confirmed
   convention) stating: INV-07's trigger-vs-manual-rebuild text selection was
   confirmed identical by direct code reading (both apply
   `COALESCE(normalized_content, content)`); the previously-named INV-07 test was
   non-functional and has been rewritten to actually exercise
   `RagMaintenanceService.rebuild_fts()` against trigger-populated data
   (`tests/rag/test_fts_sync.py::test_fts_trigger_and_manual_rebuild_use_same_text_selection_rule`);
   INV-09's behavior is documented in ADR-009; DESIGN-2 now has a static-analysis
   guard test (`tests/rag/test_fts_sync.py::test_no_unsanctioned_direct_chunks_fts_write`);
   resolved per `plans/20260920-203952_plan.md`.
4. Leave every other field of the CI-007 entry unchanged.

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

Target shape after this change (illustrative — confirm exact bullet-vs-paragraph
convention per Procedure step 1):
```
#### CI-007

- **ID**: CI-007
- **Title**: ADR-009 INV-09 — FTS5 rebuild rules not verified
- **Status**: resolved
- **Severity**: Low
...
- **Recommended Action**: Validate FTS5 rebuild logic against documented rules.
- **Resolution**: INV-07's trigger-vs-manual-rebuild text selection confirmed
  identical by direct code reading (both apply `COALESCE(normalized_content,
  content)`). The previously-named INV-07 test was non-functional and has been
  rewritten to exercise the real `RagMaintenanceService.rebuild_fts()`
  (`tests/rag/test_fts_sync.py::test_fts_trigger_and_manual_rebuild_use_same_text_selection_rule`).
  INV-09's behavior documented in ADR-009. DESIGN-2 now has a static-analysis guard
  (`tests/rag/test_fts_sync.py::test_no_unsanctioned_direct_chunks_fts_write`).
  Resolved per `plans/20260920-203952_plan.md`.
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
  (REQ-005, AC-6 of `plans/20260920-203952_plan.md`).
- Manual re-read of the edited entry to confirm no other field was accidentally
  changed, and no conflict with the sibling REQ-001/REQ-002 edits in the same file
  (confirm those edits and this one do not collide on line ranges).

## Completion criteria
- CI-007's `Status` field reads `resolved`.
- A `Resolution` bullet/paragraph exists citing the corrected INV-07 test, the ADR-009
  INV-09 documentation, and the DESIGN-2 guard test.
- No other field of the CI-007 entry, and no other entry in the document, is changed
  by this row.

## Out of scope
- REQ-001/REQ-002 entries — handled by sibling Plans' own separate implementation
  procedure documents.
- CI-014 and the CI-008-016 batching note — explicitly out of scope per the source
  Plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm Resolution format convention (reuse REQ-001/REQ-002's if already landed) | Pending | — | — | |
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
- **Requirement ID**: REQ-005 (mark CI-007 resolved in the governance inventory)
- **Source issue**: issues/20260920-191952_ci007_validate-fts5-rebuild-rules-from-adr-009-against-implementation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-203952_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-210021
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md
