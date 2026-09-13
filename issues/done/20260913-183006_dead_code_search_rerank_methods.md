# Issue: Dead Code References in SearchStages Documentation

## Summary
`docs/03_rag_03_04_query_pipeline-search-stages.md` notes that `RagPipeline.search_queries()` and `RagPipeline.rerank_candidates()` are defined in `pipeline.py` but have no callers — they are dead code.

## Evidence
- File: `docs/03_rag_03_04_query_pipeline-search-stages.md`, section 5.2
- Text: "While `RagPipeline.search_queries()` and `RagPipeline.rerank_candidates()` are defined in `pipeline.py`, neither has any callers (dead code). Actual search and reranking logic is executed in `SearchStage.run()` and `RerankStage.run()`."
- These methods exist in `scripts/rag/pipeline.py` but are never invoked anywhere in the codebase

## Impact
- Dead code increases maintenance burden and potential confusion during audits
- Future developers may assume these methods are used when they are not
- If someone modifies these methods expecting them to affect behavior, changes will have no effect

## Recommended Action
Remove `RagPipeline.search_queries()` and `RagPipeline.rerank_candidates()` from `scripts/rag/pipeline.py`. Update documentation to clarify that search and reranking are handled exclusively by `SearchStage.run()` and `RerankStage.run()`.
