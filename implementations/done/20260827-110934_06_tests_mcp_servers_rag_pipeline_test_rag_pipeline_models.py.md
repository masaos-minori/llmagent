## Goal

Add a guard test to `tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py`
pinning `RagPipelineConfig()`'s five previously-divergent defaults to the operational
TOML values (REQ-002, REQ-004, T-2), per `plans/20260826-115018_plan.md`.

## Scope

- In scope: one new test method (e.g. `test_defaults_match_operational_toml`) in
  `TestRagPipelineConfigFromDict`.
- Out of scope: `test_defaults_when_dict_empty` (line 19-21, asserts
  `RagPipelineConfig.from_dict({}) == RagPipelineConfig()` — an equality check
  between two defaults that both change together, unaffected by REQ-002 and not
  modified here); any other existing test in this file; any file-read-mcp test.

## Assumptions

- `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`'s `RagPipelineConfig`
  defaults have been (or are being, in this same pass, seq 04) aligned to
  `top_k_search=20`, `top_k_rerank=15`, `rag_min_score=2.0`,
  `semantic_cache_max_size=100`, `refiner_max_chars_per_chunk=300` — this new test's
  assertions depend on that change landing together.
- This file's own docstring (lines 3-6, verified 2026-08-27) already documents that
  `test_rag_pipeline_mcp_service.py` "only constructs `RagPipelineConfig` directly
  via its dataclass `__init__`, never through `from_dict`/`load`" — confirming that
  file's direct-construction pattern was already known at authorship time, which is
  why the seq 07 test item in this same pass (updating that file's
  `test_defaults_when_cfg_empty`) is necessary and was not an unforeseeable gap.

## Design decisions

- Add the guard test as a new method in the existing `TestRagPipelineConfigFromDict`
  class, matching this file's existing per-behavior test-method granularity, rather
  than a new test class.
- Assert against `RagPipelineConfig()` directly (not `.from_dict({})`) since the
  guard's purpose is pinning the dataclass-level default, which
  `test_defaults_when_dict_empty` already separately confirms equals
  `from_dict({})`'s result.
- Include an inline comment pointing at `config/rag_pipeline_mcp_server.toml` as the
  source of truth for these five values, per this Plan's own `T-2` specification.

## Alternatives considered

- N/A: this test's shape (assert five specific field values with a source-of-truth
  comment) is directly specified by this Plan's `T-2`; no alternative structure was
  considered.

## Implementation
### Target file
`tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py`

### Procedure
1. Add a new test method `test_defaults_match_operational_toml` to
   `TestRagPipelineConfigFromDict` asserting the five field values.
2. Run `uv run pytest tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py -v`.

### Method
Direct file edit (Edit tool) adding one test method; no changes to existing tests.

### Details
New test method body:
```python
def test_defaults_match_operational_toml(self) -> None:
    # Source of truth: config/rag_pipeline_mcp_server.toml's operational values.
    # A future edit to either side without the other must fail this test.
    cfg = RagPipelineConfig()
    assert cfg.top_k_search == 20
    assert cfg.top_k_rerank == 15
    assert cfg.rag_min_score == 2.0
    assert cfg.semantic_cache_max_size == 100
    assert cfg.refiner_max_chars_per_chunk == 300
```
Place it within `TestRagPipelineConfigFromDict`, adjacent to
`test_defaults_when_dict_empty`.

## Compatibility considerations

- Test-only change; no production code path is affected.
- Depends on seq 04 (`rag_pipeline_models.py`) landing in the same change.

## Security considerations

- N/A: test-only change, no security-relevant code path.

## Rollback considerations

- Single-method revert via `git diff`/`git checkout -- <path>`; must be reverted
  together with seq 04 (`rag_pipeline_models.py`) and seq 07
  (`test_rag_pipeline_mcp_service.py`) in this same pass.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py` | Unit | `uv run pytest tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py -v` | New test passes once seq 04 has also landed; existing tests unaffected |

## Completion criteria

- A test asserts `RagPipelineConfig()`'s five named fields equal `20`, `15`, `2.0`,
  `100`, `300` respectively, with an inline comment citing
  `config/rag_pipeline_mcp_server.toml` as the source of truth.

## Out of scope

- `test_defaults_when_dict_empty` and any other existing test in this file.
- `tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py` (separate target
  file, seq 07, in this same pass).
- Any file-read-mcp test.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `test_defaults_match_operational_toml` | Pending | — | — | |
| 2 | Run `uv run pytest tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py -v` | Pending | — | — | Requires seq 04 applied first |

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
- **Related target files**: `tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py`
