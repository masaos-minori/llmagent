# Issue: Missing Documentation for fetch_full_document Function

## Summary
`docs/03_rag_03_02_query_pipeline-rag-pipeline-class.md` notes that `fetch_full_document` is not provided by `rag/pipeline.py` but exists in `rag/repository.py`. This function's contract and behavior should be documented separately.

## Evidence
- File: `docs/03_rag_03_02_query_pipeline-rag-pipeline-class.md`, section 2
- Text: "> **Documentation vs. Implementation Mismatch**: `fetch_full_document` (`rag/repository.py`) and `sanitize_document` (`rag/utils.py`) are not provided by `rag.pipeline`. See [Part 1](03_rag_03_02_query_pipeline-rag-pipeline-class.md) for details."
- The function is imported and used but its detailed contract is not documented alongside the RagPipeline class

## Impact
- Developers unfamiliar with the codebase may not understand what `fetch_full_document` does or how it affects search results
- Without documentation, changes to this function could introduce unexpected side effects
- The function's role in fetching related chunks for context enrichment is critical but undocumented

## Recommended Action
Document `fetch_full_document`'s contract, including:
1. What parameters it accepts (chunk_id, db, window)
2. How the window parameter works (±N chunks from the source chunk)
3. Return value format and ordering guarantees
4. Any known limitations or edge cases

Consider adding a dedicated section in `docs/03_rag_03_06_query_pipeline-helpers-and-cache.md` where helper classes are already documented.
