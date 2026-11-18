## Goal

Replace the bare `int()` / `float()` coercions in `RagPipelineConfig.from_dict` with `get_typed(...)`-style validation (REQ-003), and replace the bare `int()` / `float()` re-coercions in `build_rag_cfg_adapter` with pass-through of the already-validated `RagPipelineConfig` fields (REQ-004).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Scope follows the frozen Acceptance Criteria: only `int()` / `float()` / `list()` are replaced. The `bool(...)` coercions (`use_mqe`, `use_rrf`, `use_rerank`, `use_refiner`) and `str(...)`/`get_str` string fields are retained (scope boundary, per the Plan's Assumptions/UNK-01).
- `build_rag_cfg_adapter` receives an already-typed `RagPipelineConfig`, so there is no dict/key to operate on; passing the validated value through removes the bare coercion while preserving the `RagConfig` Protocol contract (consumer at `rag_pipeline_service.py` line 108).

## Design decisions
- Scalar int/float: replace `int(d.get("k", D))` / `float(d.get("k", D))` with `get_typed(d, "k", int|float, "<a noun>", default=D)`.
- `build_rag_cfg_adapter`: assign the field directly (e.g. `rrf_k=cfg.rrf_k`) instead of `int(cfg.rrf_k)`.

## Alternatives considered
- Replacing `bool(...)` too: rejected as out of scope for the frozen acceptance gate (UNK-01); recommended as a follow-up.

## Implementation
### Target file
`scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`

### Procedure
1. In `RagPipelineConfig.from_dict` (lines 75-92), replace every bare `int()` / `float()` field with `get_typed(..., int|float, ..., default=<dataclass default>)`; leave `str(...)`/`get_str` and `bool(...)` untouched (REQ-003).
2. In `build_rag_cfg_adapter` (lines 164-175), replace the bare `int()` / `float()` re-coercions with direct pass-through of the validated `RagPipelineConfig` fields (REQ-004).
3. Import `get_typed` alongside the existing `get_str`.

### Method
- Edit the field expressions in `from_dict` and `build_rag_cfg_adapter`. Copy each `default=` verbatim from the dataclass field definition. Do not touch field definitions or the `compute_config_fingerprint()` method.

### Details
- `rag_min_score` is a float field with default `2.0`; confirm the `default=2.0` is preserved. The `test_falsy_present_values_are_not_treated_as_missing` case passes `rag_min_score: 0` (int for a float field), which `get_typed` rejects — this test must be reconciled (companion).

### Companion test files
- `tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py`
  - Procedure: update `test_numeric_string_values_are_coerced` to assert `ValueError` instead of coercion; reconcile `test_falsy_present_values_are_not_treated_as_missing`'s `rag_min_score: 0` int-for-float case; add a wrong-typed-value + missing-key-default test (T-003, T-004; REQ-005)
  - Validation: `uv run pytest tests/mcp_servers/rag_pipeline` green; no regression in `test_rag_pipeline_mcp_service.py`

## Compatibility considerations
- Valid-config behavior unchanged for correct types and missing keys; wrong-typed values now raise `ValueError` at load.

## Security considerations
- Fail-fast config boundary; do not weaken.

## Rollback considerations
- Revert the commit; confined to `RagPipelineConfig.from_dict` and `build_rag_cfg_adapter`.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py` + `tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py` | Unit | `uv run pytest tests/mcp_servers/rag_pipeline` | green; `test_numeric_string_values_are_coerced` asserts `ValueError`; `test_falsy_present_values...` reconciled; no regression in `test_rag_pipeline_mcp_service.py` |
| Changed files | Lint / type | `uv run ruff check` + `uv run mypy` on `rag_pipeline_models.py` | clean |

## Completion criteria
- No bare `int()` / `float()` remains in `RagPipelineConfig.from_dict` or `build_rag_cfg_adapter`; wrong types raise `ValueError`; missing keys return defaults; output still satisfies every `RagConfig` Protocol field (AC-003, AC-004).

## Out of Scope

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261118-082539 | 20261118-082539 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261118-082539 | 20261118-082539 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261118-082539 | 20261118-082539 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261118-082539 | 20261118-082539 | N/A: no docs/00_index.md task-scope mapping for changed config-loader files |

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
- **Requirement ID**: `REQ-003` (route `RagPipelineConfig.from_dict` int/float fields through `get_typed`), `REQ-004` (pass validated `RagPipelineConfig` fields through `build_rag_cfg_adapter` without bare coercion)
- **Source issue**: issues/20261118-025551_mcpget001_mcp-models-type-coercion.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-041831_mcpget001_mcp-models-type-coercion.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-070059
- **Related target files**: `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`, `tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py`