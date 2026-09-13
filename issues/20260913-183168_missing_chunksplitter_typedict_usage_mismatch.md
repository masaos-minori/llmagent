# Issue: Missing Documentation for RAG ChunkSplitter TypedDict Usage Mismatch

## Summary
`docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md` notes that TypedDicts are declared but not used as type annotations, indicating a design gap between interface specification and implementation.

## Evidence
- File: `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md`, section 3
- Text: "> Evidence: Explicit in code — `CrawlFilePayload` and `ChunkOutputPayload` are declared as types in `chunk_splitter.py`, but they are not used as type annotations in the actual implementation within the same file (actual input/output is handled via `ChunkJsonRaw` (`pipeline_utils.py`) or `dict[str, object]`)."
- The TypedDicts serve as interface specifications but aren't enforced at runtime
- This creates a disconnect between documented contract and actual behavior

## Impact
- Type checking tools won't catch violations of the TypedDict contract
- Future developers may assume the TypedDicts are enforced when they're not
- The interface specification becomes stale without enforcement

## Recommended Action
Either:
1. Enforce TypedDict usage in the implementation (add type annotations)
2. Remove the TypedDict declarations if they're not intended for enforcement
3. Document the TypedDicts as "interface specification only" with clear rationale
