# Refactor pipeline.py — separation of concerns

## Priority
Medium

## Summary
Split `scripts/rag/pipeline.py`'s `RagPipeline` class (672 lines) into focused modules to separate its remaining mixed concerns — config resolution, stage-status determination, the `augment()` fallback chain, and diagnostics construction — now that the actual retrieval stages (MQE, search, fusion, rerank) already live in `rag/stages/*.py`.

## Background
`rag/pipeline.py`'s own module docstring documents a "Module layout" that already delegates several concerns to sibling modules: `rag/repository.py` (RagRepository/RagScorer/SemanticCache/FTS), `rag/llm_client.py` (RagLLM/get_embedding), `rag/pipeline_service.py` (external RAG service delegation), `rag/pipeline_refiner.py` (context refiner), and `rag/stages/{mqe,search,fusion,rerank,augment}.py` (the four pipeline stages plus the augment stage). Despite that prior extraction, `RagPipeline` itself still combines several independent responsibilities beyond "orchestrate the stages." Similar splits were already completed for `scripts/agent/orchestrator.py`, `scripts/agent/repl.py`, and `scripts/rag/ingestion/ingester.py` (see `issues/done/20260829-080923_refactor_001_orchestrator_separation.md`, `_002_repl_separation.md`, `_003_ingester_separation.md`).

## Problem
`RagPipeline` exceeds the 400-line threshold defined in `skills/DESIGN.md` File Split Rule trigger condition (672 lines) and combines at least five distinct concerns:

1. **Config resolution** — `__init__` (roughly lines 93-208, ~115 lines) — resolves `cfg` through a priority chain (`RagConfigImpl` instance > dict > object with `__dict__` > `module_cfg` > `ConfigLoader().load_all()`), fills in a hardcoded set of default values for fields missing from the raw config, then runs `RagConfigValidator` and raises on validation failure.
2. **Stage execution and status determination** — `_run_stage`, `_get_stage_status`, `_mqe_status`, `_search_status`, `_fusion_status`, `_rerank_status` — runs one stage, catches its exceptions, and classifies the outcome as success/fallback/failure per stage type via a name-based dispatch (`type(stage).__name__ == "MqeStage"`, etc.).
3. **Search and rerank helpers** — `search_queries` (concurrent embedding fetch + sequential vector/FTS search) and `rerank_candidates` (Cross-Encoder rerank + dedup) — thin wrappers that mostly duplicate logic already present in `rag/stages/search.py` and `rag/stages/rerank.py`.
4. **`augment()` fallback chain** — `augment`, `_run_http_augment`, `_run_refiner` — a five-step fallback chain (HTTP service → semantic cache → search pipeline → refiner → raw chunks) documented in `augment()`'s own ~40-line docstring, which is itself evidence of the method's complexity.
5. **Diagnostics construction** — `get_diagnostics` (~65 lines) — builds a diagnostics dict from `last_stage_results`/`last_fetch_result`/`last_search_diagnostics`, including refiner-specific fallback-reason counting logic.

The `__init__` config-resolution block in particular hardcodes a `_required_fields` frozenset and a parallel `_defaults_for_missing` dict that must be kept in sync by hand, and mixes that with cache/LLM-client construction and use_rrf/use_mqe logging — none of which is "orchestrate the stages" in the sense the module docstring describes.

## Reason for Change
- The config-resolution block in `__init__` is a self-contained algorithm (priority chain + default-filling + validation) that is currently untestable except by constructing a full `RagPipeline`.
- `augment()`'s fallback chain is complex enough to need a dedicated docstring explaining five fallback steps and an "identity vs truthiness" caveat — a strong signal it should be its own unit, testable independently of stage execution.
- `get_diagnostics()`'s refiner-specific counting logic changes independently of the rest of the pipeline (e.g., adding a new fallback reason) but currently requires touching the same file as stage orchestration.
- `search_queries`/`rerank_candidates` appear to duplicate logic already encapsulated in `rag/stages/search.py`/`rag/stages/rerank.py` — worth confirming during implementation planning whether they are dead code, a legacy path, or intentionally kept as a lower-level API.

