## Goal
Add a Known Issue entry (`RAG-007`) recording that Null Fill Mode has been fully
removed from code and documentation, in
`docs/00_governance_03_issue-and-uncertainty-management.md` Part 1 — the corrected
target for `REQ-010` (see `UNK-02`; the original target,
`docs/03_rag_90_inconsistencies_and_known_issues.md`, was consolidated into this
document and deleted on 2026-09-03).

## Scope
- **In scope**: add one new Part 1 Known Issue entry, `RAG-007`, using the 16-field
  template, following the `SHARED-002`/`RAG-006` "resolved-but-retained" pattern
  already established in this document.
- **Out of scope**: any other Known Issue entry in this document, including `RAG-006`
  (a separate, non-overlapping entry added by the sibling
  `plans/done/20260903-085152_plan.md`'s REQ-012 — see Assumptions); Part 2 (Needs
  Confirmation Inventory); the Consolidation Note or Active Items section header.

## Assumptions
- **Cross-Plan ID coordination**: `implementations/20260903-121706_08_docs_00_governance_03_issue-and-uncertainty-management.md.md`
  (sibling `plans/done/20260903-085152_plan.md`'s row 8, a separate, already-archived
  Plan) reserves `RAG-006` for an unrelated topic (the `read_json_file()`/strict-reader
  documentation gap) in this same document. This row uses `RAG-007` instead of
  `RAG-006` to avoid a collision. Both entries are pending implementation as of this
  document's creation — re-verify at implementation time (immediately before editing)
  that neither `RAG-006` nor `RAG-007` has already been claimed by a third Plan, and
  that whichever of these two sibling rows is implemented first does not shift the
  other's intended number (if `RAG-006` is taken by the time this row is implemented,
  use the next number after whatever is highest at that moment, not blindly `RAG-007`).

## Design decisions
- Follow the `SHARED-002`/`RAG-006` precedent (`Status: resolved`, `Recommended
  Action` prefixed "Resolved —", retained pending a future review) for the same
  reasoning as `RAG-006`: this document's Lifecycle removes resolved items from the
  active inventory, but `REQ-010` explicitly asks for a record of this resolution.
- Insert immediately after whichever `RAG-*` entry is highest at implementation time
  (expected to be `RAG-006` immediately after this correction, but re-verify — see
  Assumptions) and before `#### DESIGN-1`, keeping all `RAG-*` entries contiguous in
  ID order.

## Alternatives considered
- Reuse `RAG-006`: rejected — already reserved by the sibling Plan's row 8 for an
  unrelated topic; reusing it would create a genuine ID collision once both
  procedures are implemented.
