# Issue: Missing Documentation for RAG Helpers and Cache Retrieval Freshness Guarantee

## Summary
`docs/03_rag_03_06_query_pipeline-helpers-and-cache.md` claims retrieval freshness is guaranteed without cache invalidation, but this guarantee lacks detailed explanation of how it works.

## Evidence
- File: `docs/03_rag_03_06_query_pipeline-helpers-and-cache.md`, section 6
- Text: "Every query executes the full retrieval pipeline (`SearchStage`, via `RagPipeline.augment()`) — including repeated identical queries. No query-result cache exists."
- The semantic cache described in `03_rag_01_system_overview.md` contradicts this claim
- The document doesn't explain how the semantic cache interacts with the "no cache" statement

## Impact
- Readers may be confused about whether there's a cache or not
- The semantic cache's role in the overall caching strategy is unclear
- Operators may misunderstand the system's consistency guarantees

## Recommended Action
Clarify the distinction between:
1. Query-result cache (doesn't exist — each query re-executes the pipeline)
2. Semantic cache (exists as an optimization layer before pipeline execution)
Document both mechanisms separately and explain their interaction. Update the semantic cache section in `03_rag_01_system_overview.md` to clarify its scope and limitations.
