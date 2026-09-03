# Unify `fetched_at`/ETag freshness documentation and remove the legacy Null Fill contract

## Priority
High

## Summary
The current `ChunkDocument` contract and strict chunk reader require `fetched_at` as a
string, and `RagIngester` carries it through document lookup, insertion, and replacement as a
required value. Some Specification documents still describe a legacy path in which
`fetched_at` may be absent and ETag/Last-Modified are updated through a Null Fill Mode, and do
not clearly define behavior when an incoming or stored timestamp is malformed.

## Background
`issues/done/20260828_01_remove-fetched-at-null-fill-and-mandatory-contract.md` already
implemented the code-side change (`_update_null_fill()` removal, `fetched_at` made mandatory).
Its `Documentation Impact` was limited to docstrings and did not update the `docs/03_rag_*.md`
Specification set. This issue covers the remaining Specification-level documentation only.

## Problem
The documentation currently mixes three separate concerns without distinguishing them: legacy
compatibility for artifacts without `fetched_at`, current stale-update protection against
older artifacts overwriting newer metadata, and error handling when timestamps cannot be
parsed or compared. Without an explicit error policy documented, a malformed timestamp could
be misread as a non-stale value, leaving the documented data-integrity guarantee incomplete.

## Reason for Change
Removing the legacy path from documentation must not silently weaken the current freshness
guard's documented guarantee. An explicit, single freshness-update contract is needed so
readers cannot conflate the removed legacy behavior with current protection.

## Implementation Intent
Document one current freshness-update contract: `fetched_at` required for chunk artifacts;
incoming timestamp validated before metadata updates; incoming compared with stored timestamp;
older input does not overwrite ETag/Last-Modified/freshness metadata; missing or invalid
timestamps block the update; invalid input vs. invalid persisted state documented as distinct
failures; Null Fill Mode absent from the current specification after implementation removal.

## Target Files or Areas
- `docs/03_rag_02_04_ingestion_pipeline-ingester.md`
- `docs/03_rag_02_05_ingestion_pipeline-document-manager.md`
- `docs/03_rag_02_06_ingestion_pipeline-supporting-components.md`
- `docs/03_rag_04_01_dto-models_data.md`
- `docs/03_rag_05_1-configuration-reference.md`
- `docs/03_rag_05_4-error-handling-reference.md`
- `docs/03_rag_05_6-local-file-re-ingestion.md`
- `docs/03_rag_90_inconsistencies_and_known_issues.md`

## Required Changes
- Document `ChunkDocument.fetched_at` as a required string field; add it to the required-field list for chunk artifacts.
- State that missing `fetched_at` is rejected before database updates, and that `RagIngester`/`DocumentManager` treat it as required.
- Remove Null Fill Mode and `COALESCE`-based missing-`fetched_at` handling from the current `ETagManager` specification.
- Document freshness-based updates as the only current ETag update mode; state that older input leaves existing metadata unchanged.
- Define the accepted `fetched_at` timestamp format and whether timezone information is mandatory; if timezone-free values remain supported, document the UTC normalization rule.
- Define behavior for an invalid incoming timestamp and for an invalid timestamp already stored in the database, as distinct error classifications.
- State that ETag/Last-Modified are not updated when timestamps cannot be compared; document behavior when incoming and stored timestamps are equal, and when both ETag and Last-Modified are unavailable.
- Preserve the current SHA-256 freshness description for local-file ingestion; keep `force=True` re-ingestion behavior documented separately from backward compatibility.
- Find and correct every document that still describes chunk `fetched_at` as optional.
- Move required legacy history to Migration History or Change History.
- Register unresolved timestamp behavior as a Known Issue or Needs Confirmation until implementation is confirmed complete; mark the related issue resolved once documentation and implementation agree.

## Constraints
Documentation-only. Do not modify `_update_null_fill()`'s removal, implement fail-closed
timestamp handling, or repair existing database values as part of this issue.

## Acceptance Criteria
- No current chunk-artifact specification describes `fetched_at` as optional.
- Null Fill Mode is absent from current specifications.
- Legacy compatibility and current stale-update protection are clearly distinguished.
- Timestamp parse failures have explicit documented outcomes; invalid input and inconsistent persisted state are distinguished.
- Invalid input is not documented as a newer artifact by default.
- DTO, reader, ingester, document-management, and ETag documentation agree with each other.
- Legacy behavior appears only in clearly marked historical sections.

## Testing Expectations
Not required — documentation-only change. Verify with
`uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_consistency.py --domain rag`.

## Documentation Impact
Yes — this issue's entire scope is the `docs/03_rag_*.md` Specification set listed above,
building on `issues/done/20260828_01_remove-fetched-at-null-fill-and-mandatory-contract.md`'s
already-landed code change.

## Out of Scope
- Removing `_update_null_fill()` from source code (already done).
- Implementing fail-closed timestamp handling.
- Repairing existing database values.
- Defining timestamp rules outside the RAG ingestion domain.

## Dependencies
`issues/done/20260828_01_remove-fetched-at-null-fill-and-mandatory-contract.md` already
implemented the code-side change this issue documents.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Read `ETagManager`, `DocumentManager`, and `ChunkDocument`'s current implementation in full
before editing, to confirm the exact timestamp-comparison and error-handling behavior rather
than trusting this issue's restatement. If a specific edge-case behavior (e.g., equal
timestamps, both ETag and Last-Modified unavailable) cannot be confirmed from code, mark it
`Needs Confirmation` instead of guessing.
