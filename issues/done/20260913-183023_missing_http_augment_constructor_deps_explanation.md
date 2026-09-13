# Issue: Missing Documentation for RAG HTTP Augment Class Constructor Dependencies

## Summary
`docs/03_rag_03_05_query_pipeline-augment-stages.md` lists constructor dependencies for AugmentRefiner but doesn't explain why certain parameters are optional vs required.

## Evidence
- File: `docs/03_rag_03_05_query_pipeline-augment-stages.md`, section 5.6
- Text: "| Parameter | Type | Required | Description |" with entries like "`http`: `httpx.AsyncClient` | Yes | HTTP client for external RAG service calls"
- The distinction between required and optional parameters isn't explained
- Some parameters have default values ("defaults to no-op") but the rationale isn't documented

## Impact
- Developers extending the class may not understand which dependencies can be safely omitted
- The default behavior for optional parameters is undocumented beyond the brief description
- Future developers may add unnecessary dependencies or miss critical ones

## Recommended Action
Add a subsection explaining:
1. Why each parameter is required vs optional
2. What happens when optional parameters use their defaults
3. How the class behaves differently based on which dependencies are injected
4. Any known edge cases where omitting an optional parameter causes problems
