# Implementation: scripts/rag/pipeline.py (remove post-rerank plugin hooks)

Source plan: `plans/done/20260717-123416_plan.md` (Implementation step 1, item 4)

Gap-filling note: see `implementations/20260717-224311_registry_py_plugin_removal.md`
for why this doc exists. This doc and its 4 siblings must all land BEFORE
`plugin_registry.py` is deleted (step 2). This file was not in the source
requirement's own target-file list; the plan's Unknowns section confirmed it
plugin-only by direct read before adding it to scope (see plan lines 50, 99).

## Goal

`RagPipeline.run()` no longer imports `plugin_registry` or invokes the
post-rerank plugin-hooks extension point; the pre-existing MQE→search→RRF→
rerank→augment flow is unchanged apart from this one removed block.

## Scope

**In scope**
- `scripts/rag/pipeline.py`: delete the `from shared.plugin_registry import (get_pipeline_post_stages, run_pipeline_stages)` import (lines 33-36) and the "Post-rerank plugin hooks" block inside `run()` (lines 302-317, the `if get_pipeline_post_stages(): ...` block including its `StageResult` append).
- Remove the now-dead `hook_strict: bool = False` parameter from `run()`'s signature (line 287) — confirmed by grep to have exactly one non-pipeline.py reference in the whole repo, `tests/test_plugin_registry.py:552`'s `test_hook_strict_mode_re_raises`, which is itself a plugin-only test already scheduled for deletion by the existing `plugin_test_files_removal` doc. No other production caller passes `hook_strict=` explicitly (confirmed via `grep -rn "hook_strict" scripts/` returning only this file's own definition and use).

**Out of scope**
- Deleting `plugin_registry.py` itself — step 2 (separate doc, must run after this one).
- Any other pipeline stage (`MqeStage`, `SearchStage`, `FusionStage`, `RerankStage`, `AugmentStage`) — unaffected; only the block between `RerankStage` and `AugmentStage` is removed.
- `StageResult`'s dataclass shape — unchanged; only the one call site that constructed a `stage_name="PluginHooks"` instance is removed.

## Assumptions

1. Confirmed by direct read (2026-07-17): the import spans lines 33-36, the plugin-hooks block spans lines 302-317 (from the `# Post-rerank plugin hooks (before AugmentStage)` comment through the closing `)` of the `StageResult(...)` append), and `run()`'s signature is at lines 282-288 with `hook_strict: bool = False` as its 4th parameter (line 287).
2. `hook_strict` has no caller outside this file and its own now-doomed test (`tests/test_plugin_registry.py:552`) — confirmed via `grep -rn "hook_strict" scripts/ tests/`. Removing the parameter is a genuine, complete cleanup (not scope creep) since an unused parameter left behind would be dead API surface; this finding was NOT explicitly listed in the plan's own Implementation step 1 text (which only mentions the import and call-site removal) but follows directly from the plan's own subtractive intent and its Design section's "trace to zero remaining call sites" principle.
3. `ctx.reranked` (read/written by the deleted block) is otherwise only read by `augment_stage` immediately after — confirmed the deleted block's sole side effect (reassigning `ctx.reranked` via `run_pipeline_stages`) has no other consumer between the deleted block and `AugmentStage`, so removing the block leaves `ctx.reranked` exactly as `RerankStage` produced it, unchanged in the no-plugin-hooks case (which is the only case in production today per plan Assumption 1 — no real plugins exist).

## Implementation

### Target file

`scripts/rag/pipeline.py`

### Procedure

1. Delete the import block (lines 33-36):
   ```python
   from shared.plugin_registry import (
       get_pipeline_post_stages,
       run_pipeline_stages,
   )
   ```
2. In `run()`'s signature, delete the `hook_strict: bool = False,` parameter (line 287).
3. Delete the plugin-hooks block (lines 302-317):
   ```python
   # Post-rerank plugin hooks (before AugmentStage)
   if get_pipeline_post_stages():
       t0 = time.perf_counter()
       ctx.reranked = await run_pipeline_stages(
           get_pipeline_post_stages(), ctx.reranked, query, strict=hook_strict
       )
       elapsed = time.perf_counter() - t0
       self.last_timings["PluginHooks"] = elapsed
       ctx.stage_results.append(
           StageResult(
               stage_name="PluginHooks",
               status="success",
               elapsed_seconds=elapsed,
               fallback_reason=None,
           )
       )
   ```
   leaving `pre_augment_stages` execution followed directly by `augment_stage = AugmentStage()`.

### Method

Direct deletions. No control-flow redesign — the pipeline simply stops offering a plugin-hooks extension point between rerank and augment.

### Details

- If `time` (used for `t0 = time.perf_counter()` only inside the deleted block) or `StageResult` become unused after this edit, check with `ruff check --select F401` and remove only what's actually flagged — both are very likely still used elsewhere in this file (other stages also use `time.perf_counter()` and construct `StageResult`), so do not remove those imports without confirming.
- Confirm no caller of `RagPipeline.run()` passes `hook_strict=` as a keyword argument before deleting the parameter — `grep -rn "\.run(" scripts/rag/ scripts/mcp_servers/rag_pipeline/ scripts/agent/` and check each call site's arguments; per Assumption 2 none currently do, but re-verify at implementation time since this repo has active concurrent edits.
- Test file changes (`test_plugin_registry.py` deletion, and any RAG-pipeline test asserting on `PluginHooks`/`hook_strict`) are the existing `plugin_test_files_removal` doc's job — do not edit test files from this doc, but flag to that doc's implementer if you find a RAG-specific test (not already on its list) that also needs updating for the `hook_strict` parameter removal.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| No plugin references remain in this file | `grep -n "plugin\|Plugin" scripts/rag/pipeline.py` | 0 matches |
| No dangling `hook_strict` references | `grep -rn "hook_strict" scripts/` | 0 matches |
| Syntax/lint | `uv run ruff check scripts/rag/pipeline.py` | 0 errors |
| Type check | `uv run mypy scripts/rag/pipeline.py` | no new errors |
| Targeted tests (expect some failures until step-2/step-6 docs also land) | `uv run pytest tests/test_rag_index_integrity.py -k pipeline -v` (or the actual RAG pipeline test file, confirm its name at implementation time) | pass once plugin-specific test cases are also removed |
