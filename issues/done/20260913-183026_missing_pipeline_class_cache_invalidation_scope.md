# Issue: Missing Documentation for RAG Pipeline Class Implementation Note Cache Invalidation

## Summary
`docs/03_rag_03_02_query_pipeline-rag-pipeline-class.md` notes that cache invalidation is caller responsibility but doesn't document what constitutes a "corpus change" that triggers invalidation.

## Evidence
- File: `docs/03_rag_03_02_query_pipeline-rag-pipeline-class.md`, Implementation Note section
- Text: "`invalidate_cache()` is intended to be called only after corpus changes that this pipeline instance is aware of; the caller (e.g., MCP service layer) is responsible for detecting corpus changes and explicitly calling it."
- The definition of "corpus change" isn't documented — does it include ingestion, deletion, or both?
- No guidance on how callers detect corpus changes

## Impact
- Callers may not know when to invalidate the cache
- Stale cache entries may persist indefinitely if corpus changes aren't detected
- Memory leaks from accumulated cache entries

## Recommended Action
Add a dedicated subsection documenting:
1. What constitutes a "corpus change" (ingestion, deletion, update)
2. How callers should detect corpus changes
3. The scope of `invalidate_cache()` (all caches vs specific ones)
4. Any known edge cases where cache invalidation fails
