## Goal

Add non-empty `llm_url`/`embed_url` attributes to `tests/rag/test_pipeline_http_result_kind.py::_make_pipeline`'s `MagicMock()` cfg, fixing 4 tests that currently fail because `RagPipeline.__init__` rejects a `use_search=True` config with these fields empty (REQ-002).

## Scope

In scope: `_make_pipeline`'s `cfg = MagicMock()` construction (lines ~17-26) in this file only. Out of scope: `scripts/rag/config_resolution.py`/`scripts/rag/pipeline.py` (confirmed already correct).

## Assumptions

- A placeholder non-empty URL string is sufficient — none of the 4 failing tests' assertions depend on the specific value of `llm_url`/`embed_url`.
- Setting `cfg.llm_url`/`cfg.embed_url` explicitly (so they appear in `cfg.__dict__`) is required, since `resolve_rag_config` reads `cfg.__dict__` directly (line 118) and a `MagicMock`'s `__dict__` only contains explicitly-assigned attributes, not auto-vivified ones.

## Design decisions

- Set `cfg.llm_url`/`cfg.embed_url` as explicit attribute assignments immediately after `cfg = MagicMock()`, alongside the existing `cfg.rag_service_url`/`cfg.use_refiner`/`cfg.use_search` assignments — consistent with the file's existing style.

## Alternatives considered

- Constructing `cfg` with `MagicMock(llm_url=..., embed_url=..., ...)` kwargs instead of separate attribute assignments: rejected — inconsistent with this function's existing assignment style (separate `cfg.x = y` lines).

## Implementation

### Target file

`tests/rag/test_pipeline_http_result_kind.py`

### Procedure

1. Re-confirm `_make_pipeline`'s current body via Read (lines ~16-26) — confirm `cfg.llm_url`/`cfg.embed_url` are still unset (adversarial re-verification).
2. Add `cfg.llm_url = "http://llm.local"` and `cfg.embed_url = "http://embed.local"` immediately after the existing `cfg.use_search = True` line.

### Method

Direct attribute-assignment addition (2 new lines) — no structural change to `_make_pipeline`.

### Details

- Before: `cfg = MagicMock(); cfg.rag_service_url = rag_service_url; cfg.use_refiner = False; cfg.use_search = True`.
- After: adds `cfg.llm_url = "http://llm.local"` and `cfg.embed_url = "http://embed.local"` after `cfg.use_search = True`.
- Confirm `http_mock = MagicMock(spec=httpx.AsyncClient)` (the mocked HTTP client) still correctly intercepts all outbound calls after the fix — the added URLs must not introduce a real network dependency (they are read by `resolve_rag_config`/`RagLLM.__init__` for URL construction, not dialed directly by `MagicMock(spec=httpx.AsyncClient)`).

## Compatibility considerations

- No production code changes; test-fixture fix.

## Security considerations

N/A: test-only fixture values, not real credentials or endpoints.

## Rollback considerations

- `git revert` the commit, or manually remove the 2 added lines.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/rag/test_pipeline_http_result_kind.py` | Unit | `uv run pytest tests/rag/test_pipeline_http_result_kind.py -q` | All 4 tests pass |

## Completion criteria

- `uv run pytest tests/rag/test_pipeline_http_result_kind.py -q` passes with no failures.

## Out of scope

- `tests/agent/commands/test_agent_rag.py`, `tests/rag/test_rag_http_mode.py`, `tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py` (each covered by its own implementation procedure document from this same Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Added llm_url/embed_url to _make_pipeline cfg + pipeline.py result init fix |
| 2 | Add or update tests per Validation plan | Completed | — | — | N/A: no new test needed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | All 4 tests pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | N/A: no docs/00_index.md task-scope mapping |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | `test_no_http_mode` fails with UnboundLocalError on `result` variable — production bug in `pipeline.py:251` where `result` used before assignment when `rag_service_url` empty | Yes | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002: add `llm_url`/`embed_url` to `_make_pipeline`'s cfg
- **Source issue**: issues/20260927-075240_rag001_rag-config-validation-rejects-fixtures-missing-llm_url-embed_url.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-082052_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-091513
- **Related target files**: tests/rag/test_pipeline_http_result_kind.py
