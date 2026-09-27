## Goal

Add non-empty `llm_url`/`embed_url` attributes to `tests/rag/test_rag_http_mode.py`'s cfg construction, fixing 4 tests that currently fail because `RagPipeline.__init__` rejects a `use_search=True` config with these fields empty (REQ-003).

## Scope

In scope: the `MagicMock()`-based cfg construction (around line 24) in this file only. Out of scope: `scripts/rag/config_resolution.py`/`scripts/rag/pipeline.py` (confirmed already correct).

## Assumptions

- A placeholder non-empty URL string is sufficient — none of the 4 failing tests' assertions depend on the specific value of `llm_url`/`embed_url`.

## Design decisions

- Set `cfg.llm_url`/`cfg.embed_url` as explicit attribute assignments alongside the existing `cfg.use_search = True` line, matching this file's own construction style (confirmed via Read to mirror `test_pipeline_http_result_kind.py`'s sibling pattern).

## Alternatives considered

- N/A: same reasoning as the sibling `test_pipeline_http_result_kind.py` implementation procedure — no alternative approach considered given the identical, confirmed root cause.

## Implementation

### Target file

`tests/rag/test_rag_http_mode.py`

### Procedure

1. Re-confirm the cfg construction's current form via Read (lines ~1-30) — confirm `cfg.llm_url`/`cfg.embed_url` are still unset (adversarial re-verification).
2. Add `cfg.llm_url = "http://llm.local"` and `cfg.embed_url = "http://embed.local"` immediately after the existing `cfg.use_search = True` line (line ~24).

### Method

Direct attribute-assignment addition (2 new lines) — no structural change.

### Details

- Before: `cfg.use_search = True` with no `llm_url`/`embed_url` set.
- After: adds `cfg.llm_url = "http://llm.local"` and `cfg.embed_url = "http://embed.local"` immediately after.

## Compatibility considerations

- No production code changes; test-fixture fix.

## Security considerations

N/A: test-only fixture values, not real credentials or endpoints.

## Rollback considerations

- `git revert` the commit, or manually remove the 2 added lines.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/rag/test_rag_http_mode.py` | Unit | `uv run pytest tests/rag/test_rag_http_mode.py -q` | All 4 tests pass |

## Completion criteria

- `uv run pytest tests/rag/test_rag_http_mode.py -q` passes with no failures.

## Out of scope

- `tests/agent/commands/test_agent_rag.py`, `tests/rag/test_pipeline_http_result_kind.py`, `tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py` (each covered by its own implementation procedure document from this same Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Added llm_url/embed_url to _make_pipeline cfg |
| 2 | Add or update tests per Validation plan | Completed | — | — | N/A: no new test needed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | All 4 tests pass |
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
- **Requirement ID**: REQ-003: add `llm_url`/`embed_url` to `test_rag_http_mode.py`'s cfg
- **Source issue**: issues/20260927-075240_rag001_rag-config-validation-rejects-fixtures-missing-llm_url-embed_url.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-082052_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-091513
- **Related target files**: tests/rag/test_rag_http_mode.py
