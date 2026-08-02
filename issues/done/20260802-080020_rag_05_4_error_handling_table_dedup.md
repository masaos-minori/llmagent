# Simplify docs/03_rag_05_4 error-handling tables

## Priority
Medium

## Summary
`docs/03_rag_05_4-error-handling-reference.md`'s Crawler/ChunkSplitter/RagIngester error-case tables include detail (like retry counts) that duplicates the configuration reference.

## Reason for Change
Retry-count values maintained in 2 places (here and the configuration reference) risk silent divergence; the design-relevant content (whether retry occurs, and failure-continuation behavior) is more valuable than the specific numeric values, which change more often.

## Implementation Intent
Remove specific retry-count numbers from this file, deferring them to `docs/03_rag_05_1-configuration-reference.md`, while keeping the design-judgment content: whether retry happens at all, and what happens after retry exhaustion (continue vs. abort).

## Target Files or Areas
`docs/03_rag_05_4-error-handling-reference.md`

## Required Changes
- Remove specific retry-count numbers from the error-case tables; replace with a reference to `docs/03_rag_05_1-configuration-reference.md` for exact values.
- Keep (or add, if missing) the retry-existence and failure-continuation-behavior design judgments, e.g. "HTTPエラーはリトライ対象(回数は05_1参照)。リトライ上限到達後は当該ページをスキップし処理継続。"

## Acceptance Criteria
No specific retry-count number is duplicated in this file; retry-existence and failure-behavior design judgments remain, with numeric detail deferred to `05_1`.

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
`docs/03_rag_05_4` corrected and shortened.

## Out of Scope
Do not edit `docs/03_rag_05_1` in this issue (its own fixes tracked separately).

## AI Implementation Instruction
Verify the retry-existence and failure-continuation behavior for each component (Crawler/ChunkSplitter/RagIngester) against current source before finalizing, in case behavior has changed since this review.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_rag.md §3 要約候補 item 8
- Generated at: 2026-08-02
