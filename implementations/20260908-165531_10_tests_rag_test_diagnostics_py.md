# Implementation Procedure: Create Unit Tests for PipelineDiagnostics

## Goal

Create unit tests for `PipelineDiagnostics.from_run_result()` verifying correct field values, and `to_dict()` verifying identical dict shape to current `get_diagnostics()`.

## Scope

- Create `tests/rag/test_diagnostics.py` with comprehensive unit tests
- Cover: `from_run_result()` produces correct field values
- Cover: `to_dict()` produces byte-for-byte identical dict to current `get_diagnostics()`

## Assumptions

- `PipelineDiagnostics` exists in `scripts/rag/diagnostics.py` (created by Phase 3).
- Current dict keys confirmed at `scripts/rag/pipeline.py:521`: `search_diagnostics` sub-dict with `embed_ok`, `embed_failed`, `fts_errors`, `degraded`.
- Cumulative counters (`stat_search_embed_failed`, `stat_search_fts_errors`) are NOT included.

## Design decisions

1. **Test `from_run_result()` directly** — isolate diagnostics construction logic.
2. **Compare `to_dict()` output byte-for-byte** — ensure backward compatibility with existing diagnostic assertion tests.
3. **Use `pytest` fixtures** for common test setup (e.g., mock run results).

## Alternatives considered

- Testing through `get_diagnostics()`: rejected because it couples diagnostics tests to pipeline execution.
- Property-based testing: rejected because the diagnostics logic has clear discrete cases (field values, dict shape).

## Implementation

### Target file

`tests/rag/test_diagnostics.py`

### Procedure

1. Create `tests/rag/test_diagnostics.py` with module docstring referencing `diagnostics.py` as the source.
2. Write test class(es) covering:
   - **`from_run_result()`**: verify correct field values for each diagnostic metric
   - **`to_dict()`**: verify byte-for-byte identical dict to current `get_diagnostics()` output
   - **Edge cases**: empty run result, partial diagnostics, all-zero metrics
3. Ensure ≥80% branch coverage for `diagnostics.py`.

### Method

Standard unit test creation: define test functions/classes, use `pytest` fixtures for setup, assert expected behavior.

### Details

- Current dict keys: `search_diagnostics` sub-dict with `embed_ok`, `embed_failed`, `fts_errors`, `degraded`
- Cumulative counters excluded per Design decision #2
- `to_dict()` must produce identical key set and values

## Compatibility considerations

- Tests must validate that `PipelineDiagnostics.to_dict()` produces identical output to current `get_diagnostics()`.

## Security considerations

- Test file changes have no security impact.

## Rollback considerations

- Revert: delete `test_diagnostics.py`.
- Trivial rollback.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/diagnostics.py` | Unit | `uv run pytest tests/rag/test_diagnostics.py -v` | `PipelineDiagnostics.from_run_result()` produces correct field values |

## Completion criteria

- `tests/rag/test_diagnostics.py` passes with ≥80% branch coverage.
- `from_run_result()` produces correct field values.
- `to_dict()` produces byte-for-byte identical dict to current `get_diagnostics()`.

## Out of scope

- Integration tests for `RagPipeline.get_diagnostics()` (covered separately via regression tests).
- Performance benchmarks.
- Testing diagnostic persistence (out of scope for this Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create `tests/rag/test_diagnostics.py` | Pending | — | — | |
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
- **Requirement ID**: REQ-002, REQ-008 — unit tests for `PipelineDiagnostics`, ≥80% branch coverage
- **Source issue**: issues/20260908-105318_refactor_rag_pipeline_complexity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-165531_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260908-165531
- **Related target files**: tests/rag/test_diagnostics.py
