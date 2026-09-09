# Implementation Procedure: Refactor RAG Pipeline Diagnostics

## Goal

Create `PipelineDiagnostics` dataclass mirroring `get_diagnostics()`'s current dict keys exactly, reducing `pipeline.py` complexity and providing typed diagnostics access.

## Scope

- Create `scripts/rag/diagnostics.py` with `PipelineDiagnostics` dataclass
- Add `PipelineDiagnostics` import to `scripts/rag/models_result.py`
- Replace `get_diagnostics()`'s dict construction with `PipelineDiagnostics.from_run_result(...)` converted back to a `dict`
- Create unit tests for `PipelineDiagnostics`

## Assumptions

- `get_diagnostics()`'s current dict shape must remain byte-for-byte identical (per REQ-002 backward-compatibility constraint)
- `PipelineDiagnostics` excludes cumulative counters (Design decision #2): only `embed_ok`/`embed_failed`/`fts_errors`/`degraded` fields under `search_diagnostics` key
- `get_diagnostics()`'s return type stays `dict` (Design decision #3); `PipelineDiagnostics.to_dict()` converts internally

## Design decisions

1. **`PipelineDiagnostics` mirrors current dict keys exactly** — per Design decision #2, cumulative counters are excluded.
2. **`PipelineDiagnostics.from_run_result()` builds the object**; `get_diagnostics()` converts via `to_dict()` before returning.
3. **`PipelineDiagnostics` is a dataclass** — enables type-safe field access while preserving dict output.

## Alternatives considered

- Keeping `get_diagnostics()` as pure dict construction: rejected because it defeats the purpose of typed diagnostics.
- Returning `PipelineDiagnostics` directly from `get_diagnostics()`: rejected because it changes the public API (backward-compatibility constraint).

## Implementation

### Target file

`scripts/rag/diagnostics.py`

### Procedure

1. Create `scripts/rag/diagnostics.py` with a module docstring referencing `pipeline.py` as the source of `get_diagnostics()`.
2. Define `PipelineDiagnostics` dataclass with fields matching the current dict keys: `search_diagnostics` (containing `embed_ok`, `embed_failed`, `fts_errors`, `degraded`).
3. Implement `PipelineDiagnostics.from_run_result(run_result)` classmethod that extracts search diagnostics from the run result.
4. Implement `PipelineDiagnostics.to_dict()` method that produces the exact same dict shape as the current `get_diagnostics()`.
5. Create `tests/rag/test_diagnostics.py` covering `from_run_result()` and `to_dict()`.

### Method

Dataclass creation + factory method pattern. The classmethod extracts relevant fields from the run result; `to_dict()` serializes back to the original dict shape.

### Details

- Current dict keys confirmed at `scripts/rag/pipeline.py:521`: `search_diagnostics` sub-dict with `embed_ok`, `embed_failed`, `fts_errors`, `degraded`
- Cumulative counters (`stat_search_embed_failed`, `stat_search_fts_errors`) are NOT included (confirmed by reading current implementation)
- `PipelineDiagnostics` must match this exactly to preserve `get_diagnostics()`'s current dict shape

## Compatibility considerations

- `get_diagnostics()` return value must be byte-for-byte identical to current output.
- `PipelineDiagnostics` is internal; no external consumers of the class itself.

## Security considerations

- Diagnostics data contains operational metrics but no secrets or PII.

## Rollback considerations

- Revert: remove `diagnostics.py`, revert `models_result.py` import, restore `get_diagnostics()` dict construction in `pipeline.py`.
- Low risk: the classmethod and `to_dict()` can be removed cleanly.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/diagnostics.py` | Unit | `uv run pytest tests/rag/test_diagnostics.py -v` | `PipelineDiagnostics.from_run_result()` produces correct field values |

## Completion criteria

- `PipelineDiagnostics` dataclass exists in `scripts/rag/diagnostics.py`.
- `PipelineDiagnostics.from_run_result()` produces correct field values.
- `PipelineDiagnostics.to_dict()` produces identical dict to current `get_diagnostics()`.
- `tests/rag/test_diagnostics.py` passes with ≥80% branch coverage.
- No regression in existing diagnostic assertion tests.

## Out of scope

- Adding new diagnostic fields beyond current dict keys.
- Changing `get_diagnostics()` return type from `dict`.
- Adding diagnostic persistence or export capabilities.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create `scripts/rag/diagnostics.py` with `PipelineDiagnostics` | Completed | — | — | File exists; dataclass defined |
| 2 | Add import to `scripts/rag/models_result.py` | Completed | — | — | Import site updated in prior cycle |
| 3 | Replace `get_diagnostics()` dict construction | Completed | — | — | Updated in prior cycle |
| 4 | Create `tests/rag/test_diagnostics.py` | Completed | — | — | Test file exists |
| 5 | Run validation sequence | Completed | — | — | Validation passed in prior cycle |

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
- **Requirement ID**: REQ-002 — create `PipelineDiagnostics` dataclass, preserve `get_diagnostics()` dict shape
- **Source issue**: issues/20260908-105318_refactor_rag_pipeline_complexity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-165531_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260908-165531
- **Related target files**: scripts/rag/diagnostics.py
