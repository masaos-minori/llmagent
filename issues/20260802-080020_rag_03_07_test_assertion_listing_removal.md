# Simplify docs/03_rag_03_07 test-name/assertion listing

## Priority
Low

## Summary
`docs/03_rag_03_07_query_pipeline-tests.md`'s sections 8.1/8.2 transcribe 18 test names and their assertions verbatim.

## Reason for Change
Test code itself is the authoritative source for exact test names and assertions; verbatim transcription here doubles maintenance effort as tests evolve.

## Implementation Intent
Remove the verbatim test-name/assertion listing, keeping a summary of the "guaranteed properties" category these tests verify, and pointing to the test files themselves for exact detail.

## Target Files or Areas
`docs/03_rag_03_07_query_pipeline-tests.md`

## Required Changes
- Remove the verbatim 18-item test-name/assertion listing in sections 8.1/8.2.
- Keep or add a "guaranteed properties" summary describing what behavioral guarantees these tests collectively verify.
- Add a pointer to the actual test files for exact test names/assertions.

## Acceptance Criteria
No verbatim test-name/assertion listing remains; a "guaranteed properties" summary and a pointer to the test files remain.

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
`docs/03_rag_03_07` shortened.

## Out of Scope
Do not change the actual test files in this issue — documentation only.

## AI Implementation Instruction
Derive the "guaranteed properties" summary from the actual current test file content, not solely from this review's characterization, in case tests have changed since the review was written.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_rag.md §2 削除候補 item 8
- Generated at: 2026-08-02
