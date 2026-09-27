## Goal

Add `llm_url`/`embed_url` kwargs to the 2 `RagPipelineConfig(...)` instances in `tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py::TestServiceStart`, fixing 2 tests that currently fail because `RagPipelineConfig` defaults `use_search=True` while these instances omit `llm_url`/`embed_url` (REQ-004).

## Scope

In scope: the 2 `RagPipelineConfig(...)` constructor calls inside `TestServiceStart` (lines ~511-517, ~534-540) only. Out of scope: `mcp_servers.rag_pipeline.rag_pipeline_models.RagPipelineConfig`'s own defaults (`use_search=True`, confirmed via `TestBuildRagCfgAdapter::test_defaults_when_cfg_empty`) and `scripts/rag/pipeline.py`/`scripts/rag/config_resolution.py` (both confirmed already correct); `TestBuildRagCfgAdapter` and other classes in this same file (unaffected, out of scope).

## Assumptions

- A placeholder non-empty URL string is sufficient — neither `test_no_module_level_cfg_override` nor `test_start_creates_pipeline_and_http_client` asserts on the specific value of `llm_url`/`embed_url`.

## Design decisions

- Add `llm_url=`/`embed_url=` as explicit kwargs to both `RagPipelineConfig(...)` calls, matching the existing kwarg style (`use_mqe=True, use_rrf=True, ...`).

## Alternatives considered

- Changing `RagPipelineConfig`'s own default `use_search` to `False` (mirroring `scripts/rag/config_resolution.py`'s `_DEFAULTS_FOR_ALL["use_search"]` fix from commit `5e568520`): rejected — out of scope per the Plan (a production default change affecting all `RagPipelineConfig` consumers, not just these 2 tests); the minimal, scoped fix is supplying the 2 tests' own missing fields.

## Implementation

### Target file

`tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py`

### Procedure

1. Re-confirm both `RagPipelineConfig(...)` call sites' current form via Read (lines ~501-541) — confirm `llm_url`/`embed_url` are still absent (adversarial re-verification).
2. Add `llm_url="http://llm.local", embed_url="http://embed.local"` as kwargs to both `fake_cfg = models_module.RagPipelineConfig(...)` calls (in `test_no_module_level_cfg_override` and `test_start_creates_pipeline_and_http_client`).

### Method

Direct kwarg addition to 2 constructor calls — no structural change.

### Details

- Before: `models_module.RagPipelineConfig(use_mqe=True, use_rrf=True, use_rerank=True, top_k_search=5, top_k_rerank=10)` (both call sites, identical).
- After: `models_module.RagPipelineConfig(use_mqe=True, use_rrf=True, use_rerank=True, top_k_search=5, top_k_rerank=10, llm_url="http://llm.local", embed_url="http://embed.local")`.

## Compatibility considerations

- No production code changes; test-fixture fix.

## Security considerations

N/A: test-only fixture values, not real credentials or endpoints.

## Rollback considerations

- `git revert` the commit, or manually remove the 2 added kwargs from both call sites.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py` | Unit | `uv run pytest tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py -q` | All tests pass, including `TestServiceStart`'s 2 previously-failing tests |

## Completion criteria

- `uv run pytest tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py -q` passes with no failures.

## Out of scope

- `tests/agent/commands/test_agent_rag.py`, `tests/rag/test_pipeline_http_result_kind.py`, `tests/rag/test_rag_http_mode.py` (each covered by its own implementation procedure document from this same Plan).
- `TestBuildRagCfgAdapter` and other classes in this same file (unaffected).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: no new test needed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no docs/00_index.md task-scope mapping for this test file |

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
- **Requirement ID**: REQ-004: add `llm_url`/`embed_url` to `TestServiceStart`'s `RagPipelineConfig` instances
- **Source issue**: issues/20260927-075240_rag001_rag-config-validation-rejects-fixtures-missing-llm_url-embed_url.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-082052_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-091513
- **Related target files**: tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py
