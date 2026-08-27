## Goal

Update `tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py`'s
`TestBuildRagCfgAdapter::test_defaults_when_cfg_empty` to assert the new
`RagPipelineConfig` defaults (REQ-002, REQ-004, T-3 — added by this
plan-to-implementation-procedure's own adversarial verification, 2026-08-27), per
`plans/20260826-115018_plan.md`.

## Scope

- In scope: `TestBuildRagCfgAdapter::test_defaults_when_cfg_empty` (verified at
  lines 29-46 as of 2026-08-27) only.
- Out of scope: every other test in this file that already passes explicit values
  for the five REQ-002 fields (`test_overrides_from_cfg`,
  `test_adapter_satisfies_rag_config_protocol`, and others — verified 2026-08-27 via
  `rg -n "refiner_max_chars_per_chunk\|top_k_search\|top_k_rerank\|rag_min_score\|semantic_cache_max_size"
  tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py`, confirming all
  other hits already pass explicit values and are unaffected by the default change);
  any file-read-mcp test.

## Assumptions

- `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`'s `RagPipelineConfig`
  defaults have been (or are being, in this same pass, seq 04) aligned to
  `top_k_search=20`, `top_k_rerank=15`, `rag_min_score=2.0`,
  `semantic_cache_max_size=100`, `refiner_max_chars_per_chunk=300` — this test's
  updated assertions depend on that change landing together.

## Design decisions

- This item exists because this Plan's own Risk-mitigation claim ("every test file
  that constructs RAG config objects directly ... passes explicit values") was
  found false against this specific file during this procedure's own adversarial
  verification of the Plan (2026-08-27) — see `plans/20260826-115018_plan.md`'s
  corrected Risk section and added `T-3`. This is a Plan-identified fix, not a
  scope addition beyond the Plan's own (corrected) Implementation steps.
- Update only the five hardcoded assertion values in `test_defaults_when_cfg_empty`
  — do not touch the test's `RagPipelineConfig()` no-argument construction itself,
  since exercising the true default (not an explicit override) is the entire point
  of this test.

## Alternatives considered

- Changing the test to construct `RagPipelineConfig` with explicit values instead of
  relying on defaults was considered and rejected — it would defeat the test's own
  purpose (`test_defaults_when_cfg_empty` specifically verifies
  `build_rag_cfg_adapter`'s behavior when `RagPipelineConfig` is default-constructed
  ["cfg empty"]); updating the expected values to match the new defaults preserves
  that intent.

## Implementation
### Target file
`tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py`

### Procedure
1. In `test_defaults_when_cfg_empty` (verified at lines 29-46 as of 2026-08-27),
   update the five hardcoded assertion values to the new defaults.
2. Run `uv run pytest tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py -v`.

### Method
Direct test-file edit (Edit tool) — five assertion value changes; no changes to the
test's setup/construction line.

### Details
Current code (verified 2026-08-27, lines 29-46):
```python
    def test_defaults_when_cfg_empty(self) -> None:
        cfg = RagPipelineConfig()
        ns = build_rag_cfg_adapter(cfg)
        assert ns.use_mqe is True
        assert ns.use_rrf is True
        assert ns.use_rerank is True
        assert ns.use_refiner is False
        assert ns.refiner_max_tokens == 512
        assert ns.refiner_max_chars_per_chunk == 800
        assert ns.refiner_timeout == 30.0
```
(Full method also includes `ns.top_k_search`/`ns.top_k_rerank`/`ns.rag_min_score`/
`ns.semantic_cache_max_size` assertions per this procedure's own verification —
confirm the exact current line ordering/content before editing, since only a
partial excerpt was captured during this Plan's evidence-gathering; re-read the full
method body first.) Update the five REQ-002-affected assertions to:
```python
        assert ns.top_k_search == 20
        assert ns.top_k_rerank == 15
        assert ns.rag_min_score == 2.0
        assert ns.semantic_cache_max_size == 100
        assert ns.refiner_max_chars_per_chunk == 300
```
Leave `ns.use_mqe`/`ns.use_rrf`/`ns.use_rerank`/`ns.use_refiner`/
`ns.refiner_max_tokens`/`ns.refiner_timeout` and any other non-REQ-002 assertion in
this test unchanged — only the five fields this Plan's REQ-002 modifies are
affected.

## Compatibility considerations

- Test-only change; no production code path is affected.
- Depends on seq 04 (`rag_pipeline_models.py`) landing in the same change — without
  it, this test's updated assertions fail against the still-old defaults.

## Security considerations

- N/A: test-only change, no security-relevant code path.

## Rollback considerations

- Five-assertion revert via `git diff`/`git checkout -- <path>`; must be reverted
  together with seq 04 (`rag_pipeline_models.py`) in this same pass.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py` | Unit | `uv run pytest tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py -v` | `test_defaults_when_cfg_empty` passes once seq 04 has also landed; all other tests in this file remain unaffected (already pass explicit values) |

## Completion criteria

- `test_defaults_when_cfg_empty` asserts `ns.top_k_search == 20`,
  `ns.top_k_rerank == 15`, `ns.rag_min_score == 2.0`,
  `ns.semantic_cache_max_size == 100`, `ns.refiner_max_chars_per_chunk == 300`.
- No other test in this file needs modification (confirmed by this procedure's own
  `rg` sweep, see Scope above).

## Out of scope

- Every other test in this file (already unaffected, confirmed by `rg` sweep).
- Any file-read-mcp test.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update `test_defaults_when_cfg_empty`'s 5 assertion values | Pending | — | — | |
| 2 | Run `uv run pytest tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py -v` | Pending | — | — | Requires seq 04 applied first |

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
- **Requirement ID**: REQ-002, REQ-004
- **Source issue**: `issues/20260821_05_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260826-115018_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260827-110934
- **Related target files**: `tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py`
