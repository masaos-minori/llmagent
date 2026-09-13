# Fix SearchDiagnostics.degraded field inconsistency during search execution

## Priority
Medium

## Summary
Set the `degraded` field to True in SearchDiagnostics when embed_failed > 0 or fts_errors > 0 during search execution. Currently the field defaults to False even when search results are degraded, making diagnostics misleading.

## Background
SearchDiagnostics has a `degraded: bool = False` field (models_result.py:106). PipelineDiagnostics.from_run_result() computes `degraded = embed_failed > 0 or fts_errors > 0` (diagnostics.py:45). However, _search_all_queries() in stages/search.py returns SearchDiagnostics without setting degraded:

```python
return all_results, SearchDiagnostics(
    embed_ok=embed_ok,
    embed_failed=embed_failed,
    fts_errors=fts_errors,
)
```

This means the degraded field is False during search execution but becomes True after pipeline diagnostics collection.

## Problem
Callers that read ctx.search_diagnostics.degraded immediately after SearchStage.run() get False even when search was degraded. This causes:
1. Misleading diagnostic reports showing degraded=False despite failed embeddings
2. Inconsistent state between intermediate and final diagnostics
3. Potential silent acceptance of degraded search results

## Reason for Change
The degraded field should reflect the actual state at each point in time. Setting it during search execution ensures consistency and allows callers to make informed decisions about result quality.

## Implementation Intent
In _search_all_queries() (stages/search.py), compute degraded = embed_failed > 0 or fts_errors > 0 and include it in the SearchDiagnostics constructor call. This mirrors the logic in SearchDiagnostics.from_run_result().

## Target Files or Areas
- scripts/rag/stages/search.py

## Required Changes
- In _search_all_queries(): add `degraded = embed_failed > 0 or fts_errors > 0` before the return statement
- Pass `degraded=degraded` to the SearchDiagnostics constructor

## Constraints
- Must not change the SearchDiagnostics dataclass definition
- Must not affect the existing logging behavior (warnings already emitted)
- Must maintain backward compatibility — degraded defaults to False for new instances

## Acceptance Criteria
- SearchDiagnostics.degraded is True when embed_failed > 0 or fts_errors > 0
- SearchDiagnostics.degraded is False when all queries succeed
- Existing tests that check search_diagnostics fields pass after changes
- Pipeline diagnostics remain consistent with search diagnostics

## Testing Expectations
- Add test verifying degraded=True when embed_failed > 0
- Add test verifying degraded=True when fts_errors > 0
- Add test verifying degraded=False when all queries succeed
- Run: pytest tests/rag/test_rag_stages.py -k TestSearchDiagnostics

## Documentation Impact
Update docstring of SearchDiagnostics.degraded field to clarify it reflects real-time degradation status during search.

## Out of Scope
- Changes to SearchDiagnostics dataclass structure
- Changes to PipelineDiagnostics.from_run_result() logic
- Changes to warning log messages

## Dependencies
N/A: none

## Unresolved Questions
N/A: none

## AI Implementation Instruction
1. Read scripts/rag/stages/search.py
2. Find the return statement in _search_all_queries() (around line 69-73)
3. Before `return all_results, SearchDiagnostics(...)`, add:
   ```python
   degraded = embed_failed > 0 or fts_errors > 0
   ```
4. Add `degraded=degraded` as a keyword argument to SearchDiagnostics()
5. Run pytest tests/rag/test_rag_stages.py to verify existing tests pass

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260913-163623
- **Related target files**: scripts/rag/stages/search.py
