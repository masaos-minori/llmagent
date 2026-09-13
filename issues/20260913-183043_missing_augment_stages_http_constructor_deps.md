# Issue: Missing Documentation for RAG Augment Stages HTTP Constructor Dependencies

## Summary
`docs/03_rag_03_05_query_pipeline-augment-stages.md` describes the HTTP constructor dependencies but doesn't explain why they're needed or how they interact.

## Evidence
- File: `docs/03_rag_03_05_query_pipeline-augment-stages.md`, section 5.1
- Text: "**Constructor Dependencies:** `__init__(self, embed_client, fetch_full_document, max_tokens)` — embed_client: embedding model client; fetch_full_document: function to fetch full document content; max_tokens: maximum token limit for embeddings."
- The interaction between these dependencies isn't explained
- No documentation on when each dependency is used during execution

## Impact
- Developers adding new dependencies won't know how to integrate them properly
- Operators can't debug issues caused by specific dependency failures
- The dependency graph becomes harder to understand without documentation

## Recommended Action
Add a dedicated subsection explaining:
1. Why each dependency is needed (beyond the brief description)
2. How the dependencies interact during execution
3. When each dependency is called
4. Any known edge cases where dependency failures cause problems
