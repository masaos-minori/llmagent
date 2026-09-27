## Goal

Add non-empty `llm_url`/`embed_url` keys to `tests/agent/commands/test_agent_rag.py::_make_cfg`'s defaults dict, fixing 5 `TestAugmentHttpMode` tests that currently fail because `RagPipeline.__init__` rejects a `use_search=True` config with these fields empty (REQ-001).

## Scope

In scope: `_make_cfg`'s `defaults` dict (lines ~17-37) in this file only. Out of scope: `scripts/rag/config_resolution.py`'s `resolve_rag_config`/`RagConfigValidator` and `scripts/rag/pipeline.py`'s `RagPipeline.__init__` — both confirmed already correct and intentional.

## Assumptions

- A placeholder non-empty URL string (e.g. `"http://llm.local"`/`"http://embed.local"`) is sufficient — none of the 5 failing tests' own assertions depend on the specific value of `llm_url`/`embed_url`.

## Design decisions

- Add both keys directly to `_make_cfg`'s `defaults` dict so every caller (all 5 `TestAugmentHttpMode` tests use `_make_cfg()` with no override for these fields) picks them up uniformly, rather than passing them as `**kwargs` overrides per call site.

## Alternatives considered

- Passing `llm_url`/`embed_url` explicitly at each of the 5 test call sites instead of adding them to the shared `defaults` dict: rejected — `_make_cfg`'s own design intent is to provide sensible defaults for all HTTP-mode fields; the other fields (`rag_service_url`, `use_mqe`, etc.) already follow this pattern, and these two omissions are the anomaly.

## Implementation

### Target file

`tests/agent/commands/test_agent_rag.py`

### Procedure

1. Re-confirm `_make_cfg`'s current `defaults` dict contents via Read (lines ~17-37) — confirm `llm_url`/`embed_url` are still absent (adversarial re-verification).
2. Add `"llm_url": "http://llm.local"` and `"embed_url": "http://embed.local"` to the `defaults` dict, in a position consistent with the dict's existing field grouping (e.g. near `"rag_service_url"`).

### Method

Direct dict-literal addition (2 new key-value pairs) — no structural or signature change to `_make_cfg`.

### Details

- Before: `defaults = {"use_search": True, "rag_service_url": "http://127.0.0.1:8010", "rag_auth_token": "", "use_mqe": True, ...}` (no `llm_url`/`embed_url` keys).
- After: `defaults = {"use_search": True, "rag_service_url": "http://127.0.0.1:8010", "llm_url": "http://llm.local", "embed_url": "http://embed.local", "rag_auth_token": "", "use_mqe": True, ...}`.
- `resolve_rag_config`'s validation (`scripts/rag/config_resolution.py:145-158`) requires `rag_db_path`/`llm_url`/`embed_url` non-empty when `use_search=True`; `rag_db_path` already defaults to `":memory:"` (non-empty) via `_DEFAULTS_FOR_ALL`, so only `llm_url`/`embed_url` need adding here.

## Compatibility considerations

- No production code changes; test-fixture fix supplying values a legitimately-required-when-enabled feature (HTTP-mode RAG augmentation) needs.

## Security considerations

N/A: test-only fixture values, not real credentials or endpoints.

## Rollback considerations

- `git revert` the commit, or manually remove the 2 added keys.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/agent/commands/test_agent_rag.py` | Unit | `uv run pytest tests/agent/commands/test_agent_rag.py -q` | All tests pass, including the 5 previously-failing `TestAugmentHttpMode` tests |

## Completion criteria

- `uv run pytest tests/agent/commands/test_agent_rag.py -q` passes with no failures.

## Out of scope

- `tests/rag/test_pipeline_http_result_kind.py`, `tests/rag/test_rag_http_mode.py`, `tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py` (each covered by its own implementation procedure document from this same Plan).
- `scripts/rag/config_resolution.py` and `scripts/rag/pipeline.py` (confirmed already correct).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Added llm_url/embed_url to _make_cfg defaults |
| 2 | Add or update tests per Validation plan | Completed | — | — | N/A: no new test needed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | All 7 tests pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | N/A: no docs/00_index.md task-scope mapping |

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
- **Requirement ID**: REQ-001: add `llm_url`/`embed_url` to `_make_cfg`'s defaults
- **Source issue**: issues/20260927-075240_rag001_rag-config-validation-rejects-fixtures-missing-llm_url-embed_url.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-082052_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-091513
- **Related target files**: tests/agent/commands/test_agent_rag.py
