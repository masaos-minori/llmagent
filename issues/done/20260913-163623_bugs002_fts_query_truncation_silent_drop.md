# Fix FTS query truncation silent drop of long queries

## Priority
Medium

## Summary
Add bounds checking and warning logging when FTS queries exceed the configured maximum length. Currently, queries longer than max_query_length are silently truncated without any indication, causing retrieval failures for legitimate long inputs.

## Background
RagConfigImpl has `max_query_length: int` (default 512). _search_all_queries() in stages/search.py validates query lengths:
```python
for q in queries:
    if len(q) > self.config.max_query_length:
        logger.warning("Query too long (%d chars), skipping", len(q))
        fts_errors += 1
        continue
```

However, the validation only increments fts_errors and skips the query — it doesn't truncate or warn about partial retrieval. The user receives degraded results without knowing why.

## Problem
1. Silent degradation: Long queries are dropped entirely rather than being shortened intelligently
2. No user feedback: Users don't know their query was rejected
3. Potential security concern: An attacker could send very long queries to cause systematic query drops
4. No retry mechanism: Once dropped, there's no way to recover the missed content

## Reason for Change
Improve the handling of oversized queries by either:
A) Truncating the query to max_query_length and logging a warning (preserves retrieval)
B) Raising a clear error with guidance for the caller to shorten the input

Option A is recommended for better user experience; Option B for stricter API contracts.

## Target Files or Areas
- scripts/rag/stages/search.py

## Required Changes
- Replace `fts_errors += 1; continue` with truncation logic or explicit error raising
- Log appropriate warnings/errors based on chosen approach
- Update SearchDiagnostics.fetched_count to reflect actual retrieved chunks

## Constraints
- Must not change the max_query_length default value
- Must preserve backward compatibility — configs that currently work must still work
- Error messages must be actionable

## Acceptance Criteria
- Queries exceeding max_query_length are handled gracefully (truncated or error raised)
- Appropriate logging occurs for oversized queries
- Existing tests pass after changes
- SearchDiagnostics accurately reflects retrieval status

## Testing Expectations
- Add test for query exactly at max_query_length boundary
- Add test for query exceeding max_query_length
- Verify logging output contains expected message
- Run: pytest tests/rag/test_rag_stages.py -k TestSearchStage

## Documentation Impact
Update docstring of RagConfigImpl.max_query_length to clarify its purpose and behavior when exceeded.

## Out of Scope
- Changing the default max_query_length value
- Implementing query summarization or splitting
- Changes to the FTS search algorithm itself

## Dependencies
N/A: none

## Unresolved Questions
Should we implement automatic query splitting for long inputs (split into multiple queries)? This would require significant changes to the fusion/rerank logic.

## AI Implementation Instruction
1. Read scripts/rag/stages/search.py
2. Find the query length check (around line 69-73):
   ```python
   if len(q) > self.config.max_query_length:
       logger.warning("Query too long (%d chars), skipping", len(q))
       fts_errors += 1
       continue
   ```
3. For Option A (truncate): replace with:
   ```python
   if len(q) > self.config.max_query_length:
       logger.warning("Truncating query from %d to %d chars", len(q), self.config.max_query_length)
       q = q[:self.config.max_query_length]
   ```
4. For Option B (error): raise ValueError with a clear message
5. Start with Option A unless user requests Option B
6. Run pytest tests/rag/test_rag_stages.py to verify

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260913-163623
- **Related target files**: scripts/rag/stages/search.py
