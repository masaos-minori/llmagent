# Issue: Missing Documentation for RAG Pipeline Overview Fallback Chain Detail

## Summary
`docs/03_rag_03_01_query_pipeline-overview.md` describes the fallback chain but doesn't document what happens when each fallback stage fails.

## Evidence
- File: `docs/03_rag_03_01_query_pipeline-overview.md`, Query Pipeline Flow section
- Text: "- **Fallback Chain**: MQE → Search → RRF → Rerank → Augment — if any stage fails, downstream stages are skipped; partial results may be returned."
- The behavior of partial results isn't explained — which fields are populated?
- No guidance on how callers interpret partial results

## Impact
- Operators can't determine if a query failed partially vs completely
- Debugging requires understanding undocumented partial result format
- Callers may misinterpret incomplete results as valid responses

## Recommended Action
For each stage in the fallback chain, document:
1. What happens when the stage fails
2. Which fields are populated vs absent in partial results
3. How callers should detect partial failures
4. Any known edge cases where partial results cause problems
