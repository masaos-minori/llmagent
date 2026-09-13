# Issue: Missing Documentation for RAG Ingestion Pipeline Utils Cross-Field Rules

## Summary
`docs/03_rag_02_01_ingestion_pipeline-overview.md` mentions cross-field rules but doesn't explain what they are or why they exist.

## Evidence
- File: `docs/03_rag_02_01_ingestion_pipeline-overview.md`, File Lifecycle section
- Text: "> Cross-field rules: `ContentOnly` chunks always have `normalized_content=None`; `NormalizedContent` chunks always have `content=None`."
- The rule is stated without explanation of its purpose or implications
- No documentation on how these rules affect downstream processing

## Impact
- Developers modifying chunk creation logic may violate these rules unknowingly
- Operators can't predict which fields will be populated for different chunk types
- The rules become harder to maintain without clear rationale

## Recommended Action
Add a dedicated subsection explaining:
1. Why `ContentOnly` chunks have `normalized_content=None`
2. Why `NormalizedContent` chunks have `content=None`
3. How these rules affect downstream processing
4. Any known edge cases where the rules are violated
