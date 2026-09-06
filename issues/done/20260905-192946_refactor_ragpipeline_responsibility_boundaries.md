# Extract RagPipeline config resolution from __init__

## Priority
Medium

## Summary
Move config resolution logic from `RagPipeline.__init__` into a standalone function, reducing constructor responsibility count from 10 to ~6 and eliminating the `_ModuleConfig` singleton coupling.

## Background
`RagPipeline.__init__` (lines 92-218) currently performs 10 distinct responsibilities: HTTP client setup (line 102), status callback wiring (lines 103-104), per-run state field initialization (lines 106-115), config resolution from three sources (lines 118-179), SemanticCache instantiation (lines 180-183), RagLLM instantiation (lines 185-189), embed URL construction (line 190), DB path storage (lines 192-195), AugmentRefiner instantiation (lines 198-206), and logging (lines 208-217). This violates the single-responsibility principle and makes the constructor difficult to test independently.

The `_ModuleConfig` class (lines 64-78) implements a class-level singleton pattern for lazy config loading. It caches `ConfigLoader().load_all()` results at class level (`_cache: dict[str, str] | None = None`). This couples the pipeline to a global config source and makes testing harder because there is no way to inject a mock config loader.

`RagConfig` is defined as a Protocol in `scripts/shared/types.py:75`. `RagConfigImpl` (a frozen dataclass) satisfies this Protocol. The constructor accepts `cfg: RagConfig` which can be either a `RagConfigImpl` instance, a plain dict, or an object with `__dict__` (e.g., `SimpleNamespace`, `AgentConfig`).

## Problem
`RagPipeline.__init__` has 127 lines of code handling 10 distinct responsibilities. Config resolution logic (lines 118-179) is particularly dense: it handles three different input types (RagConfigImpl, dict, object with `__dict__`), fills missing required fields from hardcoded defaults (14 fields), validates via `RagConfigValidator`, and logs warnings/errors — all in one method. This makes the constructor hard to test, understand, and maintain.

Additionally, line 188 contains an unnecessary `cast(RagConfig, self._cfg)` inside `__init__`: after the if/else branch resolves `self._cfg`, its type is already `RagConfig` (either directly assigned as `RagConfigImpl` or cast from `RagConfigImpl(**_raw_cfg)`). The cast serves no purpose and indicates lingering type uncertainty.

## Reason for Change
- Maintainability risk: a single change to config handling requires understanding the entire constructor
- Testability concern: cannot mock config resolution without instantiating the full pipeline
- The `_ModuleConfig` singleton pattern prevents dependency injection and makes the pipeline's config source opaque
- Unnecessary `cast(RagConfig, self._cfg)` at line 188 indicates type confusion in the original design

## Implementation Intent
Create a module-level function `resolve_rag_config(cfg, *, module_cfg=None, config_loader=None)` that takes raw inputs and returns a validated `RagConfigImpl`. The constructor should delegate config resolution rather than performing it inline. This preserves the priority order: cfg > module_cfg > ConfigLoader().load_all(), but moves the complexity out of the constructor.

For `_ModuleConfig`: have `resolve_rag_config` accept an optional `config_loader` parameter. When `None`, fall back to creating a fresh `ConfigLoader().load_all()` (preserving current behavior). When provided, use the injected loader (enabling dependency injection for tests). This replaces the `_ModuleConfig` singleton without changing runtime behavior for non-test callers.

After config resolution, the constructor should only wire up the resolved config with its collaborators (SemanticCache, RagLLM, AugmentRefiner).

## Target Files or Areas
- `scripts/rag/pipeline.py` — primary target
- `tests/rag/` — tests depending on `RagPipeline.__init__` config behavior

## Required Changes
- Create `resolve_rag_config(cfg, *, module_cfg=None, config_loader=None) -> RagConfigImpl` function at module level in `pipeline.py`
- Replace inline config resolution in `RagPipeline.__init__` with: `self._cfg = resolve_rag_config(cfg, module_cfg=module_cfg)`
- Remove `_ModuleConfig` class entirely (no longer needed when `config_loader` is injected)
- Remove the unnecessary `cast(RagConfig, self._cfg)` at line 188
- Preserve the priority order: explicit cfg > module_cfg > config_loader()

## Constraints
- Must preserve public API: `RagPipeline.__init__` signature must remain compatible (http, cfg, module_cfg, on_status, on_clear parameters)
- Must not change external behavior: config resolution priority, validation errors, and warning messages must remain identical
- Must not introduce new dependencies
- Config resolution must still handle all three input types: RagConfigImpl, dict, and object with `__dict__`
- The `RagConfigValidator` integration must be preserved
- Default values for missing fields must remain identical (14 fields: llm_url="", embed_url="", rag_db_path="", sqlite_vec_so="", sqlite_timeout=30, sqlite_busy_timeout_ms=30000, mqe_n_queries=3, mqe_prompt_template="", rerank_prompt_template="", embed_retry=3, embed_workers=4, rag_pipeline_service_url=None, use_search=True, rag_service_url=None)

## Acceptance Criteria
- [ ] Config resolution is performed by a separate callable, not inline in the constructor
- [ ] `_ModuleConfig` class is removed
- [ ] Unnecessary `cast(RagConfig, self._cfg)` at line 188 is removed
- [ ] Public API contract unchanged: same constructor parameters, same exceptions raised
- [ ] All existing tests pass
- [ ] mypy passes on changed files
- [ ] ruff check passes on changed files

## Testing Expectations
- Run targeted tests: `uv run pytest tests/rag/test_pipeline*.py -v`
- Run full suite: `uv run pytest -v`
- Type check: `uv run mypy scripts/rag/pipeline.py`
- Lint check: `uv run ruff check scripts/rag/pipeline.py`
- Architecture check: `PYTHONPATH=scripts uv run lint-imports`
- Verify config resolution behavior: test with RagConfigImpl input, dict input, None input, and invalid config input

## Documentation Impact
No documentation update required unless the extracted config resolution function becomes a public API. If so, add docstring explaining the priority order and input types.

## Out of Scope
- Changing config resolution priority or defaults
- Adding new config sources or removing existing ones
- Modifying `RagConfigValidator` or `RagConfigImpl`
- Refactoring other methods in `RagPipeline` (search_queries, rerank_candidates, run, augment, get_diagnostics, invalidate_cache)
- Changing the AugmentRefiner or SemanticCache initialization logic

## Dependencies
N/A: none

## Unresolved Questions
- Should config resolution return `RagConfigImpl` directly, or should it return a dict that the caller passes to `RagConfigImpl(**...)`? The former eliminates the `cast()` call but requires the resolver to always produce a valid instance.
- Should the extracted config resolver also handle the logging of warnings/errors, or should that remain in the constructor?

## AI Implementation Instruction
- Do not rewrite unrelated files in `scripts/rag/`
- Keep changes minimal: only extract config resolution, do not restructure the entire class
- Preserve the exact config resolution priority: cfg > module_cfg > ConfigLoader().load_all()
- Preserve all exception types and error messages from config validation
- After extraction, verify no legacy symbol names remain (rg "RagConfigImpl\(\*\*.*_raw_cfg" scripts/rag/)
- Do not implement any behavior-changing ideas discovered during refactoring — record them as proposals instead
