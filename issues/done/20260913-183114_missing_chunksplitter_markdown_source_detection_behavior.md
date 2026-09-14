# Issue: Missing Documentation for RAG ChunkSplitter Markdown Source Detection Behavior

## Summary
`docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md` describes markdown source detection but doesn't explain why `.md`/`.markdown`/`.mdx` URLs always use heading chunking regardless of `md_index_enable`.

## Evidence
- File: `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md`, section 3a
- Text: "URLs ending in `.md`, `.markdown`, or `.mdx` always use heading chunking regardless of `md_index_enable`. For other files, heuristic detection (two or more heading lines in content) is used only if `md_index_enable=true`."
- The rationale for this distinction is undocumented — why should file extension determine chunking strategy?
- No documentation explains the design decision behind this behavior

## Impact
- Operators cannot understand why certain files are chunked differently
- New developers may not realize they can override this behavior with `md_index_enable`
- The distinction between URL-based and file-based chunking is unclear

## Recommended Action
Add a dedicated subsection explaining:
1. Why `.md`/`.markdown`/`.mdx` URLs always use heading chunking
2. The historical reason for this distinction
3. How to override the behavior for non-URL sources
4. Any known edge cases where this behavior causes problems
