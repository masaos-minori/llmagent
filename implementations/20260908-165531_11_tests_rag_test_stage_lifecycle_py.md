# Implementation Procedure: Create Unit Tests for Stage Lifecycle

## Goal

Create unit tests for `RagPipelineStageLifecycle` covering stage execution order, timing recording, and fallback detection, ensuring the extracted class behaves identically to the original `run()` method.

## Scope

- Create `tests/rag/test_stage_lifecycle.py` with comprehensive unit tests
- Cover: stage execution order (MQE → search → RRF → rerank)
- Cover: timing recording accuracy
- Cover: fallback detection correctness

## Assumptions

- `RagPipelineStageLifecycle` exists in `scripts/rag/stage_lifecycle.py` (created by Phase 5).
- The class accepts `RagConfigImpl` and executes stages in the same order as the original `run()`.
- Stage lifecycle location in source: `scripts/rag/pipeline.py:361` (stage-execution loop), lines 254-296 (`_run_stage`/`_get_stage_status` helpers).

## Design decisions

1. **Test the class directly**, not through `RagPipeline.run()` — isolates stage lifecycle logic.
2. **Mock individual stages** where appropriate to avoid full pipeline execution.
3. **Verify timing recording** using `time.monotonic()` assertions.

## Alternatives considered

- Testing through `RagPipeline.run()`: rejected because it couples stage lifecycle tests to pipeline construction.
- Property-based testing: rejected because the stage lifecycle logic has clear discrete cases (execution order, timing, fallback).

## Implementation

### Target file

`tests/rag/test_stage_lifecycle.py`

### Procedure

1. Create `tests/rag/test_stage_lifecycle.py` with module docstring referencing `stage_lifecycle.py` as the source.
2. Write test class(es) covering:
   - **Stage execution order**: MQE → search → RRF → rerank
   - **Timing recording**: accurate start/end times for each stage
   - **Fallback detection**: correct identification when a stage fails
   - **Edge cases**: empty stage list, single-stage execution, all-fail scenario
3. Ensure ≥80% branch coverage for `stage_lifecycle.py`.

### Method

Standard unit test creation: define test functions/classes, use `pytest` fixtures for setup, mock individual stages where needed, assert expected behavior.

### Details

- Stage order: MQE → search → RRF → rerank (per Issue's "Do not change the RAG pipeline algorithm order")
- Timing recorded via `time.monotonic()` for each stage
- Fallback detected when a stage raises an exception or returns failure status

## Compatibility considerations

- Tests must validate that `RagPipelineStageLifecycle` behaves identically to the original `run()` method.

## Security considerations

- Test file changes have no security impact.

## Rollback considerations

- Revert: delete `test_stage_lifecycle.py`.
- Trivial rollback.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/stage_lifecycle.py` | Unit | `uv run pytest tests/rag/test_stage_lifecycle.py -v` | Stage execution order, timing recording, fallback detection all correct |

## Completion criteria

- `tests/rag/test_stage_lifecycle.py` passes with ≥80% branch coverage.
- Stage execution order verified: MQE → search → RRF → rerank.
- Timing recording verified: accurate start/end times.
- Fallback detection verified: correct identification on failure.

## Out of scope

- Integration tests for `RagPipeline.run()` (covered separately via regression tests).
- Performance benchmarks.
- Testing stage-level parallelism (out of scope for this Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create `tests/rag/test_stage_lifecycle.py` | Pending | — | — | |
| 2 | Run validation sequence | Pending | — | — | |

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
- **Requirement ID**: REQ-003, REQ-008 — unit tests for `RagPipelineStageLifecycle`, ≥80% branch coverage
- **Source issue**: issues/20260908-105318_refactor_rag_pipeline_complexity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-165531_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260908-165531
- **Related target files**: tests/rag/test_stage_lifecycle.py
