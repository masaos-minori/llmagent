# Refactor RagPipeline: extract config resolution, diagnostics, and stage lifecycle from pipeline.py

## Priority
Medium

## Summary
Reduce `scripts/rag/pipeline.py`'s complexity (587 lines) by extracting three concerns into dedicated modules: config resolution (`resolve_rag_config`), diagnostics formatting (`get_diagnostics`), and stage lifecycle management. Improve testability and adherence to single-responsibility boundaries.

## Background
`scripts/rag/pipeline.py` was originally designed as a thin orchestrator wrapping MQE → search → RRF → rerank stages. Over time, it accumulated additional responsibilities: inline configuration resolution (116 lines), diagnostics dict construction (67 lines), and tight coupling to `AugmentRefiner` in `__init__`. The module layout comment at line 12 already acknowledges four related files, but the actual boundary between `pipeline.py` and those files has blurred — `pipeline.py` imports and instantiates `AugmentRefiner` directly, constructs `RagRepository` instances inline in `search_queries`, and builds raw dicts in `get_diagnostics` instead of using typed objects.

## Problem
`pipeline.py` violates the single-responsibility principle in three distinct ways:

1. **Config resolution**: `resolve_rag_config()` (lines 63-178) is a standalone configuration resolution function with its own defaults, validation, and fallback logic. It has no dependency on pipeline orchestration — it only reads config sources and produces `RagConfigImpl`. Its presence in `pipeline.py` couples config resolution to pipeline internals.

2. **Diagnostics formatting**: `get_diagnostics()` (lines 521-587) constructs a flat dict with hardcoded keys (`"stage_results"`, `"timings"`, `"fusion_mode"`, etc.) that duplicates information already available via `PipelineRunResult` (a TypedDict/dataclass). Callers must deserialize this dict to access typed fields.

3. **Tight `AugmentRefiner` coupling**: `__init__` (lines 192-252) creates `AugmentRefiner` with lambda callbacks (`set_fetch_result=lambda fr: setattr(self, "last_fetch_result", fr)`) that bypass type safety. The constructor also stores five SQLite-related attributes (`_rag_db_path`, `_sqlite_vec_so`, `_sqlite_timeout`, `_sqlite_busy_timeout_ms`) that are only used in `augment()`, polluting the constructor signature.

Additionally, `search_queries()` (lines 299-335) and `SearchStage.run()` (lines 98-117 in `stages/search.py`) contain nearly identical embedding-fetch-and-search logic — the former is a public API, the latter is a stage implementation. When `augment()` calls `self.run()` internally, it also creates a `SQLiteHelper` instance — a resource that should be managed by a factory or context manager, not duplicated across callers.

## Reason for Change
- **Maintainability risk**: 587-line modules are hard to review and modify without unintended side effects. Each added feature requires scanning the entire file.
- **Testability degradation**: Tight `AugmentRefiner` coupling means unit-testing `RagPipeline.__init__` requires mocking HTTP clients, LLM instances, AND callback lambdas simultaneously.
- **Type safety erosion**: `get_diagnostics()` returns raw dicts; callers cannot benefit from IDE autocomplete or static type checking on diagnostic fields.
- **Duplication**: `search_queries()` and `SearchStage.run()` share the same embedding-fetch-and-search loop; `augment()` and `run()` each open their own `SQLiteHelper` instances.

## Implementation Intent
Extract three concerns into dedicated modules while preserving the public API contract of `RagPipeline`:

1. **Config resolution**: Move `resolve_rag_config()` to `rag/config_resolution.py`. Keep the function signature unchanged so callers do not break. The new module owns the defaults dict, validation logic, and source-priority ordering.

2. **Diagnostics**: Create `rag/diagnostics.py` with a `PipelineDiagnostics` dataclass mirroring the dict structure returned by `get_diagnostics()`. Replace `get_diagnostics()`'s dict construction with `PipelineDiagnostics.from_run_result()`. Update callers to use the typed object.

3. **Stage lifecycle**: Extract the stage-creation-and-execution loop from `RagPipeline.run()` into a `RagPipelineStageLifecycle` class. This class owns the `pre_augment_stages` list, the `augment_stage` handling, and the `ctx` mutation logic. `RagPipeline.run()` becomes a thin delegator.

4. **Decouple `AugmentRefiner`**: Pass `AugmentRefiner` as an optional constructor parameter with a default factory (`None`). If not provided, `augment()` falls back to creating one internally. Remove the lambda callback parameters — replace with direct attribute assignment after construction.

5. **SQLite connection management**: Introduce a `RagDatabaseConnection` context manager in `rag/db_connection.py` that wraps `SQLiteHelper.open/close` lifecycle. Both `augment()` and any future callers use it.

## Target Files or Areas
- `scripts/rag/pipeline.py` — reduce to ~200 lines (orchestration only)
- `scripts/rag/config_resolution.py` — new file for `resolve_rag_config()`
- `scripts/rag/diagnostics.py` — new file for `PipelineDiagnostics` dataclass
- `scripts/rag/stage_lifecycle.py` — new file for `RagPipelineStageLifecycle`
- `scripts/rag/db_connection.py` — new file for `RagDatabaseConnection`
- `scripts/rag/models_result.py` — add `PipelineDiagnostics` dataclass import
- `tests/rag/test_rag_pipeline*.py` — update tests for new module boundaries

