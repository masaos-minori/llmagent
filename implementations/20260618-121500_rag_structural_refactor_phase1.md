# Implementation: rag/*.py structural refactoring Phase 1 — pre-resolved

## Goal

Resolve the three structural issues identified in plans/20260618-065848_plan.md.

## Status

All three issues were ALREADY resolved in the codebase before this plan was executed.
No code changes required.

## Issues (pre-resolved)

### 1. `pipeline.py` — module-level `_cfg` mutable global
- **Plan target:** Remove `_cfg: dict | None = None` at line 62
- **Current state:** `_ModuleConfig` class (lines 67-81) with class-level `_cache`; no module-level `_cfg` variable
- **`import asyncio`:** Already at top of file (line 20), not inside a method
- **Test:** `test_rag_get_cfg.py::TestRagPipelineGetCfg` already patches `_ModuleConfig._cache`, not `_cfg`

### 2. `repository.py` — `_get_sudachi_tokenizer()` indirection
- **Plan target:** Inline `_get_sudachi_tokenizer()` (lines 70-72)
- **Current state:** Function does not exist; `_sudachi` is used directly at line 78

### 3. `llm_client.py` — config reload on every `summarize_tool_result()` call
- **Plan target:** Add caching mechanism
- **Current state:** `_llm_url_cache: str | None = None` global + `_get_cached_llm_url()` function
  already implements caching (lines 51-63)
