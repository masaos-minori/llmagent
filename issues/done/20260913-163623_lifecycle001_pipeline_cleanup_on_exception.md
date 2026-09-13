# Add pipeline lifecycle cleanup on exception to prevent resource leaks

## Priority
Medium

## Summary
Add try/finally blocks around pipeline stage execution to ensure database connections are closed and resources are cleaned up even when exceptions occur during stage processing. Currently, if a stage raises an exception, the RagDatabaseConnection context manager may not close properly.

## Background
RagPipeline.run() uses RagDatabaseConnection as a context manager:
```python
async with RagDatabaseConnection(db_path=self.db_path) as conn:
    # ... execute stages
```

However, individual stages (e.g., MqeStage.run(), SearchStage.run()) also use their own database connections internally. If a stage fails mid-execution, the connection may remain open until garbage collection.

Additionally, _search_all_queries() creates multiple concurrent tasks via asyncio.gather(). If one task fails, others may hang waiting for results.

## Problem
1. Resource leak: Open database connections during exception handling
2. Connection pool exhaustion under high load
3. Stale transactions holding locks on SQLite database
4. Potential data corruption if partial writes complete during failure

## Reason for Change
Ensure deterministic resource cleanup regardless of exception path. This includes:
1. Wrapping each stage's run() in try/finally for connection cleanup
2. Adding timeout to asyncio.gather() to prevent hanging tasks
3. Ensuring RagDatabaseConnection.__aexit__() always closes the connection

## Target Files or Areas
- scripts/rag/pipeline.py
- scripts/rag/stages/search.py
- scripts/rag/db_connection.py

## Required Changes
- Add try/finally around stage execution in RagPipeline.run()
- Add timeout parameter to asyncio.gather() in _search_all_queries()
- Verify RagDatabaseConnection.__aexit__() handles all cases correctly

## Constraints
- Must not change the RagDatabaseConnection interface
- Must not introduce performance regressions from added synchronization
- Must preserve existing error propagation behavior

## Acceptance Criteria
- Database connections closed even when exceptions occur
- asyncio.gather() timeouts prevent hanging tasks
- Existing tests pass after changes
- No resource leaks under stress testing

## Testing Expectations
- Add test verifying connection closure on exception
- Add test for asyncio.gather() timeout behavior
- Run: pytest tests/rag/test_rag_pipeline.py -k lifecycle

## Documentation Impact
Update RagPipeline.run() docstring to document resource cleanup guarantees.

## Out of Scope
- Adding distributed transaction support
- Changes to SQLite WAL mode configuration
- Implementing connection pooling beyond what RagDatabaseConnection provides

## Dependencies
N/A: none

## Unresolved Questions
Should we add a global timeout for the entire pipeline execution? This would require changes to the PipelineContext and all stage implementations.

## AI Implementation Instruction
1. Read scripts/rag/pipeline.py — find RagPipeline.run()
2. Wrap stage execution in try/finally:
   ```python
   async with RagDatabaseConnection(db_path=self.db_path) as conn:
       try:
           # existing stage execution
       finally:
           await self._cleanup_on_failure(ctx)
   ```
3. In _search_all_queries(): add timeout to asyncio.gather():
   ```python
   results = await asyncio.wait_for(
       asyncio.gather(*tasks, return_exceptions=True),
       timeout=self.config.search_timeout
   )
   ```
4. Verify RagDatabaseConnection.__aexit__() in db_connection.py handles all cases
5. Run pytest tests/rag/test_rag_pipeline.py to verify

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260913-163623
- **Related target files**: scripts/rag/pipeline.py, scripts/rag/stages/search.py, scripts/rag/db_connection.py