- Add to Part 2 instead of Part 1: rejected — same reasoning as `RAG-006`: this is a
  resolved documentation-vs-code mismatch (Known Issue territory), not an unconfirmed
  claim (Part 2's subject).

## Implementation
### Target file
`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure
Insert a new `#### RAG-007` entry immediately after whichever `RAG-*` entry is highest
at implementation time (before `#### DESIGN-1`).

### Method
Use `Edit`, anchoring on the exact final line of the then-highest `RAG-*` entry and the
`#### DESIGN-1` heading, to insert between them without altering either. If
`plans/done/20260903-085152_plan.md`'s row 8 (`RAG-006`) has already been implemented
by the time this row is implemented, anchor on `RAG-006`'s final line instead of
`RAG-005`'s.

### Details
Insert the following content immediately before the `#### DESIGN-1` heading (i.e.
immediately after the then-highest `RAG-*` entry's final field):

```markdown
#### RAG-007

- **ID**: RAG-007
- **Title**: Documentation did not reflect Null Fill Mode's removal from `ETagManager`
- **Status**: resolved
- **Severity**: Medium
- **Area**: RAG
- **Type**: obsolete-description
- **Source**: `scripts/rag/ingestion/etag_manager.py`
- **Owner**: Team
- **First Found**: 2026-09-02
- **Target**: `docs/03_rag_02_06_ingestion_pipeline-supporting-components.md`
- **Related**: N/A: no related active Known Issue
- **Summary**: `issues/done/20260828_01_remove-fetched-at-null-fill-and-mandatory-contract.md` removed `_update_null_fill()` and made `fetched_at` mandatory on `ChunkDocument`/`ETagManager.update()`/`DocumentManager.handle_existing_document()`, but that change's Documentation Impact was limited to docstrings — the `docs/03_rag_*.md` Specification set was not updated to reflect Null Fill Mode's removal, `fetched_at`'s mandatory status, or several ETagManager freshness-comparison edge cases (invalid timestamps, equal timestamps, missing stored timestamp) newly relevant once the fallback path was gone.
- **Current Description**: `scripts/rag/ingestion/` no longer contains any `_update_null_fill`, `null_fill`, or `COALESCE` reference (confirmed via repository-wide search). The `docs/03_rag_*.md` Specification set now states Freshness Mode as `ETagManager`'s only update mode, documents `fetched_at` as a required field on `ChunkDocument`, and documents the invalid-incoming-timestamp, invalid-stored-timestamp, equal-timestamp, and missing-stored-timestamp outcomes in this document's Target above.
- **Observed Implementation**: Explicit in code — `scripts/rag/ingestion/etag_manager.py`'s `ETagManager` has a single update path (`_update_with_freshness()`), gated by `_is_stale_update()`; `ChunkDocument.fetched_at`, `ETagManager.update()`'s `new_fetched_at`, and `DocumentManager.handle_existing_document()`'s `fetched_at` are all typed `str`, not `str | None`.
- **Impact**: Prior to resolution, a reader of the Specification set could believe missing-`fetched_at` fallback handling (Null Fill Mode) still existed, or could be unaware of the freshness-comparison edge cases introduced by its removal.
- **Recommended Action**: Resolved — the `docs/03_rag_*.md` Specification set was updated to document `fetched_at` as required, Freshness Mode as the only update mode, and the invalid-timestamp/equal-timestamp/missing-stored-timestamp edge cases, cross-linked from the ingester and document-manager documents rather than duplicated. (Action already taken via `plans/done/20260903-085718_plan.md`; entry retained per this template pending removal at next review, matching the `SHARED-002`/`RAG-006` precedent in this document.)
```

Repository evidence: `docs/00_governance_03_issue-and-uncertainty-management.md:101-156`
(`RAG-003`–`RAG-005` entries, used as the insertion-anchor and ID-numbering baseline);
`implementations/20260903-121706_08_docs_00_governance_03_issue-and-uncertainty-management.md.md`
(sibling Plan's `RAG-006` reservation, confirming the collision this row avoids by
using `RAG-007`); `grep -rn "_update_null_fill|null_fill|COALESCE" scripts/rag/ingestion/`
returns no matches (confirmed during row 2 of this Plan and re-confirmed here) — all
confirmed by direct read/search during this document's creation.

## Compatibility considerations
N/A: documentation-only; no code change. Sequencing note: if this row's edit lands
before the other five documents in this Plan, this entry's claims about their content
will be temporarily ahead of the actual document state until those edits land; no
other document links to this entry, so no broken-link risk. See Assumptions for the
`RAG-006`/`RAG-007` numbering coordination with the sibling Plan.

## Security considerations
N/A: documentation-only, no security-relevant behavior described or changed.

## Rollback considerations
Revert via `git checkout` on this file only; no data migration or dependent artifact
regeneration involved. Reverting this entry does not affect the other five documents
in this Plan (no reverse dependency).

## Validation plan
Run `uv run python tools/check_docs_quality.py` and `uv run python
tools/check_docs_consistency.py --domain rag` against this file (per Plan Validation
plan); re-confirm the `RAG-007` ID does not collide with `RAG-006` or any entry added
by another in-flight Plan since this document's re-read at implementation time.

## Completion criteria
`docs/00_governance_03_issue-and-uncertainty-management.md` Part 1 contains exactly one
new entry (`RAG-007`, or the next available `RAG-*` ID if a collision is found at
implementation time) with all 16 required fields populated, documenting Null Fill
Mode's removal as resolved.

## Out of scope
- Any other Known Issue entry in this document, including `RAG-006`.
- Part 2, the Consolidation Note, or the Active Items header.
- Any change to `scripts/rag/ingestion/etag_manager.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Re-check next available `RAG-*` ID immediately before inserting (coordinate with sibling Plan's `RAG-006`) |
| 2 | Add or update tests per Validation plan | N/A | — | — | No tests required — documentation-only (Plan Tests section) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | `check_docs_quality.py`, `check_docs_consistency.py --domain rag` |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | This document IS the documentation update |

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
- **Requirement ID**: REQ-010
- **Source issue**: issues/20260902-143329_ragfreshness_unify_fetched_at_etag_freshness_docs_remove_null_fill.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-085718_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-122926
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md
