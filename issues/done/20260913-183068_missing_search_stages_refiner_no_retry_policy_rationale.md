# Issue: Missing Documentation for RAG Search Stages Refiner No-Retry Policy Rationale

## Summary
`docs/03_rag_03_04_query_pipeline-search-stages.md` mentions a no-retry policy for the refiner stage but doesn't explain why retries aren't attempted.

## Evidence
- File: `docs/03_rag_03_04_query_pipeline-search-stages.md`, section 4.1
- Text: "**No-Retry Policy:** The refiner stage does not retry failed requests; if the first attempt fails, the query proceeds with reduced context rather than retrying."
- The rationale for this design decision isn't documented
- No explanation of what happens when the refiner fails vs succeeds

## Impact
- Developers modifying the refiner stage may not understand the retry policy implications
- Operators can't determine whether a reduced-context result is expected behavior
- The policy becomes harder to enforce without clear rationale

## Recommended Action
Add a dedicated subsection explaining:
1. Why retries aren't attempted for the refiner stage
2. What the refiner's purpose is and why it's optional
3. How the pipeline handles reduced context gracefully
4. Any known edge cases where the no-retry policy causes problems
