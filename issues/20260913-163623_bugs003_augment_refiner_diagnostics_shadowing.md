# Fix AugmentRefiner diagnostics shadowing bug

## Priority
Low

## Summary
Fix the AugmentRefiner.run_refiner() method where it shadows the outer ctx.search_diagnostics field with a local variable of the same name, preventing the pipeline from accessing accurate search diagnostics after refinement.

## Background
In augment.py (AugmentRefiner.run_refiner()), the code creates a new SearchDiagnostics instance:
```python
ctx.search_diagnostics = SearchDiagnostics(
    embed_ok=...,
    embed_failed=...,
    fts_errors=...,
)
```

This overwrites the original SearchDiagnostics computed during search execution. The original diagnostics contained information about which embeddings failed and how many FTS errors occurred — information lost when overwritten.

## Problem
1. Original search diagnostics are replaced with refiner's own diagnostics
2. The refiner's diagnostics may have different values (e.g., different embed_failed count)
3. Pipeline-level diagnostics aggregation becomes inaccurate
4. Operators cannot distinguish between search failures and refiner failures

## Reason for Change
Preserve the original search diagnostics and add refiner-specific diagnostics as a separate field. This allows operators to trace failures back to their source.

## Implementation Intent
1. Rename the refiner's SearchDiagnostics to `_refiner_diagnostics` or similar
2. Keep the original ctx.search_diagnostics unchanged
3. If the refiner needs to report its own diagnostics, use a separate field

## Target Files or Areas
- scripts/rag/augment.py

## Required Changes
- In AugmentRefiner.run_refiner(): rename the SearchDiagnostics assignment to avoid shadowing
- Consider adding a `_refiner_diagnostics` field to PipelineContext or using a separate return value

## Constraints
- Must not change the PipelineContext dataclass structure (or update it consistently across all callers)
- Must preserve existing diagnostic reporting for search operations
- Must not break existing tests

## Acceptance Criteria
- Original search diagnostics preserved after refiner runs
- Refiner can still report its own diagnostics via a separate mechanism
- All existing tests pass after changes

## Testing Expectations
- Add test verifying ctx.search_diagnostics is not modified by refiner
- Verify refiner diagnostics accessible via separate mechanism
- Run: pytest tests/rag/test_rag_pipeline.py

## Documentation Impact
Update PipelineContext docstring to document the relationship between search and refiner diagnostics.

## Out of Scope
- Adding a full diagnostics hierarchy to PipelineContext
- Changes to SearchDiagnostics dataclass structure
- Changes to how PipelineDiagnostics aggregates diagnostics

## Dependencies
N/A: none

## Unresolved Questions
Should we add a `_refiner_diagnostics` field to PipelineContext? This would require updating the dataclass definition and all stage implementations.

## AI Implementation Instruction
1. Read scripts/rag/augment.py
2. Find the SearchDiagnostics assignment in run_refiner() (around line 140-150)
3. Rename the variable from `ctx.search_diagnostics` to something like `refiner_diag` or `_refiner_diagnostics`
4. Do NOT modify PipelineContext dataclass unless explicitly requested
5. Run pytest tests/rag/test_rag_pipeline.py to verify

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260913-163623
- **Related target files**: scripts/rag/augment.py
