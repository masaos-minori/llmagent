# Document the ETagManager doc_id=0 bug accurately across docs/03_rag_02_04-part1, 02_05, 02_06

## Priority
High

## Summary
`docs/03_rag_02_04_ingestion_pipeline-ingester-part1.md` incorrectly states that the skip-path guard causes etag/last_modified to be updated; `docs/03_rag_02_05_ingestion_pipeline-document-manager.md` is cited as the reference for this behavior but contains no actual description; `docs/03_rag_02_06_ingestion_pipeline-supporting-components.md` treats the issue as an unconfirmed "Needs confirmation" item, when code reading (`_update_etag()` constructing `ETagManager(self._db, 0)`) confirms it as a definite bug, not a possibility.

## Reason for Change
Once the underlying code bug is fixed (tracked in a separate implementation issue), or even before it's fixed, these 3 files must accurately reflect current behavior rather than asserting an incorrect "it works" claim or treating a confirmed fact as merely uncertain.

## Implementation Intent
Until the code fix lands, describe the bug as a confirmed known issue in all 3 files with consistent wording, cross-referencing `docs/03_rag_90_inconsistencies_and_known_issues.md`. Once the code fix (tracked separately) lands, update the wording to describe the corrected, working behavior instead.

## Target Files or Areas
`docs/03_rag_02_04_ingestion_pipeline-ingester-part1.md`, `docs/03_rag_02_05_ingestion_pipeline-document-manager.md`, `docs/03_rag_02_06_ingestion_pipeline-supporting-components.md`

## Required Changes
- In `02_04-part1`, replace "etag/last_modified is updated" with: "Known issue (confirmed): `_update_etag()` constructs `ETagManager(self._db, 0)` without passing the real document ID, so `UPDATE ... WHERE doc_id = 0` does not match any existing document (`doc_id` starts at 1) — etag/last_modified updates on the skip path are effectively a no-op. See `docs/03_rag_90_inconsistencies_and_known_issues.md` for detail."
- In `02_05`, add the actual description of this behavior (currently referenced but not described) or remove the reference if the description belongs solely elsewhere.
- In `02_06`, upgrade this item from "Needs confirmation" to a confirmed known issue, using consistent wording with `02_04-part1`.
- Coordinate timing with the separate implementation-fix issue: if that fix lands first, update all 3 files' wording to describe the corrected behavior instead of the bug.

## Acceptance Criteria
All 3 files describe the etag/last_modified update behavior consistently and accurately (as either a confirmed bug or, once fixed, as corrected working behavior) — no file asserts the pre-fix "it works" claim, and no file treats this as merely uncertain.

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
3 files corrected for consistency; depends on / should be re-synced with the separate implementation-fix issue's outcome.

## Out of Scope
Do not fix the actual code bug in this issue — that is tracked separately. Do not add the Known Issues entry to `docs/03_rag_90` in this issue (tracked in the broader Known Issues population issue) — only cross-reference it.

## AI Implementation Instruction
Check whether the related implementation-fix issue has already landed before writing this documentation — if it has, describe the corrected behavior; if not, describe the confirmed bug using consistent wording across all 3 files.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_rag.md §1 (横断的な確定済み誤り item 3), §4 強化候補 (02_06 ETagManager), §5 例3, §6A (ETagManager doc_id=0固定値問題)
- Generated at: 2026-08-02
