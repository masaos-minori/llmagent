## Goal
- Reduce `AugmentRefiner` to the refiner concern (REQ-001, REQ-002): remove HTTP augment, HTTP state, and the remote identity.

## Scope
**Release unit**: http-path-and-gate

- In scope: this one file, Phase 1 of the Plan.
- Not in scope: any other file; a second file needed here is an additional-target discovery.
- Execution order follows the Plan's phases, not `seq`: Phases 1 and 2 are one release unit (HTTP path and identity gate: documents 01-08, 11, 15, 21, 25, 27, 59 with their companions); Phase 3 (configuration keys: documents 09, 10, 12, 13, 14, 16, 17, 61 and the fixture tests 26, 30-33, 35, 37, 38, 40); Phase 4 (ADRs and documents: 18, 19, 41-58, 60).

## Assumptions
- Overlap with plan 004 (`config/agent.toml`, `scripts/agent/production_config_validator.py`, `tests/agent/test_production_config_validator.py`, ADR-004) and plan 006 (`adr_01_index.md`): different keys or sections (judged in the Plan); no contradiction on this file.
- The Plan's Step 3a corrections apply (removed-key rejection is implemented once in `RagConfigValidator`; the gate block of `RagPipeline.augment()` keeps recording `_last_corpus_generation`; `rag_pipeline_service_url` belongs to the ingester and stays).

## Design decisions
- Remove only what the delegation path alone uses; keep `compute_local_identity`, `CorpusIdentity`, `ensure_corpus_meta`, `compute_identity`, and the refiner.

## Alternatives considered
N/A: RAG is reached only through rag-pipeline-mcp over the common MCP transport (Issue Implementation Intent); no remote-delegation or fallback path remains.

## Implementation
### Target file
`scripts/rag/augment.py`

### Procedure
1. Remove `run_http_augment`, `_forward_fetch_result`, the `last_fetch_result`, `http_stage_results`, `last_remote_identity`, and `map_http_result_kind` members, and `_last_fetch_result`/`_last_remote_identity`.
2. Remove the constructor parameters `http`, `set_fetch_result`, and `set_fallback_reason` (only the HTTP path used them) and their stored attributes; keep `cfg`, `on_status`, `search_diagnostics`, `llm`.
3. Remove the imports left unused (`httpx`, `dataclasses`, `RagPipelineError`, `HttpAugment`, `_map_http_result_kind`, `TwoStageFetchResult`, `HttpResultKind`, `ResultSource`, `CorpusIdentity`, `Any`) and rewrite the module docstring (it describes HTTP augment).
4. Keep `reset_request_state`, `last_stage_results`, `search_diagnostics`, and `run_refiner` unchanged; update the class docstring (no HttpAugment injection).

### Method
- Targeted edits; remove imports left unused as `ruff` reports them.

### Details
- `AugmentRefiner(` is constructed in exactly three places: `scripts/rag/pipeline.py` (document 04) and the two test modules named as companions below (impact radius measured with `rg -c`).
- `RagPipeline` keeps its own `_http` for `RagLLM`; only the refiner loses `http`.

### Companion test files
- `tests/rag/test_augment_refiner.py`
  - Procedure: Remove the HTTP-augment test classes and the `http` constructor argument; keep refiner and request-state cases.
  - Validation: `uv run pytest tests/rag/test_augment_refiner.py -v`
- `tests/rag/test_augment_integration.py`
  - Procedure: Remove the HTTP-augment integration cases and the `http` constructor argument; keep refiner integration.
  - Validation: `uv run pytest tests/rag/test_augment_integration.py -v`

## Compatibility considerations
- The removal is intentional and has no shim (`tools/check_compat_shims.py`).

## Security considerations
- Removes an outbound-token path and an empty-token default; no authentication or authorization behavior of the MCP server changes.

## Rollback considerations
- Revert the phase's commit; Phases 1 and 2 are one release unit and revert together.

## Validation plan
- `uv run pytest tests/rag/test_augment_refiner.py tests/rag/test_augment_integration.py -v`.
- `uv run ruff check scripts/ tests/ tools/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`.

## Completion criteria
- `AugmentRefiner` exposes only refiner and per-request state; no HTTP symbol remains in the module.

## Out of Scope
- Editing any other file.
- Adding any new fallback or remote-delegation mechanism.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change in `scripts/rag/augment.py` | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20261109-112608_adrrev003_rag-http-delegation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-092546_adrrev003_rag-http-delegation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-143149
- **Related target files**: `scripts/rag/augment.py`, `tests/rag/test_augment_refiner.py`, `tests/rag/test_augment_integration.py`
