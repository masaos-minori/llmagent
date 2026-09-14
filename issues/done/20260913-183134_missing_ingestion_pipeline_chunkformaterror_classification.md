# Issue: Missing Documentation for RAG Ingestion Pipeline Utils ChunkFormatError Classification

## Summary
`docs/03_rag_05_4-error-handling-reference.md` mentions `ChunkFormatError` but doesn't explain its relationship to the broader exception hierarchy or when it should be raised vs caught.

## Evidence
- File: `docs/03_rag_05_4-error-handling-reference.md`, Pipeline Utils — Artifact Validation section
- Text: "Both canonical artifact readers (`scripts/rag/ingestion/pipeline_utils.py`) raise `ChunkFormatError` (`scripts/rag/exceptions.py:27`, a `RagLayerError` and `ValueError` subclass) on any validation failure"
- The exception class is mentioned but its role in the hierarchy isn't explained
- No guidance on whether callers should catch this specific exception or rely on the base class

## Impact
- Developers adding new validation logic may not know which exception to raise
- Error handling code may miss catching `ChunkFormatError` if relying on wrong base class
- The exception hierarchy becomes harder to navigate without documentation

## Recommended Action
Add a subsection documenting:
1. Where `ChunkFormatError` fits in the exception hierarchy
2. When it should be raised vs other exceptions
3. What callers should catch (specific vs base class)
4. Any known edge cases where the wrong exception type is used
