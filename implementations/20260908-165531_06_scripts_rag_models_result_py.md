# Implementation Procedure: Add PipelineDiagnostics Import to models_result.py

## Goal

Add `PipelineDiagnostics` import to `scripts/rag/models_result.py` alongside existing result dataclasses (`PipelineExecutionResult`, `SearchDiagnostics`, etc.), enabling typed diagnostics usage throughout the rag package.

## Scope

- Add `from rag.diagnostics import PipelineDiagnostics` to `models_result.py`
- No other modifications to `models_result.py`

## Assumptions

- `PipelineDiagnostics` is already defined in `scripts/rag/diagnostics.py` (created by Phase 3).
- `models_result.py` has 107 lines with 10 existing result dataclasses; adding one import does not change its structure.
- No circular import risk between `diagnostics.py` and `models_result.py` (confirmed by reading both files).

## Design decisions

1. **Import alongside existing result imports** — follows the pattern used by other result dataclasses in `models_result.py`.
2. **No re-export or aliasing** — consumers import `PipelineDiagnostics` from `diagnostics.py` directly when they need it.

## Alternatives considered

- Exporting `PipelineDiagnostics` from `models_result.py` as well: rejected because it would create an indirect dependency and obscure the true origin of the class.
- Moving `PipelineDiagnostics` into `models_result.py`: rejected because it mixes diagnostic types with result types (separation of concerns).

## Implementation

### Target file

`scripts/rag/models_result.py`

### Procedure

1. Open `scripts/rag/models_result.py` (107 lines, 10 existing result dataclasses).
2. Locate the existing import section for result dataclasses.
3. Add `from rag.diagnostics import PipelineDiagnostics` alongside other result imports.
4. Verify no circular import by running `python -c "import rag.models_result"`.

### Method

Simple import addition — mechanical edit, no behavioral change.

### Details

- File location: `scripts/rag/models_result.py`
- Existing dataclasses: `PipelineExecutionResult`, `SearchDiagnostics`, etc.
- Import line added near other result dataclass imports (not mixed with unrelated imports)

## Compatibility considerations

- No API change; `PipelineDiagnostics` was previously only accessible via `get_diagnostics()` return value.
- Consumers who were importing from `pipeline.py` now import from `models_result.py` or `diagnostics.py`.

## Security considerations

- Import addition has no security impact.

## Rollback considerations

- Revert: remove the single import line.
- Trivial rollback.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/models_result.py` | Import verification | `python -c "import rag.models_result"` | No circular import error |

## Completion criteria

- `from rag.diagnostics import PipelineDiagnostics` present in `models_result.py`.
- No circular import error when importing `models_result`.
- No other changes to `models_result.py`.

## Out of scope

- Modifying any existing dataclass in `models_result.py`.
- Adding new dataclasses beyond `PipelineDiagnostics`.
- Changing import order or style.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `PipelineDiagnostics` import to `models_result.py` | Pending | — | — | |
| 2 | Verify no circular import | Pending | — | — | |

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
- **Requirement ID**: REQ-002 — add `PipelineDiagnostics` import to `models_result.py`
- **Source issue**: issues/20260908-105318_refactor_rag_pipeline_complexity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-165531_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260908-165531
- **Related target files**: scripts/rag/models_result.py
