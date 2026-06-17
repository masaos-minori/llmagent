# Plan: rag/*.py structural refactoring (Phase 1 dependency mapping)

## Target modules and issues

### 1. `scripts/rag/pipeline.py`

| Issue | Location | Description |
|---|---|---|
| Module-level mutable global `_cfg` | Line 62 | `_cfg: dict | None = None` — lazy-loaded config cached at module level; prevents per-instance isolation in tests |
| `import asyncio` inside method | Line 122 | `import asyncio` inside `search_queries()` body — stdlib import should be at top of file |

**Importers of `pipeline.py`:**
- `scripts/mcp/rag_pipeline/service.py:51-52` — imports `RagPipeline`, `fetch_full_document`, `RagHit`, `RawHit`
- `scripts/agent/commands/cmd_ingest.py:87` — imports `RagPipeline`
- `tests/test_rag_pipeline.py:12` — imports `RagPipeline`, `RagPipelineError`, `RagHit`, `fetch_full_document`
- `tests/test_rag_pipeline_stage.py:260,291` — imports `RagPipeline`
- `tests/test_agent_rag.py:14` — imports `RagPipeline`
- `tests/test_rag_get_cfg.py:15` — patches `pipeline_mod._cfg`

**Impact of removing `_cfg`:**
- `_get_cfg()` function (lines 68-77) and its single caller in `__init__` (line 112) are affected
- Test `test_rag_get_cfg.py::TestRagPipelineGetCfg::test_get_cfg_error_path` directly patches `_cfg` — this test will need to change
- No other code reads `_cfg` directly

### 2. `scripts/rag/repository.py`

| Issue | Location | Description |
|---|---|---|
| Redundant `_get_sudachi_tokenizer()` | Lines 70-72 | Returns the module-level `_sudachi` variable — unnecessary indirection, can be inlined |

**Importers of `repository.py`:**
- `scripts/rag/pipeline.py:36-40` — imports `RagRepository`, `deduplicate_chunks`, `fetch_full_document`
- `scripts/rag/stages/rerank.py:6` — imports `deduplicate_chunks`
- `scripts/rag/stages/fusion.py:3` — imports `RagScorer`, `_dedup_hits`
- `scripts/rag/stages/search.py:12` — imports `RagRepository`
- `tests/test_rag_repository.py:12` — imports multiple symbols

**Impact of inlining `_get_sudachi_tokenizer()`:**
- Only internal function; no external callers import it
- `_build_fts_tokens_ja()` at line 83 calls it — will be changed to use `_sudachi` directly
- No test imports `_get_sudachi_tokenizer`

### 3. `scripts/rag/llm_client.py`

| Issue | Location | Description |
|---|---|---|
| Config reload on every call | Lines 237-239 | Module-level `summarize_tool_result()` calls `ConfigLoader().load()` on every invocation — inconsistent with pipeline.py's caching approach |

**Importers of `llm_client.py`:**
- `scripts/rag/llm.py:18` — re-exports all public symbols
- `scripts/agent/commands/cmd_tooling.py` — imports `summarize_tool_result` from `rag.llm`
- `tests/test_rag_pipeline_stage.py` — tests via `RagLLM` class

**Impact of caching config:**
- Module-level `summarize_tool_result()` function needs a cache mechanism (same pattern as pipeline.py's `_get_cfg()`)
- Behavior is unchanged for callers; config is loaded once and cached

## Dependency graph

```
rag.pipeline ──────────────► rag.repository
        │                         │
        ├─► rag.llm ──────────────┘
        │      │
        │      ▼
        │  rag.llm_prompts
        │  rag.llm_client
        │
        ├─► rag.cache
        ├─► rag.types ────► rag.enums
        ├─► rag.stage ────► rag.types
        ├─► rag.stages.* ─┘
        ├─► rag.pipeline_refiner ──► rag.llm
        └─► rag.pipeline_service
```

## No import cycles detected

The rag/ module has a clean DAG structure. No circular imports found in current code.
