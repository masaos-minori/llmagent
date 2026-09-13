# Fix HTTP augment fallback chain identity vs truthiness bug

## Priority
Medium

## Summary
Fix the HTTP augment fallback logic that uses `or` operator to chain fallbacks, causing `None` results to short-circuit and skip subsequent fallback stages. When HttpAugment returns None (e.g., due to network error), the `or` expression evaluates to the next value immediately, bypassing the semantic cache check entirely.

## Background
In augment() (pipeline.py:104-112), the fallback chain is:
```python
ctx = await self.http_augment.run(ctx)
if ctx.reranked is None:
    ctx = await self.semantic_cache.run(ctx)
    if ctx.reranked is None:
        # ... execute pipeline
```

However, in pipeline_service.py (call_rag_service()), the fallback chain uses `or`:
```python
result = await self.http_augment.run(ctx) or await self.semantic_cache.run(ctx) or await self.pipeline.run(ctx)
```

The `or` operator checks truthiness, not None specifically. While None is falsy, this creates subtle bugs when a stage returns a non-None result that is semantically empty (e.g., empty list, zero-score result).

## Problem
1. In pipeline_service.py: `or` chaining means if HttpAugment returns None, it falls through to semantic_cache, then pipeline. But if HttpAugment returns an empty list `[]`, it's also falsy and would fall through — however, the intent was to only fall through on None, not on empty results.
2. The two patterns are inconsistent: pipeline.py uses explicit `is None` checks, pipeline_service.py uses `or`.
3. If HttpAugment returns a valid but empty result (no external data found), the `or` would skip it and try semantic cache — potentially returning stale cached data instead of fresh empty results.

## Reason for Change
Align the fallback logic across both code paths. Use explicit `is None` checks consistently to distinguish between "no result available" (None) and "empty result" ([]).

## Implementation Intent
Replace `or` chaining in pipeline_service.py with explicit `is None` checks matching the pattern in pipeline.py. This ensures:
- None → try next fallback
- Empty list [] → use as-is (valid result, just empty)
- Non-empty list → use as-is

## Target Files or Areas
- scripts/rag/pipeline_service.py

## Required Changes
- Replace `or` chaining in call_rag_service() with explicit `is None` checks
- Ensure consistent behavior with pipeline.py's augment() method

## Constraints
- Must preserve existing fallback order: http_augment → semantic_cache → pipeline → refiner
- Must not change the semantics of what constitutes a "fallback" (only None triggers fallback)
- Must not break existing tests

## Acceptance Criteria
- HttpAugment returning None triggers fallback to semantic_cache
- HttpAugment returning empty list [] is used as-is (not treated as None)
- Behavior matches pipeline.py's augment() method
- All existing tests pass after changes

## Testing Expectations
- Add test verifying HttpAugment returning [] does NOT trigger fallback
- Add test verifying HttpAugment returning None DOES trigger fallback
- Run: pytest tests/mcp_servers/rag_pipeline/

## Documentation Impact
Update docstring of call_rag_service() to document the fallback chain behavior explicitly.

## Out of Scope
- Changing the fallback order
- Adding new fallback stages
- Changes to HttpAugment's return values

## Dependencies
N/A: none

## Unresolved Questions
Should we define a sentinel object (e.g., `_NO_RESULT`) instead of using None to make the distinction clearer?

## AI Implementation Instruction
1. Read scripts/rag/pipeline_service.py
2. Find the `or` chaining in call_rag_service() (around line 104-112)
3. Replace:
   ```python
   result = await self.http_augment.run(ctx) or await self.semantic_cache.run(ctx) or await self.pipeline.run(ctx)
   ```
   With:
   ```python
   result = await self.http_augment.run(ctx)
   if result is None:
       result = await self.semantic_cache.run(ctx)
   if result is None:
       result = await self.pipeline.run(ctx)
   ```
4. Do NOT change pipeline.py's augment() method (already correct)
5. Run pytest tests/mcp_servers/rag_pipeline/ to verify

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260913-163623
- **Related target files**: scripts/rag/pipeline_service.py