## Implementation Intent
Extract the concerns above into separate modules/classes, following the constructor-injection / delegation pattern already used for the `orchestrator.py` and `ingester.py` splits. Suggested (not mandatory) grouping, left for the implementation planning phase to finalize:
- **Config resolver** — owns the `__init__` config priority-chain resolution, default-filling, and `RagConfigValidator` invocation, returning a validated `RagConfig`.
- **Stage runner** — owns `_run_stage` and the per-stage status classifiers (`_get_stage_status`, `_mqe_status`, `_search_status`, `_fusion_status`, `_rerank_status`).
- **Augment orchestrator** — owns the `augment()` fallback chain, `_run_http_augment`, `_run_refiner`.
- **Diagnostics builder** — owns `get_diagnostics()`.

`RagPipeline` should become a thinner composition facade wiring these components together, preserving the `RagPipelineLike` Protocol (`scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py`) surface — `augment()`, `last_fetch_result`, `last_timings`, `invalidate_cache()` — and the rest of its current public interface (`run()`, `get_diagnostics()`, `search_queries()`, `rerank_candidates()`) unchanged.

## Target Files or Areas
- `scripts/rag/pipeline.py` — primary target
- `scripts/rag/stages/mqe.py`, `search.py`, `fusion.py`, `rerank.py`, `augment.py` — existing stage implementations; referenced, not modified
- `scripts/rag/stage.py` — referenced by `PipelineContext`, `PipelineStage`, `StageResult`
- `scripts/rag/repository.py`, `llm_client.py`, `cache.py`, `http_augment.py`, `pipeline_refiner.py`, `models_config.py`, `models_data.py`, `models_result.py`, `types.py` — referenced dependencies, not modified
- `shared/config_loader.py`, `shared/config_validator.py`, `shared/llm_client.py`, `shared/types.py` — referenced dependencies, not modified
- `scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py` — consumer via the `RagPipelineLike` Protocol; must continue to work unmodified
- `tests/rag/test_rag_pipeline.py`, `test_rag_pipeline_stage.py`, `test_pipeline_refiner_fallback.py`, `test_pipeline_http_result_kind.py` — to be reorganized alongside the split
- Documentation: `docs/03_rag_03_02_query_pipeline-rag-pipeline-class.md` and related `03_rag_03_*` files are the likely candidates — confirm against `docs/00_index.md`'s task-scope mapping before editing

## Required Changes
- Extract the config-resolution logic in `__init__` into its own resolver, testable independently of `RagPipeline` construction.
- Extract `_run_stage` and the per-stage status classifiers into a stage-runner unit.
- Extract the `augment()` fallback chain (`augment`, `_run_http_augment`, `_run_refiner`) into its own orchestrator.
- Extract `get_diagnostics()` into a diagnostics builder.
- Confirm during implementation whether `search_queries`/`rerank_candidates` duplicate `rag/stages/search.py`/`rag/stages/rerank.py` and, if so, resolve the duplication (removal, delegation, or documented reason to keep both) as part of this issue rather than leaving it unaddressed.
- Preserve the `RagPipelineLike` Protocol surface (`augment()`, `last_fetch_result`, `last_timings`, `invalidate_cache()`) exactly.
- Preserve `RagPipeline`'s other current public methods (`run()`, `get_diagnostics()`, `search_queries()`, `rerank_candidates()`) with identical signatures and behavior.

## Constraints
- Do not change the `augment()` fallback chain's order or any of its fallback conditions (HTTP → semantic cache → search pipeline → refiner → raw chunks) — behavior must be identical before and after the split.
- Do not change the `get_diagnostics()` dict's keys or value semantics — `rag_pipeline_service.py` and its tests may depend on the exact shape.
- Do not change the `RagPipelineLike` Protocol definition in `rag_pipeline_service.py` unless a genuinely new capability requires it (out of scope here — flag as a separate issue if discovered).
- Do not change any existing log message string.
- `RagConfigValidator`'s validation behavior and error/warning handling in `__init__` must remain identical.

