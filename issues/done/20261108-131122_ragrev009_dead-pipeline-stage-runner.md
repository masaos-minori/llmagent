# RagPipeline keeps an unused duplicate stage runner that has its own tests

## Priority
Medium

## Summary
`RagPipeline._run_stage` and `_get_stage_status` duplicate the logic of `RagPipelineStageLifecycle` but are no longer called by `RagPipeline.run()`; a test still exercises the dead copy.

## Background
Review finding F-011. Evidence (Explicit in code): `RagPipeline.run()` delegates to `RagPipelineStageLifecycle.run()`; a repository-wide search finds `_run_stage` / `_get_stage_status` of `scripts/rag/pipeline.py` referenced only by `tests/rag/test_rag_pipeline_stage.py` (`test_run_stage_records_failure_on_rerank_error`). The two copies already differ in how they would be maintained, and the production stage runner is covered by `tests/rag/test_stage_lifecycle.py` instead.

## Problem
A reader or a future change can fix the wrong copy; the test gives the impression that failure absorption of the pipeline is verified through a path that production never takes.

## Reason for Change
Dead duplicates with live tests are a maintainability and test-fidelity risk, and the discrepancy already hid a missing check (ragrev003).

## Implementation Intent
Remove the dead methods and move the one behavior the test protects (failure recorded as a stage result, not re-raised) to the lifecycle tests if it is not already covered.

## Target Files or Areas
- `scripts/rag/pipeline.py` (`RagPipeline._run_stage`, `_get_stage_status`)
- `tests/rag/test_rag_pipeline_stage.py`
- `tests/rag/test_stage_lifecycle.py`

## Required Changes
- Confirm with a search that nothing else calls the two methods.
- Delete them and unused imports.
- Retarget the test to `RagPipelineStageLifecycle._run_stage` or confirm equivalent coverage exists.

## Constraints
- No behavior change.
- Keep the `PipelineStage` protocol untouched.

## Acceptance Criteria
- No reference to the removed methods remains.
- The failure-absorption behavior is asserted against the lifecycle implementation.
- `uv run pytest tests/rag -q` passes.

## Testing Expectations
- `uv run pytest tests/rag -q`, `uv run ruff check`, `uv run mypy`, `PYTHONPATH=scripts uv run lint-imports`.
- `uv run python tools/check_mock_patch_targets.py` after the test change.

## Documentation Impact
No documentation change expected.

## Out of Scope
- Refactoring the lifecycle class.

## Dependencies
Related, no required order: `issues/20261108-131006_ragrev003_fallback-diagnostics-overwritten.md` (same files).

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Keep the change minimal and confined to the Target Files or Areas. Do not rewrite unrelated files, keep public behavior unchanged unless Required Changes says otherwise, and do not implement items listed under Out of Scope. Add the tests named in Testing Expectations before or with the fix. If a requirement is unclear, stop and report the open question instead of guessing.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261108-131122
- **Related target files**: `scripts/rag/pipeline.py`, `tests/rag/test_rag_pipeline_stage.py`, `tests/rag/test_stage_lifecycle.py`
