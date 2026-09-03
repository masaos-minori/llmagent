## Goal
Cross-link the existing "Freshness Guard for Skip Path" description to the extended
`ETagManager` edge-case description (`REQ-004`), and confirm this file already treats
`fetched_at` as a required, non-optional parameter, requiring no further change for
`REQ-002` beyond the link.

## Scope
- **In scope**: append a cross-link to the first "Freshness Guard for Skip Path"
  bullet (under "## 4.") pointing to the new `ETagManager` edge-case subsection (row 2
  of this Plan).
- **Out of scope**: the duplicate "Freshness Guard for Skip Path" bullet under this
  document's "## 4a." section (pre-existing duplicate-header structure, not in this
  Plan's scope — same out-of-scope reasoning as the sibling `plans/done/20260903-085152_plan.md`'s
  row 3 for this same file); this document's "4.1 Class Overview" and "4.6 Error
  Handling" content (owned by that sibling Plan's row 3, a separate, non-overlapping
  edit — see Assumptions); modifying `scripts/rag/ingestion/ingester.py`.

## Assumptions
- **Cross-Plan awareness (non-conflicting)**: `implementations/20260903-121706_03_docs_03_rag_02_04_ingestion_pipeline-ingester.md.md`
  (`plans/done/20260903-085152_plan.md`'s row 3, a separate, already-archived Plan)
  also targets this file, editing the "4.1 Class Overview" paragraph and the first
  "4.6 Error Handling" table row. This row's edit (the "4.2 Detailed Behavior" section's
  "Freshness Guard for Skip Path" bullet) is a distinct, non-overlapping anchor — no
  conflict expected regardless of which Plan's edit lands first. Confirmed via direct
  read of the current file: `REQ-002`'s underlying fact (`fetched_at: str`, not
  `str | None`, in both `RagIngester` and `DocumentManager` signatures) is not
  separately stated as prose in this file today, but the existing bullet already says
  "All callers now provide `fetched_at`; there is no fallback path for missing
  timestamps" — judged sufficient for `REQ-002`'s intent once cross-linked to the
  `ETagManager` subsection's fuller error-handling detail; no separate `REQ-002`
  sentence is added here to avoid restating what the cross-link already covers.

## Design decisions
- Append the cross-link to the end of the existing bullet rather than rewriting it —
  the bullet's existing claim is accurate (confirmed by this Plan's own Reference
  Files evidence, `docs/03_rag_02_04_ingestion_pipeline-ingester.md:67`), so only a
  pointer to the newly-added edge-case detail (row 2) is needed.

## Alternatives considered
- Restate the full edge-case list (invalid timestamps, equal timestamps,
  missing-stored-timestamp) inline in this bullet instead of linking: rejected — this
  is exactly the duplication `REQ-004`'s cross-linking approach (see Plan Design
  section) is meant to avoid.

## Implementation
### Target file
`docs/03_rag_02_04_ingestion_pipeline-ingester.md`

### Procedure
Append a cross-link sentence to the first "Freshness Guard for Skip Path" bullet
(under the "## 4." section, not its duplicate under "## 4a.").

### Method
Use `Edit`, anchored on the exact existing bullet text shown below, matching only its
first occurrence (the duplicate under "## 4a." is out of scope — see Out of scope).

### Details
Replace the first occurrence of:
```
- **Freshness Guard for Skip Path:** Compares the input `fetched_at` (from the chunk payload) with the stored `documents.fetched_at`. If the input is older, the update is skipped (ensures newer crawls take precedence over older ones overwriting metadata). All callers now provide `fetched_at`; there is no fallback path for missing timestamps.
```
with:
```
- **Freshness Guard for Skip Path:** Compares the input `fetched_at` (from the chunk payload) with the stored `documents.fetched_at`. If the input is older, the update is skipped (ensures newer crawls take precedence over older ones overwriting metadata). All callers now provide `fetched_at`; there is no fallback path for missing timestamps. For the full set of edge cases (invalid timestamps, equal timestamps, missing stored timestamp) and error conditions, see [03_rag_02_06_ingestion_pipeline-supporting-components.md section 4.8.1](03_rag_02_06_ingestion_pipeline-supporting-components.md#481-freshness-comparison-edge-cases-and-error-handling).
```
Repository evidence: `docs/03_rag_02_04_ingestion_pipeline-ingester.md:67` (existing
bullet text, confirmed accurate and unchanged as of this document's creation — the
sibling Plan's row 3 does not touch this bullet); `scripts/rag/ingestion/document_manager.py:55`
and `scripts/rag/ingestion/etag_manager.py:27` (`fetched_at: str`, not `Optional`, in
both signatures, supporting the bullet's "no fallback path" claim) — confirmed by
direct read during this document's creation.

## Compatibility considerations
N/A: documentation-only; no code or behavior change. The added link depends on row 2's
new "4.8.1" subsection existing — verify it resolves after row 2's edit lands (per this
Plan's Validation plan link/cross-check).

## Security considerations
N/A: documentation-only, no security-relevant behavior described or changed.

## Rollback considerations
Revert via `git checkout` on this file only; no data migration or dependent artifact
regeneration involved.

## Validation plan
Run `uv run python tools/check_docs_quality.py` and `uv run python
tools/check_docs_consistency.py --domain rag` against this file (per Plan Validation
plan); manually confirm the added link resolves to row 2's new subsection (per Plan
Validation plan's manual cross-check row).

## Completion criteria
The first "Freshness Guard for Skip Path" bullet links to the extended `ETagManager`
edge-case subsection instead of leaving those edge cases undocumented from this file's
perspective.

## Out of scope
- The duplicate "Freshness Guard for Skip Path" bullet under this document's "## 4a."
  section.
- This document's "4.1 Class Overview" and "4.6 Error Handling" content (sibling
  Plan's row 3).
- Any change to `scripts/rag/ingestion/ingester.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260903-174900 | 20260903-174900 | Adversarially re-verified: bullet text unchanged since Plan creation (sibling `ragcontract` row 3 did not touch this anchor); `document_manager.py`/`etag_manager.py` signatures confirmed `fetched_at`/`new_fetched_at: str` (not Optional). Edited only the first occurrence (duplicate section structure ambiguous for Edit's string match — used precise line-index replacement) |
| 2 | Add or update tests per Validation plan | N/A | — | — | No tests required — documentation-only (Plan Tests section) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260903-174900 | 20260903-174900 | `check_docs_quality.py`: 0 errors. `check_docs_structure.py`: pre-existing "3 H1 headings" finding only (no broken-link finding — the new cross-link to row 2's anchor resolves); `check_docs_consistency.py --domain rag`: no findings for this file |
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
- **Requirement ID**: REQ-002, REQ-004
- **Source issue**: issues/20260902-143329_ragfreshness_unify_fetched_at_etag_freshness_docs_remove_null_fill.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-085718_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-122926
- **Related target files**: docs/03_rag_02_04_ingestion_pipeline-ingester.md
