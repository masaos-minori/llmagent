# Implementation Procedure: Refactor RAG Pipeline Config Resolution

## Goal

Extract `resolve_rag_config()` function from `pipeline.py` into a dedicated module, preserving its exact public signature and behavior. This reduces `pipeline.py` complexity and isolates config resolution logic.

## Scope

- Extract `resolve_rag_config()` verbatim into `scripts/rag/config_resolution.py`
- Update `pipeline.py` to import from the new module
- Create unit tests covering priority ordering, defaults, and validation error propagation

## Assumptions

- `resolve_rag_config()`'s current implementation is correct; extraction is mechanical (no behavioral changes)
- The function depends only on `RagConfigImpl`, `RagConfig`, and standard library modules (confirmed by reading `pipeline.py:63`)
- No other file imports `resolve_rag_config` directly from `pipeline.py` (confirmed by grep)

## Design decisions

1. **Keep `resolve_rag_config()`'s exact signature unchanged** — per REQ-001 backward-compatibility constraint on `RagPipeline`'s public method signatures.
2. **Module docstring references `pipeline.py` as origin** — clarifies provenance for future maintainers.

## Alternatives considered

- Inlining config resolution inside `RagPipeline.__init__`: rejected because it would increase coupling between pipeline construction and config logic.
- Making `resolve_rag_config` a classmethod on `RagPipeline`: rejected because config resolution has no pipeline state dependency.

## Implementation

### Target file

`scripts/rag/config_resolution.py`

### Procedure

1. Create `scripts/rag/config_resolution.py` with a module docstring referencing `pipeline.py` as the source of `resolve_rag_config()`.
2. Copy the entire `resolve_rag_config()` function body from `pipeline.py:63` verbatim.
3. Ensure the function accepts the same parameters and returns the same type (`RagConfigImpl`).
4. Update `pipeline.py` to remove the local `resolve_rag_config()` definition and replace it with `from rag.config_resolution import resolve_rag_config`.

### Method

Mechanical extraction: copy function body, verify parameter list and return type match, update import site.

### Details

- Function location in source: `scripts/rag/pipeline.py:63`
- Return type: `RagConfigImpl` (already resolved concrete type, not `RagConfig`)
- Dependencies: `RagConfigImpl`, `RagConfig` dataclasses from `models.py`
- The function resolves config priority: CLI args → env vars → YAML config → defaults
- Validation errors propagate unchanged (raised as exceptions)

## Compatibility considerations

- `RagPipeline.__init__` calls `resolve_rag_config()` — after extraction, it imports from the new module. The call site is identical; no API change.
- No other production code imports `resolve_rag_config` from `pipeline.py` (confirmed by grep).

## Security considerations

- Config resolution may read sensitive values from environment variables or YAML config files. Extraction does not change security posture; the function still reads the same sources.

## Rollback considerations

- Revert: restore `resolve_rag_config()` in `pipeline.py`, delete `config_resolution.py`, revert import in `pipeline.py`.
- Low risk: the function body is copied verbatim; rollback is a simple revert.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/config_resolution.py` | Unit | `uv run pytest tests/rag/test_config_resolution.py -v` | Priority ordering, defaults, and validation-error propagation all pass |

## Completion criteria

- `resolve_rag_config()` exists in `scripts/rag/config_resolution.py` with identical behavior to the original.
- `pipeline.py` imports from `config_resolution` instead of defining locally.
- `tests/rag/test_config_resolution.py` passes with ≥80% branch coverage.
- No regression in existing `RagPipeline` integration tests.

## Out of scope

- Modifying `resolve_rag_config()` logic or adding new config sources.
- Changing the config priority order.
- Adding config hot-reload capability.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create `scripts/rag/config_resolution.py` with extracted `resolve_rag_config()` | Completed | — | — | File exists; function body verbatim copy confirmed |
| 2 | Update `pipeline.py` to import from `config_resolution` | Completed | — | — | Import site updated in prior cycle |
| 3 | Create `tests/rag/test_config_resolution.py` | Completed | — | — | Test file exists |
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
- **Requirement ID**: REQ-001 — extract `resolve_rag_config()` into dedicated module
- **Source issue**: issues/20260908-105318_refactor_rag_pipeline_complexity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-165531_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260908-165531
- **Related target files**: scripts/rag/config_resolution.py
