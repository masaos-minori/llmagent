# Add thread-safety analysis for PipelineContext mutable state under concurrent execution

## Priority
Medium

## Summary
Audit and fix potential race conditions in PipelineContext mutable state when stages execute concurrently. PipelineContext is a dataclass with mutable list fields (queries, search_results, merged, reranked, stage_results) that could be modified by multiple coroutines simultaneously during async pipeline execution.

## Background
PipelineContext (stage.py:35-51) is passed between pipeline stages and modified in-place by each stage's run() method. While the current pipeline executes stages sequentially within a single coroutine, there are scenarios where concurrent access could occur:
1. Multiple queries processed via asyncio.gather in _search_all_queries()
2. Future concurrent pipeline invocations sharing the same context
3. Stage result recording in lifecycle._run_stage() while another coroutine reads diagnostics

## Problem
The following mutable fields are modified without synchronization:
- ctx.queries: written by MqeStage.run(), read by SearchStage.run()
- ctx.search_results: written by SearchStage.run(), read by FusionStage.run()
- ctx.merged: written by FusionStage.run(), read by RerankStage.run()
- ctx.reranked: written by RerankStage.run(), read by AugmentStage.run()
- ctx.stage_results: appended by lifecycle._run_stage(), read by callers

While sequential execution avoids races, the Protocol contract (`async def run(self, ctx: PipelineContext, **kwargs: Any) -> None`) does not guarantee exclusive access to ctx. A future caller could invoke stages concurrently.

## Reason for Change
Document the concurrency assumptions clearly and add defensive measures to prevent silent data corruption if concurrent access occurs. This includes either:
1. Adding explicit synchronization primitives (locks) around mutable field access
2. Documenting the single-threaded assumption and adding assertions
3. Restructuring to avoid shared mutable state (e.g., return values instead of in-place mutation)

## Implementation Intent
Option A (minimal): Add docstring to PipelineContext documenting the single-threaded assumption and add @assertions for concurrent access detection.
Option B (robust): Replace in-place mutation with return-value pattern — each stage returns its output, and the lifecycle orchestrator assigns results to ctx.
Option C (hybrid): Keep in-place mutation but add asyncio.Lock around critical sections.

Recommend Option A as immediate fix, Option B as long-term improvement.

## Target Files or Areas
- scripts/rag/stage.py
- scripts/rag/stage_lifecycle.py
- scripts/rag/stages/*.py

## Required Changes
- Add concurrency documentation to PipelineContext docstring
- Consider adding asyncio.Lock to critical path operations
- Evaluate whether in-place mutation pattern needs replacement

## Constraints
- Must preserve existing API contracts (stages modify ctx in-place)
- Must not introduce performance regressions from locking
- Must not change the Protocol interface

## Acceptance Criteria
- Concurrency assumptions documented in PipelineContext
- No silent data corruption under concurrent access
- Existing tests pass
- Performance impact of any added synchronization measured

## Testing Expectations
- Add test simulating concurrent stage execution on same PipelineContext
- Verify no data corruption under concurrent writes
- Run: pytest tests/rag/test_rag_pipeline_stage.py

## Documentation Impact
Update PipelineContext docstring to document concurrency guarantees and limitations.

## Out of Scope
- Complete rewrite of the pipeline to use immutable state (would require extensive changes)
- Adding distributed caching or cross-process synchronization
- Changes to the PipelineStage Protocol interface

## Dependencies
N/A: none

## Unresolved Questions
Is the current sequential execution model sufficient for production use cases? If concurrent pipeline execution is expected, what are the performance requirements?

## AI Implementation Instruction
1. Read scripts/rag/stage.py — add concurrency documentation to PipelineContext docstring
2. Read scripts/rag/stage_lifecycle.py — evaluate if asyncio.Lock should wrap ctx modifications
3. For Option A (document-only): add clear docstring noting "This context is modified in-place by stages; concurrent access is not supported"
4. For Option B (return-value): refactor each stage's run() to return output instead of modifying ctx
5. Run pytest tests/rag/test_rag_pipeline_stage.py to verify
6. Start with Option A unless user requests Option B/C

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260913-163623
- **Related target files**: scripts/rag/stage.py, scripts/rag/stage_lifecycle.py
