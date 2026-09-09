# Implementation Procedure: Refactor RAG Pipeline Stage Lifecycle

## Goal

Extract stage lifecycle management from `RagPipeline.run()` into a dedicated `RagPipelineStageLifecycle` class, reducing `pipeline.py` complexity and isolating stage execution logic.

## Scope

- Create `scripts/rag/stage_lifecycle.py` with `RagPipelineStageLifecycle` class
- Update `run()` to delegate to `RagPipelineStageLifecycle`
- Create unit tests for stage execution order, timing recording, fallback detection

## Assumptions

- `RagPipelineStageLifecycle` accepts `RagConfigImpl`, not `RagConfig` (Design decision #4): `self._cfg` is assigned from `resolve_rag_config()`'s return value, which is already `RagConfigImpl`.
- Stage creation-and-execution loop (`_run_stage`/`_get_stage_status`) extracted verbatim.
- All public method signatures on `RagPipeline` remain unchanged.

## Design decisions

1. **Accept `RagConfigImpl` instead of `RagConfig`** — avoids unnecessary cast since `resolve_rag_config()` returns concrete type.
2. **`RagPipelineStageLifecycle` encapsulates the entire stage execution loop** — including stage creation, execution, status tracking, and fallback detection.

## Alternatives considered

- Making `RagPipelineStageLifecycle` accept `RagConfig` and casting internally: rejected because `resolve_rag_config()` already returns `RagConfigImpl`.
- Keeping stage lifecycle inline in `run()`: rejected because it defeats the purpose of extracting ~100+ lines of stage logic.

## Implementation

### Target file

`scripts/rag/stage_lifecycle.py`

### Procedure

1. Create `scripts/rag/stage_lifecycle.py` with a module docstring referencing `pipeline.py` as the source of the stage lifecycle logic.
2. Define `RagPipelineStageLifecycle` class with:
   - `__init__(self, cfg: RagConfigImpl)` accepting resolved config
   - `run(self, ...)` method replicating the stage-creation-and-execution loop
   - `_run_stage(self, ...)` helper for individual stage execution
   - `_get_stage_status(self, ...)` helper for status reporting
3. Ensure the class preserves all timing recording and fallback detection behavior.
4. Update `pipeline.py`'s `run()` to instantiate and delegate to `RagPipelineStageLifecycle`.
5. Create `tests/rag/test_stage_lifecycle.py` covering stage execution order, timing, and fallback detection.

### Method

Class extraction: copy the stage lifecycle methods from `RagPipeline.run()`, verify parameter list matches, update call site in `run()`.

### Details

- Stage lifecycle location in source: `scripts/rag/pipeline.py:361` (stage-execution loop), lines 254-296 (`_run_stage`/`_get_stage_status` helpers)
- Accepts `RagConfigImpl` (not `RagConfig`) — per Design decision #4
- Preserves: stage execution order, timing recording, fallback detection, status reporting

## Compatibility considerations

- `RagPipeline.run()` delegates to `RagPipelineStageLifecycle`; external callers see no change.
- All public method signatures on `RagPipeline` remain unchanged.

## Security considerations

- Stage lifecycle does not handle sensitive operations; no security impact.

## Rollback considerations

- Revert: remove `stage_lifecycle.py`, restore stage lifecycle code in `RagPipeline.run()`, revert `run()` call site.
- Low risk: the class can be removed cleanly; rollback restores original structure.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/stage_lifecycle.py` | Unit | `uv run pytest tests/rag/test_stage_lifecycle.py -v` | Stage execution order, timing recording, fallback detection all correct |

## Completion criteria

- `RagPipelineStageLifecycle` class exists in `scripts/rag/stage_lifecycle.py`.
- `RagPipelineStageLifecycle` accepts `RagConfigImpl` and executes stages correctly.
- Timing recording and fallback detection preserved.
- `tests/rag/test_stage_lifecycle.py` passes with ≥80% branch coverage.
- No regression in existing pipeline integration tests.

## Out of scope

- Modifying stage execution order or adding new stages.
- Changing how fallback detection works.
- Adding stage-level parallelism.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create `scripts/rag/stage_lifecycle.py` with `RagPipelineStageLifecycle` | Completed | — | — | File exists; class defined |
| 2 | Update `run()` to delegate to `RagPipelineStageLifecycle` | Completed | — | — | Updated in prior cycle |
| 3 | Create `tests/rag/test_stage_lifecycle.py` | Completed | — | — | Test file exists |
| 4 | Run validation sequence | Completed | — | — | Validation passed in prior cycle |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003 — extract stage lifecycle into dedicated class
- **Source issue**: issues/20260908-105318_refactor_rag_pipeline_complexity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-165531_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260908-165531
- **Related target files**: scripts/rag/stage_lifecycle.py
