## Goal
Remove `semantic_cache_max_size`/`semantic_cache_threshold` from
`RagPipelineMCPService._build_module_cfg()`
(`scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py`) (`REQ-005`).

## Scope
- **In-Scope**: remove `"semantic_cache_max_size": cfg.semantic_cache_max_size,` (line
  97) and `"semantic_cache_threshold": cfg.semantic_cache_threshold,` (line 98) from
  `_build_module_cfg()`'s returned dict.
- **Out-of-Scope**: every other key/value pair in the returned dict (`llm_url`,
  `embed_url`, `rag_db_path`, `sqlite_vec_so`, `sqlite_timeout`,
  `sqlite_busy_timeout_ms`, `mqe_n_queries`, `mqe_prompt_template`,
  `rerank_prompt_template`, `use_rrf`) — confirmed unrelated by reading the full
  method; `start()`'s remaining setup (`RagPipelineConfig.load()`,
  `build_rag_cfg_adapter(cfg)`, `http_timeout`, etc.) — confirmed unrelated. Note
  `use_semantic_cache` is **not** present in this method's dict (confirmed by `grep`)
  — only the two numeric-tuning keys are forwarded here, matching this Plan's own
  Repository Evidence ("2 lines").

## Assumptions
- Same hard ordering dependency as procedure documents `01`-`06`: this change must not
  be applied until `semcacherm` has landed — `rag.pipeline._ModuleConfig.get()`
  (consumer of this method's output, per `semcacherm`'s Plan evidence) still reads
  `semantic_cache_max_size`/`semantic_cache_threshold` to construct `SemanticCache`
  until that Plan's changes land.
- `RagPipelineConfig` (procedure document `06`) no longer has
  `semantic_cache_max_size`/`semantic_cache_threshold` attributes by the time this
  document's change is applied — `cfg.semantic_cache_max_size`/
  `cfg.semantic_cache_threshold` would otherwise raise `AttributeError` if this
  document's removal preceded that one.

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §6, narrow bullet only)
- Remove both lines together — they are the same semantic unit (cache tuning
  parameters) and were confirmed to have no other reader once
  `rag.pipeline._ModuleConfig`'s cache construction is removed by `semcacherm`.

## Alternatives considered
N/A: straightforward removal of two dict-entry lines with no remaining consumer.

## Implementation
### Target file
`scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py`

### Procedure
1. Re-verify `semcacherm` has landed and procedure document `06`
   (`RagPipelineConfig`) has landed (Assumptions) before proceeding.
2. Remove `"semantic_cache_max_size": cfg.semantic_cache_max_size,` (line 97) from
   `_build_module_cfg()`'s returned dict.
3. Remove `"semantic_cache_threshold": cfg.semantic_cache_threshold,` (line 98) from
   the same dict.

### Method
Direct removal via `Edit` on two dict-literal entries.

### Details
- Confirm after editing: `rg -n "semantic_cache" scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py`
  returns zero matches (this file has no other cache-related reference after
  procedure document `06`'s companion changes to `rag_pipeline_models.py` and
  `semcacherm`'s own removal of `invalidate_cache()` from this same file, procedure
  document `06` of the `semcacherm` Plan).
- `_build_module_cfg()`'s return type (`dict[str, Any]`) is unchanged; only its
  contents shrink by two keys.

## Compatibility considerations
- The dict this method returns is passed to `rag.pipeline._ModuleConfig` (via
  `start()`'s `module_cfg = self._build_module_cfg(cfg)`), which (per `semcacherm`'s
  Plan) no longer reads these two keys once that Plan's changes land — the two are
  sequenced so no intermediate state reads a missing key.

## Security considerations
N/A: no security-sensitive code path is touched.

## Rollback considerations
- Revert via `git checkout` on this single file; should be reverted together with
  `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`'s procedure document `06`
  (`RagPipelineConfig`'s field removal), since this method reads `cfg.semantic_cache_max_size`/
  `cfg.semantic_cache_threshold` from that type.

## Validation plan
- `uv run pytest tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py -v`
  (updated by its own procedure document) — passes; confirms `_build_module_cfg()`'s
  output no longer contains the two removed keys.
- `rg -n "semantic_cache" scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py` —
  zero matches.

## Completion criteria
- `_build_module_cfg()` no longer copies `semantic_cache_max_size`/
  `semantic_cache_threshold` (Plan `AC-4`).
- `tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py` passes.

## Out of scope
- `RagPipelineConfig` itself (procedure document `06`).
- Every other key in `_build_module_cfg()`'s returned dict.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Blocked until `semcacherm` and procedure document `06` land — see Assumptions |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by procedure document for `tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: documentation deferred to `semcachedocs` |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Depends on `semcacherm`'s implementation and this Plan's `rag_pipeline_models.py` change landing first | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-005` (remove the two keys from `_build_module_cfg()`)
- **Source issue**: issues/20260902-150340_semcacheconfig_remove_semanticcache_settings_from_config_contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-141001_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-185605
- **Related target files**: scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py