## Acceptance Criteria
- Each resulting module/class addresses exactly one of the four concerns listed under Implementation Intent (config resolution, stage running/status, augment orchestration, diagnostics).
- `RagPipeline`'s public interface (`__init__`, `run`, `augment`, `get_diagnostics`, `search_queries`, `rerank_candidates`, `invalidate_cache`, `last_fetch_result`, `last_timings`, `last_stage_results`, `last_search_diagnostics`, `stat_search_embed_failed`, `stat_search_fts_errors`) retains identical signatures, attribute names, and behavior after the refactor.
- `scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py`'s `RagPipelineLike` usage continues to work unmodified.
- All pre-existing tests in the affected test files pass unchanged in outcome (reorganized as needed).
- The `search_queries`/`rerank_candidates` duplication question (see Required Changes) is resolved and documented in the resulting plan or implementation procedure, not left silently unaddressed.
- `ruff`, `mypy`, and `bandit` are clean on all new/modified files.
- A full `uv run pytest` run shows no new failures compared to the pre-change baseline.

## Testing Expectations
- Run `tests/rag/test_rag_pipeline.py`, `test_rag_pipeline_stage.py`, `test_pipeline_refiner_fallback.py`, and `test_pipeline_http_result_kind.py` (reorganized to match the new module layout) and confirm no behavioral regression.
- Run the `tests/mcp_servers/rag_pipeline/` suite to confirm `RagPipelineLike` consumers are unaffected.
- Run the full `uv run pytest` suite once after implementation and compare against the pre-change baseline for new failures.
- Apply the standard validation sequence in `rules/toolchain.md` (format → lint → type → arch → security → test → coverage).

## Documentation Impact
`docs/03_rag_03_02_query_pipeline-rag-pipeline-class.md` and possibly `03_rag_03_03_query_pipeline-context-and-diagnostics.md` (which documents `get_diagnostics()`'s fields) reference `RagPipeline`'s current structure — check `docs/00_index.md`'s "Document References by Task" table against whichever files this issue's implementation actually touches, and update only the matched row(s) to reflect the new module boundaries without duplicating implementation detail (per `skills/DESIGN.md` Avoid implementation-reference duplication).

## Out of Scope
- Changing the `augment()` fallback chain's logic, order, or conditions.
- Changing the `get_diagnostics()` output schema.
- Changing the `RagPipelineLike` Protocol's method/attribute set.
- Modifying `rag/stages/*.py`, `rag/repository.py`, `rag/llm_client.py`, `rag/pipeline_refiner.py`, or `rag/http_augment.py` internals.
- Adding new pipeline stages or fallback steps.
- Performance optimization of the retrieval or rerank pipeline.

## Dependencies
N/A: none

## Unresolved Questions
- Whether `search_queries()`/`rerank_candidates()` duplicate `rag/stages/search.py`/`rag/stages/rerank.py` and should be removed, kept as a documented lower-level API, or merged — needs confirmation during implementation planning (see Required Changes).
- Exact module names and file layout for the four extracted concerns are left to the `issue-to-plan` / `plan-to-implementation-procedure` phases.

## AI Implementation Instruction
- Do not change observable behavior: preserve the `augment()` fallback chain's order/conditions, the `get_diagnostics()` output shape, log message text, and the `RagPipelineLike` Protocol surface exactly.
- Extract the four concerns into separate modules/classes; you may follow the composition/delegation pattern used in `scripts/agent/orchestrator.py`'s and `scripts/rag/ingestion/ingester.py`'s splits as a reference, but it is not mandatory.
- Investigate and resolve the `search_queries`/`rerank_candidates` duplication question rather than silently carrying it forward.
- Verify `scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py` still works against the refactored `RagPipeline` via the `RagPipelineLike` Protocol.
- Do not touch out-of-scope items (fallback-chain logic changes, diagnostics schema changes, Protocol changes, stage internals).
- If a required design decision (module layout, duplication resolution) is unclear, stop and record it under Unresolved Questions rather than guessing.
