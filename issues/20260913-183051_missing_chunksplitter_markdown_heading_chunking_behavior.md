# Issue: Missing Documentation for RAG ChunkSplitter Markdown Heading Chunking Behavior

## Summary
`docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md` describes markdown heading chunking behavior but doesn't explain the fallback mechanism when sections exceed `md_snippet_max_chars`.

## Evidence
- File: `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md`, section 3a
- Text: "Text is split by Markdown headings (# through ######). Sections exceeding `md_snippet_max_chars` characters are further split using sentence-based chunking."
- The fallback from heading chunking to sentence-based chunking isn't explained
- No documentation on how the two chunking strategies interact

## Impact
- Developers modifying chunking logic may not understand the interaction between strategies
- Operators can't predict chunk sizes for large sections
- Debugging oversized chunks requires understanding undocumented fallback behavior

## Recommended Action
Add a dedicated subsection explaining:
1. When heading chunking falls back to sentence-based chunking
2. How the two strategies combine (sequential vs parallel)
3. What happens to chunk metadata during fallback
4. Any known edge cases where fallback causes problems
