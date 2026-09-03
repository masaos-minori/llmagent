## Goal
Add a Known Issue entry (`RAG-006`) documenting the resolution of the
`read_json_file()`/strict-reader documentation gap, in
`docs/00_governance_03_issue-and-uncertainty-management.md` Part 1 — the corrected
target for `REQ-012` (see `UNK-03`; the original target,
`docs/03_rag_90_inconsistencies_and_known_issues.md`, was consolidated into this
document and deleted on 2026-09-03).

## Scope
- **In scope**: add one new Part 1 Known Issue entry, `RAG-006`, using the 16-field
  template, following the "resolved-but-retained" pattern already established by
  `SHARED-002` in this same document.
- **Out of scope**: any other Known Issue entry in this document; Part 2 (Needs
  Confirmation Inventory); the Consolidation Note or Active Items section header.

## Assumptions
- The next available `RAG-*` ID is `RAG-006` (highest existing is `RAG-005`) — this
  MUST be re-checked immediately before the edit, at implementation time, since another
  in-flight Plan could reserve it first (per this Plan's corrected Risks section).

## Design decisions
- Follow the `SHARED-002` precedent (same document, `Status: resolved`, `Recommended
  Action` prefixed "Resolved —", with a closing parenthetical noting the entry is
  retained pending a future review) rather than omitting the entry entirely — this
  document's stated Lifecycle removes resolved items from the active inventory, but an
  existing precedent already retains a just-resolved entry through one review cycle, and
  `REQ-012` explicitly asks for a record of the resolution, not silence.
- Insert immediately after the `RAG-005` entry (before `#### DESIGN-1`) to keep all
  `RAG-*` entries contiguous in ID order, matching this document's existing ordering.

## Alternatives considered
- Add the entry to Part 2 (Needs Confirmation Inventory) instead of Part 1: rejected —
  the gap being documented is a resolved documentation-vs-code mismatch (Known Issue
  territory), not an unconfirmed claim awaiting verification (Part 2's subject).
- Omit the entry entirely, since the document's Lifecycle removes resolved items:
  rejected — `REQ-012` requires a record of this resolution to exist, and the
  `SHARED-002` precedent already establishes that a just-resolved entry may be
  retained through one review cycle.

## Implementation
### Target file
`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure
Insert a new `#### RAG-006` entry immediately after the existing `#### RAG-005` entry's
final field and before the `#### DESIGN-1` heading.

### Method
Use `Edit`, anchoring on the exact existing `RAG-005` entry's final line and the
`#### DESIGN-1` heading, to insert between them without altering either.

### Details
Insert the following content immediately before the `#### DESIGN-1` heading (i.e.
immediately after `RAG-005`'s `- **Recommended Action**: ...` line):

```markdown
#### RAG-006

- **ID**: RAG-006
- **Title**: Documentation described `read_json_file()`'s lenient fallback behavior as a current production reader
- **Status**: resolved
- **Severity**: Medium
- **Area**: RAG
- **Type**: obsolete-description
- **Source**: `scripts/rag/ingestion/pipeline_utils.py`
- **Owner**: Team
- **First Found**: 2026-09-02
- **Target**: `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md`
- **Related**: N/A: no related active Known Issue
- **Summary**: `docs/03_rag_02_08_ingestion_pipeline-shared.md` documented `read_json_file()`'s lenient fallback behavior (`lang` default `"en"`, `chunk_index` default `0`, empty-string fallbacks) as a currently-relevant reader, even though the strict-reader migration (`read_crawl_json()`/`read_chunk_json()`, both raising `ChunkFormatError` on missing/invalid fields) had already superseded it in code.
- **Current Description**: `read_json_file()` remains in `scripts/rag/ingestion/pipeline_utils.py` (removal was out of scope for this resolution) but is confirmed unused by any current pipeline code path. The `docs/03_rag_*.md` Specification set now states `read_crawl_json()`/`read_chunk_json()` as the canonical readers, documents the `ChunkFormatError` failure mode, classifies every crawl/chunk field as Required/Nullable/Conditional in one canonical table (this document's Target), and marks `read_json_file()`'s description as historical in `docs/03_rag_02_08_ingestion_pipeline-shared.md`.
- **Observed Implementation**: Verified by test — `tests/rag/ingestion/test_pipeline_utils_strict.py` exercises `read_crawl_json()`/`read_chunk_json()`'s `ChunkFormatError` conditions; no test exercises `read_json_file()` as a production path.
- **Impact**: Prior to resolution, new artifact producers or future implementers reading the Specification set risked reintroducing lenient-fallback assumptions no longer valid against the strict readers.
- **Recommended Action**: Resolved — canonical-reader statements, the `ChunkFormatError` failure mode, and a single canonical Required/Nullable/Conditional field-contract table were added across the `docs/03_rag_*.md` Specification set, and `read_json_file()`'s description was relocated to a clearly marked historical section. (Action already taken via `plans/20260903-085152_plan.md`; entry retained per this template pending removal at next review, matching the `SHARED-002` precedent in this document.)
```

Repository evidence: `docs/00_governance_03_issue-and-uncertainty-management.md:139-156`
(`RAG-005` entry, used as the insertion anchor and ID-numbering baseline); `:348-365`
(`SHARED-002` entry, used as the resolved-entry-retention precedent); confirmed via
`test -f docs/03_rag_90_inconsistencies_and_known_issues.md` (missing) and `grep -n -i
"read_json_file|strict-reader|ChunkFormatError"` against this document's full content
(no matches) that no existing entry already covers this topic — both checks performed
during this Plan's Step 2 revalidation and re-confirmed during this document's
creation.

## Compatibility considerations
N/A: documentation-only; no code change. This entry references the other seven target
documents in this Plan by their resolved state — sequencing note: if this row's edit
lands before the other seven, the entry's claims about their content will be
temporarily ahead of the actual document state until those edits land; no other
document links to this entry, so no broken-link risk.

## Security considerations
N/A: documentation-only, no security-relevant behavior described or changed.

## Rollback considerations
Revert via `git checkout` on this file only; no data migration or dependent artifact
regeneration involved. Reverting this entry does not affect the other seven documents
in this Plan (no reverse dependency).

## Validation plan
Run `uv run python tools/check_docs_quality.py` and `uv run python
tools/check_docs_consistency.py --domain rag` against this file (per Plan Validation
plan); re-confirm the `RAG-006` ID does not collide with an entry added by another
in-flight Plan since this document's re-read at implementation time.

## Completion criteria
`docs/00_governance_03_issue-and-uncertainty-management.md` Part 1 contains exactly one
new entry (`RAG-006`, or the next available `RAG-*` ID if a collision is found at
implementation time) with all 16 required fields populated, documenting the
`read_json_file()`/strict-reader documentation gap as resolved.

## Out of scope
- Any other Known Issue entry, Part 2, or the Consolidation Note / Active Items header
  in this document.
- Any change to `scripts/rag/ingestion/pipeline_utils.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Re-check next available `RAG-*` ID immediately before inserting |
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
- **Requirement ID**: REQ-012
- **Source issue**: issues/20260902-143328_ragcontract_align_rag_artifact_contract_with_strict_reader_behavior.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-085152_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-121706
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md
