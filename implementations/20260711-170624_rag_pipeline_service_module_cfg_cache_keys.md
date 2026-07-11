# Implementation: scripts/mcp_servers/rag_pipeline/service.py — extend module_cfg with cache/rrf keys

## Goal

Extend the `module_cfg` dict built in `RagPipelineMCPService.start()` to include
`use_rrf`, `semantic_cache_max_size`, and `semantic_cache_threshold` (pulled from the
already-loaded `cfg: RagPipelineConfig`). Without this, `RagConfigValidator`'s flat-shape
fix alone would still be validating a dict that structurally never contains these keys
for the MCP path, defeating the goal of making "MCP module config path receives
meaningful validation."

## Scope

**In:**
- `scripts/mcp_servers/rag_pipeline/service.py::RagPipelineMCPService.start()` — add 3
  keys to the `module_cfg: dict[str, object]` literal (current lines 75-85)

**Out:**
- No change to `rag_cfg = build_rag_cfg_adapter(cfg)` (the separate `RagConfig`-typed
  object passed as `RagPipeline`'s `cfg` parameter) — untouched by this plan
- No change to `RagPipelineConfig` itself (`scripts/mcp_servers/rag_pipeline/models.py`) —
  it already has `use_rrf`, `semantic_cache_max_size`, `semantic_cache_threshold` as real
  fields; only reading them into `module_cfg` is new
- No change to any `_resolved_cfg.get(...)` call site elsewhere in `pipeline.py` — none of
  these 3 keys are currently read there (confirmed by grep in the plan's research), so
  there is no consumer to conflict with

## Assumptions

1. `RagPipelineMCPService.start()`'s `module_cfg` dict (current lines 75-85, confirmed by
   direct read) includes `llm_url`, `embed_url`, `rag_db_path`, `sqlite_vec_so`,
   `sqlite_timeout`, `sqlite_busy_timeout_ms`, `mqe_n_queries`, `mqe_prompt_template`,
   `rerank_prompt_template` — but not `use_rrf`, `semantic_cache_max_size`, or
   `semantic_cache_threshold`.
2. `cfg` (the `RagPipelineConfig.load()` result, bound at the top of `start()`) has
   `use_rrf`, `semantic_cache_max_size`, and `semantic_cache_threshold` as real attributes
   with real values (confirmed by direct read of
   `scripts/mcp_servers/rag_pipeline/models.py`).
3. `module_cfg` is passed to `RagPipeline(self._http, rag_cfg, module_cfg=module_cfg)`,
   which in turn is what reaches `RagConfigValidator.validate(_resolved_cfg)` inside
   `rag/pipeline.py` — adding these 3 keys here is what makes the validator's flat-shape
   checks (companion doc `20260711-170540_...`) actually see real values for the MCP path,
   instead of validating an empty/absent set of keys.
4. Adding keys to `module_cfg` is purely additive — no existing `_resolved_cfg.get(...)`
   call anywhere in `pipeline.py` reads these 3 key names today, so there is no shadowing
   or semantic conflict risk.

## Implementation

### Target file

`scripts/mcp_servers/rag_pipeline/service.py`

### Procedure

1. Locate the `module_cfg: dict[str, object] = {...}` literal inside `start()`.
2. Add 3 new entries to the dict literal, in the same style as the existing entries
   (`"key": cfg.attr`):
   - `"use_rrf": cfg.use_rrf`
   - `"semantic_cache_max_size": cfg.semantic_cache_max_size`
   - `"semantic_cache_threshold": cfg.semantic_cache_threshold`
3. Preserve the existing 9 keys and their order; append the 3 new keys after
   `"rerank_prompt_template"` (or in a position that keeps the dict readable — exact
   ordering is not semantically significant, but grouping the 3 new cache/rrf-related
   keys together aids readability).
4. No other lines in `start()` change.

### Method

Single dict-literal edit: 3 new `"key": value` lines added to an existing `dict[str, object]`
literal. No new imports, no signature changes, no control-flow changes.

### Details

- Type annotation `dict[str, object]` already accommodates `bool` (`use_rrf`), `int`
  (`semantic_cache_max_size`), and `float` (`semantic_cache_threshold`) values — no
  annotation change needed.
- This is an additive-only change: any code path that only reads the previously-existing
  9 keys is completely unaffected.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/mcp_servers/rag_pipeline/service.py` | 0 errors |
| Type check | `uv run mypy scripts/mcp_servers/rag_pipeline/service.py` | No new errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations (no new imports added) |
| Regression | `uv run pytest tests/test_rag_pipeline_mcp_service.py tests/test_mcp_rag_pipeline.py -q` | No new failures — confirms `RagPipeline` construction with the extended `module_cfg` still succeeds |
| Manual | Start the MCP RAG service (or exercise `start()` in a test) and confirm `RagConfigValidator.validate()` (once its flat-shape fix is in place) reports non-trivial results (not silently empty) for the MCP path | Validator sees real `use_rrf`/`semantic_cache_max_size`/`semantic_cache_threshold` values, confirming the Acceptance Criteria "MCP module config path receives meaningful validation" |