## Required Changes
- Extract `resolve_rag_config()` to `rag/config_resolution.py`; update `pipeline.py` import
- Create `PipelineDiagnostics` dataclass in `rag/diagnostics.py`; replace `get_diagnostics()` dict construction
- Create `RagPipelineStageLifecycle` class in `rag/stage_lifecycle.py`; delegate from `RagPipeline.run()`
- Make `AugmentRefiner` an optional constructor parameter; remove lambda callbacks
- Create `RagDatabaseConnection` context manager in `rag/db_connection.py`; use in `augment()`
- Consolidate `search_queries()` and `SearchStage.run()` logic — either `search_queries()` delegates to `SearchStage` or both share a common helper
- Update all test files to import from new module locations
- Preserve backward compatibility: `RagPipeline` public methods (`run`, `augment`, `get_diagnostics`, `search_queries`, `rerank_candidates`, `get_diagnostics`) retain their signatures

## Constraints
- **Backward compatibility**: All public method signatures on `RagPipeline` must remain unchanged. Existing callers must not break.
- **No behavior change**: Refactoring must preserve exact runtime behavior — timings, error messages, logging output, and fallback chains must be identical.
- **No new dependencies**: Only stdlib additions allowed (e.g., `contextlib.contextmanager`). No third-party packages.
- **Preserve existing types**: Do not change `PipelineRunResult`, `StageResult`, `PipelineContext`, or `RagHit` definitions unless necessary for the diagnostics extraction.
- **Testing requirement**: Every extracted module must have its own test file before merging.

## Acceptance Criteria
- [ ] `pipeline.py` is under 250 lines (excluding blank lines and comments)
- [ ] `resolve_rag_config()` exists in `rag/config_resolution.py` and is imported by `pipeline.py`
- [ ] `PipelineDiagnostics` dataclass exists in `rag/diagnostics.py` and replaces `get_diagnostics()` dict construction
- [ ] `RagPipelineStageLifecycle` class exists in `rag/stage_lifecycle.py` and is instantiated by `RagPipeline`
- [ ] `RagDatabaseConnection` context manager exists in `rag/db_connection.py` and is used by `augment()`
- [ ] `AugmentRefiner` is an optional constructor parameter on `RagPipeline` (default `None`)
- [ ] All existing tests pass without modification (only import path changes if needed)
- [ ] New modules have their own test coverage (≥80% branch coverage)

## Testing Expectations
- Unit tests for `config_resolution.py`: verify priority ordering, defaults application, and validation error propagation
- Unit tests for `diagnostics.py`: verify `PipelineDiagnostics.from_run_result()` produces correct field values
- Unit tests for `stage_lifecycle.py`: verify stage execution order, timing recording, and fallback detection
- Unit tests for `db_connection.py`: verify `open/close` lifecycle and exception handling
- Integration tests: re-run `pytest tests/rag/test_rag_pipeline*.py -v` to confirm no behavioral regression
- Type check: `uv run mypy scripts/rag/ --no-error-summary` passes without new errors

## Documentation Impact
Update `pipeline.py` module docstring to reflect new module layout (replace the old layout comment with references to the new files). Add docstrings to `PipelineDiagnostics` and `RagPipelineStageLifecycle` classes describing their responsibility boundaries. Document the `RagDatabaseConnection` context manager's usage pattern.

## Out of Scope
- Adding new pipeline stages or modifying existing stage behavior
- Changing the RAG pipeline algorithm (MQE → search → RRF → rerank order)
- Modifying `AugmentRefiner` internal logic or its HTTP/refiner delegation
- Adding caching layers or performance optimizations beyond what refactoring enables
- Migrating to a different database abstraction layer

## Dependencies
- `issue-to-plan` will produce a plan from this issue before implementation
- `python-test-and-fix` skill for test updates after refactoring

## Unresolved Questions
- Should `RagPipelineStageLifecycle` accept `RagConfig` or `RagConfigImpl`? Current code casts `RagConfig` in `run()`, but `RagConfigImpl` is more specific.
- Does `search_queries()` need to remain a public method, or can it be replaced by `SearchStage` instantiation + execution?
- Should `PipelineDiagnostics` include cumulative counters (`stat_search_embed_failed`, `stat_search_fts_errors`) or only per-run diagnostics?

## AI Implementation Instruction
- Do NOT rewrite unrelated files outside the listed target files.
- Preserve all public method signatures on `RagPipeline` exactly.
- Run `uv run mypy scripts/rag/` after each extraction to catch type regressions early.
- Write tests for each new module BEFORE moving production code — characterize current behavior first.
- Verify `pytest tests/rag/test_rag_pipeline*.py -v` passes after every phase, not just at the end.
- If a public method currently relies on a private attribute that would be moved, create a forwarding property rather than changing the caller.
