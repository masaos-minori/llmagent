## Goal
Remove `use_semantic_cache`/`semantic_cache_max_size`/`semantic_cache_threshold`
references from `tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py`'s
four affected test methods, made obsolete by procedure documents `06`/`07`
(`REQ-004`, `REQ-005`, `REQ-009`).

## Scope
- **In-Scope**, four locations:
  1. `TestBuildRagCfgAdapter.test_defaults_when_cfg_empty`: remove
     `assert ns.semantic_cache_max_size == 100` (line 43) and
     `assert ns.semantic_cache_threshold == 0.92` (line 44).
  2. `TestBuildRagCfgAdapter.test_overrides_from_cfg`: remove
     `semantic_cache_max_size=64,` (line 60) and `semantic_cache_threshold=0.85,`
     (line 61) from the `RagPipelineConfig(...)` construction; remove
     `assert ns.semantic_cache_max_size == 64` (line 76) and
     `assert ns.semantic_cache_threshold == 0.85` (line 77).
  3. The `required_fields`-list test (around line 95-155): remove
     `semantic_cache_max_size=64,`, `semantic_cache_threshold=0.85,`,
     `use_semantic_cache=True,` (lines 107-109) from the `RagPipelineConfig(...)`
     construction; remove `"semantic_cache_max_size",`, `"semantic_cache_threshold",`
     (lines 118-119) and `"use_semantic_cache",` (line 136) from the `required_fields`
     list; remove `assert adapter.semantic_cache_max_size == 64`,
     `assert adapter.semantic_cache_threshold == 0.85`,
     `assert adapter.use_semantic_cache is True` (lines 153-155).
  4. `TestBuildModuleCfg.test_translates_config_fields`: remove
     `semantic_cache_max_size=64,` (line 518) and `semantic_cache_threshold=0.5,`
     (line 519) from the `RagPipelineConfig(...)` construction; remove
     `assert module_cfg["semantic_cache_max_size"] == 64` (line 530) and
     `assert module_cfg["semantic_cache_threshold"] == 0.5` (line 531).
- **Out-of-Scope**: every other field/assertion in all four test methods (`use_mqe`,
  `use_rrf`, `use_rerank`, `use_refiner`, `top_k_search`, `refiner_*`, `rag_auth_token`,
  `llm_url`, `embed_url`, `rag_db_path`, etc.) — confirmed unrelated by reading each
  method in full; every other test class in this file.

## Assumptions
- `RagPipelineConfig` (procedure document `06`) no longer accepts the three removed
  keys as constructor arguments once that document lands — all four
  `RagPipelineConfig(...)` calls in this file's affected tests must stop passing them.
- `build_rag_cfg_adapter()`'s returned `SimpleNamespace` (procedure document `06`) no
  longer has the three attributes — `TestBuildRagCfgAdapter`'s assertions on `ns.*`/
  `adapter.*` must stop reading them.
- `RagPipelineMCPService._build_module_cfg()` (procedure document `07`) no longer
  copies `semantic_cache_max_size`/`semantic_cache_threshold` into its returned dict —
  `TestBuildModuleCfg`'s assertions on `module_cfg["..."]` must stop reading them
  (note: `use_semantic_cache` was never in `_build_module_cfg()`'s output, confirmed
  by procedure document `07`'s own investigation, so `TestBuildModuleCfg` has no
  `use_semantic_cache` reference to remove).

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §7, narrow bullet only)
- Treat the four locations as independent edits within the same file, since each
  targets a distinct test method with its own construction/assertion pair — no shared
  fixture links them.
- In the `required_fields`-list test, remove the list entries and their corresponding
  `hasattr`-loop check together with the explicit value assertions — both check the
  same three now-removed attributes from two angles (presence via `hasattr`, value via
  direct read); leaving one without the other would be an incomplete cleanup.

## Alternatives considered
N/A: straightforward removal of now-invalid constructor arguments and assertions
across four locations with no remaining subject to test.

## Implementation
### Target file
`tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py`

### Procedure
1. In `test_defaults_when_cfg_empty`, remove the two `assert ns.semantic_cache_*`
   lines (43-44).
2. In `test_overrides_from_cfg`, remove the two constructor kwargs (60-61) and the
   two corresponding assertions (76-77).
3. In the `required_fields`-list test, remove the three constructor kwargs (107-109),
   the three `required_fields` list entries (118-119, 136), and the three value
   assertions (153-155).
4. In `TestBuildModuleCfg.test_translates_config_fields`, remove the two constructor
   kwargs (518-519) and the two corresponding assertions (530-531).

### Method
Direct `Edit` across four independent locations in the same file.

### Details
- Re-read each of the four test methods' current line numbers immediately before
  editing (per Step 3a Adversarial Verification), since earlier edits within this same
  file shift later line numbers.
- Confirm after editing: `rg -n "semantic_cache"
  tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py` returns zero
  matches.

## Compatibility considerations
N/A: test-only file; no production caller depends on it.

## Security considerations
N/A: no security-sensitive code path is touched.

## Rollback considerations
- Revert via `git checkout` on this single file; must be reverted together with
  procedure documents `06` (`rag_pipeline_models.py`) and `07`
  (`rag_pipeline_service.py`).

## Validation plan
- `uv run pytest tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py -v` —
  all tests pass across all four affected methods.
- `rg -n "semantic_cache"
  tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py` — zero matches.

## Completion criteria
- No reference to any of the three removed keys remains in this file (Plan `AC-4`,
  `AC-8`).
- All four affected test methods pass against the modified
  `RagPipelineConfig`/`build_rag_cfg_adapter()`/`_build_module_cfg()`.

## Out of scope
- `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py` (procedure document `06`).
- `scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py` (procedure document `07`).
- Every other test class/method in this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: assertion/fixture cleanup only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: `REQ-005` (assert `_build_module_cfg()` no longer copies the two keys); `REQ-004` (assert `RagPipelineConfig`/`build_rag_cfg_adapter()` no longer carry the three fields)
- **Source issue**: issues/20260902-150340_semcacheconfig_remove_semanticcache_settings_from_config_contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-141001_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-185605
- **Related target files**: tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py
