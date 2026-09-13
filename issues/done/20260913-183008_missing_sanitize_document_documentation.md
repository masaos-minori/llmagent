# Issue: Missing Documentation for sanitize_document Function

## Summary
`docs/03_rag_03_02_query_pipeline-rag-pipeline-class.md` notes that `sanitize_document` is not provided by `rag/pipeline.py` but exists in `rag/utils.py`. This function's contract and behavior should be documented separately.

## Evidence
- File: `docs/03_rag_03_02_query_pipeline-rag-pipeline-class.md`, section 2
- Text: "> **Documentation vs. Implementation Mismatch**: `fetch_full_document` (`rag/repository.py`) and `sanitize_document` (`rag/utils.py`) are not provided by `rag.pipeline`. See [Part 1](03_rag_03_02_query_pipeline-rag-pipeline-class.md) for details."
- The function is imported and used but its detailed contract is not documented alongside the RagPipeline class

## Impact
- Developers unfamiliar with the codebase may not understand what `sanitize_document` does or how it affects output
- Without documentation, changes to this function could introduce unexpected side effects
- The function's role in preventing prompt injection attacks is critical but undocumented

## Recommended Action
Document `sanitize_document`'s contract, including:
1. What sanitization rules it applies
2. How it prevents prompt injection
3. Its return value format
4. Any known limitations or edge cases

Consider adding a dedicated section in `docs/03_rag_03_05_query_pipeline-augment-stages.md` or creating a separate document for utility functions.
