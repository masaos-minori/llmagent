## Goal
- Make `RagPipeline.augment()` run the in-process pipeline only (REQ-001) and remove the fallback identity gate while keeping the corpus-generation record (REQ-002).

## Scope
**Release unit**: http-path-and-gate

- In scope: this one file, Phase 1 and Phase 2 of the Plan.
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
`scripts/rag/pipeline.py`

### Procedure
1. Phase 1: delete the HTTP branch of `augment()` (the `rag_query_service_url` check, `run_http_augment`, the `http_diag`/`http_records` state, and the diagnostics copy in `finally`), the `_merge_http_state` method, and the imports `_map_http_result_kind`, `HttpResultKind`; construct `AugmentRefiner` without `http=` and `set_fetch_result=`.
2. Phase 1: in `get_diagnostics()` drop the `http_result_kind` computation and the `http_result_kind=` argument of `PipelineDiagnostics.from_run_result` (document 07); rewrite the `augment()` docstring: the chain is search, refiner, raw chunks.
3. Phase 2: reduce the gate block to `local_identity = compute_local_identity(db, schema_version=SCHEMA_VERSION)` followed by `self._last_corpus_generation = local_identity.index_generation if local_identity.verified else None`; delete `_identity_gate`, the `IdentityGate` stage record, the reject/degraded branches, `_identity_degraded`, `_safe_corpus_id`, and their imports; remove `diagnostics["identity_degraded"]` from `get_diagnostics()` and keep `diagnostics["corpus_generation"]`.
4. Keep `reset_request_state()` at the top of `augment()` and the `RuntimeError` to `RagPipelineError` translation.

### Method
- Targeted edits; remove imports left unused as `ruff` reports them.

### Details
- `_last_corpus_generation` is read only by `get_diagnostics()` (RAGCORPUS001 REQ-004), so the local-identity computation stays; the gate was its only other consumer of `local_identity`.
- The frozen diagnostics contract lives in `tests/rag/test_diagnostics.py` (document 27).

### Companion test files
- `tests/rag/test_rag_pipeline.py`
  - Procedure: Drop `rag_query_service_url` and `rag_auth_token` from the config fixtures and any HTTP-mode case.
  - Validation: `uv run pytest tests/rag/test_rag_pipeline.py -v`
- `tests/rag/test_rag_pipeline_no_cache_freshness.py`
  - Procedure: Drop the removed keys from the config fixture.
  - Validation: `uv run pytest tests/rag/test_rag_pipeline_no_cache_freshness.py -v`

## Compatibility considerations
- The removal is intentional and has no shim (`tools/check_compat_shims.py`).

## Security considerations
- Removes an outbound-token path and an empty-token default; no authentication or authorization behavior of the MCP server changes.

## Rollback considerations
- Revert the phase's commit; Phases 1 and 2 are one release unit and revert together.

## Validation plan
- `uv run pytest tests/rag/test_rag_pipeline.py tests/rag/test_rag_pipeline_no_cache_freshness.py tests/rag/test_diagnostics.py -v`, then `uv run pytest tests/rag tests/mcp_servers/rag_pipeline -v`.
- `uv run ruff check scripts/ tests/ tools/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run python tools/check_module_size.py`.

## Completion criteria
- `augment()` has no HTTP branch and no gate; `rg -n "_identity_gate|_merge_http_state|rag_query_service_url" scripts/rag/pipeline.py` is empty; `get_diagnostics()` still reports `corpus_generation`.

## Out of Scope
- Editing any other file.
- Adding any new fallback or remote-delegation mechanism.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change in `scripts/rag/pipeline.py` | Completed | 20261110-151959 | 20261110-151959 | — |
| 2 | Add or update tests per Validation plan | Completed | 20261110-151959 | 20261110-151959 | — |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261110-151959 | 20261110-151959 | — |

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
- **Related target files**: `scripts/rag/pipeline.py`, `tests/rag/test_rag_pipeline.py`, `tests/rag/test_rag_pipeline_no_cache_freshness.py`
