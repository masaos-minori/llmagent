## Goal
Update `tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py`'s
`TestRagPipelineConfigFromDict` assertions to remove the three removed
`RagPipelineConfig` fields, made obsolete by procedure document `06` (`REQ-004`,
`REQ-009`).

## Scope
- **In-Scope**:
  - `test_defaults_match_operational_toml`: remove `assert
    cfg.semantic_cache_max_size == 100` (line 30).
  - `test_custom_values_are_mapped`: remove `"semantic_cache_max_size": 64,`,
    `"semantic_cache_threshold": 0.8,`, `"use_semantic_cache": True,` (lines 54-56)
    from the `raw` dict; remove `assert cfg.semantic_cache_max_size == 64`,
    `assert cfg.semantic_cache_threshold == 0.8`,
    `assert cfg.use_semantic_cache is True` (lines 82-84).
- **Out-of-Scope**: `test_defaults_when_dict_empty`, `test_numeric_string_values_are_coerced`,
  `test_falsy_present_values_are_not_treated_as_missing`,
  `test_unknown_keys_are_ignored`, and `class TestRagPipelineConfigLoad`'s two tests
  (`test_load_delegates_to_config_loader_with_expected_filename`,
  `test_load_propagates_config_loader_errors`) — confirmed unaffected by reading each:
  none references any of the three removed keys, and the two `load()` tests mock
  `ConfigLoader.load` directly (not `RagConfigValidator`), so procedure document `06`'s
  new validator call inside `load()` does not change their behavior (an empty or
  cache-key-free fake payload passes validation with no error/warning either way).

## Assumptions
- `RagPipelineConfig` (procedure document `06`) no longer has the three removed
  fields — `test_custom_values_are_mapped`'s `RagPipelineConfig.from_dict(raw)` call
  would otherwise silently produce a `RagPipelineConfig` instance without the three
  attributes read by the removed assertions, causing `AttributeError` at assertion
  time if those assertions were left in place.
- The two `TestRagPipelineConfigLoad` tests do not need a new test proving the
  `REQ-003` migration-error behavior — that is `tests/mcp_servers/rag_pipeline/test_removed_config_keys_rejected.py`'s
  (a separate, new procedure document's) responsibility, per this Plan's own Testing
  Expectations naming that file specifically for the rejection-path regression test.

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §7, narrow bullet only)
- Remove the two locations' cache-related lines only — every other field/assertion in
  both affected tests remains, since `test_defaults_match_operational_toml`'s and
  `test_custom_values_are_mapped`'s broader purpose (matching TOML defaults; mapping
  every other custom value) is unaffected by this Plan.

## Alternatives considered
N/A: straightforward removal of now-invalid assertions/fixture keys with no
replacement subject.

## Implementation
### Target file
`tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py`

### Procedure
1. In `test_defaults_match_operational_toml`, remove
   `assert cfg.semantic_cache_max_size == 100` (line 30).
2. In `test_custom_values_are_mapped`, remove the three `raw` dict entries
   (`"semantic_cache_max_size": 64,`, `"semantic_cache_threshold": 0.8,`,
   `"use_semantic_cache": True,`, lines 54-56) and the three corresponding assertions
   (`assert cfg.semantic_cache_max_size == 64`, `assert cfg.semantic_cache_threshold
   == 0.8`, `assert cfg.use_semantic_cache is True`, lines 82-84).

### Method
Direct `Edit` across two locations in the same test class.

### Details
- Confirm `test_defaults_match_operational_toml`'s comment ("Source of truth:
  `config/rag_pipeline_mcp_server.toml`'s operational values") remains accurate after
  removing the cache assertion — the remaining assertions
  (`top_k_search`, `top_k_rerank`, `rag_min_score`, `refiner_max_chars_per_chunk`)
  still correspond to values in that TOML file per procedure document `10`'s edit.
- Confirm after editing: `rg -n "semantic_cache"
  tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py` returns zero matches.

## Compatibility considerations
N/A: test-only file; no production caller depends on it.

## Security considerations
N/A: no security-sensitive code path is touched.

## Rollback considerations
- Revert via `git checkout` on this single file; must be reverted together with
  procedure document `06` (`RagPipelineConfig`).

## Validation plan
- `uv run pytest tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py -v` — all
  tests pass, including the two unaffected `TestRagPipelineConfigLoad` tests.
- `rg -n "semantic_cache" tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py`
  — zero matches.

## Completion criteria
- No reference to any of the three removed keys remains in this file (Plan `AC-1`,
  `AC-3`, `AC-8`).
- All tests in this file pass against the modified `RagPipelineConfig`.

## Out of scope
- `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py` (procedure document `06`).
- `tests/mcp_servers/rag_pipeline/test_removed_config_keys_rejected.py` (new,
  separate procedure document proving the `AC-7` rejection path).
- `class TestRagPipelineConfigLoad`'s existing two tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | New rejection-path test is a separate procedure document |
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
- **Requirement ID**: `REQ-004` (assert `RagPipelineConfig`/`from_dict()` no longer carry the three fields)
- **Source issue**: issues/20260902-150340_semcacheconfig_remove_semanticcache_settings_from_config_contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-141001_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-185605
- **Related target files**: tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py
