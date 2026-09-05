## Goal
Create `tests/mcp_servers/rag_pipeline/test_removed_config_keys_rejected.py`: a new
regression test proving the RAG MCP configuration-loading path
(`RagPipelineConfig.load()`) rejects each of the three removed keys
(`use_semantic_cache`, `semantic_cache_threshold`, `semantic_cache_max_size`) with the
`REQ-003` migration error, individually and in combination (`REQ-009`).

## Scope
- **In-Scope**: create one new test file mocking `ConfigLoader.load` (matching
  `tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py`'s own
  `TestRagPipelineConfigLoad` pattern, procedure document `32`'s Out-of-Scope
  reference) to return a raw dict containing one or more of the three removed keys,
  asserting `RagPipelineConfig.load()` raises `ValueError` naming the offending
  key(s).
- **Out-of-Scope**: exercising `build_agent_config()`'s equivalent rejection path (a
  separate new file, `tests/agent/test_removed_config_keys_rejected.py`, procedure
  document `43`); re-testing `RagPipelineConfig.from_dict()`'s other, already-covered
  behavior (procedure document `32`'s updates already cover the non-rejection paths).

## Assumptions
- `RagPipelineConfig.load()` (procedure document `06`) raises `ValueError`
  synchronously inside `load()` itself, before `from_dict()` is called — confirmed by
  that document's planned implementation (`raw_cfg = ConfigLoader().load(...)`;
  validate; raise on `not validation_result.ok`; only then `return
  cls.from_dict(raw_cfg)`).
- `monkeypatch.setattr(ConfigLoader, "load", fake_load)` (the same technique
  `tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py`'s
  `TestRagPipelineConfigLoad` already uses, confirmed by reading that class) is the
  correct way to inject a raw dict containing a removed key without needing an actual
  TOML file on disk.

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §7/§10, narrow bullets only)
- Reuse the exact `monkeypatch.setattr(ConfigLoader, "load", fake_load)` technique
  already established in `tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py`
  (procedure document `32`'s Out-of-Scope reference) for consistency, rather than
  inventing a new mocking approach for this sibling test file.
- Write four test methods mirroring procedure document `43`'s structure at the RAG
  MCP layer: three individually-removed-key tests plus one three-keys-combined test —
  parallel structure across both new "rejected" test files aids readability and
  future maintenance.
- Assert via `pytest.raises(ValueError, match=...)` using a substring match on the
  removed key's name, consistent with procedure documents `42`/`43`'s
  substring-assertion design choice.

## Alternatives considered
- Testing against a real temporary TOML file (via `tmp_path`) instead of mocking
  `ConfigLoader.load` — rejected: the sibling test class in
  `test_rag_pipeline_models.py` already established the mocking pattern for this exact
  `load()` method; using a different technique in a new, closely-related test file
  would introduce unnecessary inconsistency for no added coverage.

## Implementation
### Target file
`tests/mcp_servers/rag_pipeline/test_removed_config_keys_rejected.py` (new file)

### Procedure
1. Create the file with a module docstring stating its purpose (regression coverage
   for `REQ-009`/`AC-7`: the RAG MCP config-loading path rejects removed
   SemanticCache-related keys).
2. Import `RagPipelineConfig` from `mcp_servers.rag_pipeline.rag_pipeline_models` and
   `ConfigLoader` from `shared.config_loader`, matching
   `tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py`'s own imports.
3. Write `test_use_semantic_cache_rejected`: monkeypatch `ConfigLoader.load` to return
   `{"llm_url": "http://x", "use_semantic_cache": True}`; call
   `RagPipelineConfig.load()` inside `pytest.raises(ValueError,
   match="use_semantic_cache")`.
4. Write `test_semantic_cache_threshold_rejected`: same pattern with
   `{"llm_url": "http://x", "semantic_cache_threshold": 0.5}`,
   `match="semantic_cache_threshold"`.
5. Write `test_semantic_cache_max_size_rejected`: same pattern with
   `{"llm_url": "http://x", "semantic_cache_max_size": 50}`,
   `match="semantic_cache_max_size"`.
6. Write `test_all_three_removed_keys_rejected`: merge all three keys into the fake
   payload at once; assert `ValueError` is raised (per procedure document `05`'s
   Assumptions on combined vs. per-key messages, do not over-assert exact
   count/structure here — that is procedure document `42`'s responsibility at the
   `RagConfigValidator` unit level).

### Method
New test file, written directly, mirroring
`tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py`'s
`TestRagPipelineConfigLoad`'s existing `monkeypatch`-based `ConfigLoader.load` mocking
convention.

### Details
- Each fake payload includes a minimal, unrelated key (`"llm_url": "http://x"`)
  alongside the removed key(s) under test — purely for readability, matching the
  sibling test class's style; not strictly required, since `RagPipelineConfig.load()`'s
  validation runs against the raw dict regardless of which other keys are present.
- Do not import anything from `scripts/rag/cache.py` (deleted, `semcacherm` procedure
  document `02`) — this file tests configuration rejection only.

## Compatibility considerations
N/A: new test file; no existing caller is affected by its creation.

## Security considerations
N/A: no security-sensitive code path is touched.

## Rollback considerations
- Revert by deleting this newly-created file; no other file depends on it existing.

## Validation plan
- `uv run pytest tests/mcp_servers/rag_pipeline/test_removed_config_keys_rejected.py -v`
  — all four new tests pass against the fully-implemented Plan (procedure documents
  `06`/`05` landed).
- Confirm each test fails if procedure document `06`'s validator wiring is reverted
  (per the Plan's Testing Expectations instruction, same verification approach as
  procedure document `43`).

## Completion criteria
- `tests/mcp_servers/rag_pipeline/test_removed_config_keys_rejected.py` exists and
  contains four passing tests, each proving `RagPipelineConfig.load()` raises
  `ValueError` for a removed key (individually and in combination) (Plan `AC-7`).

## Out of scope
- `build_agent_config()`'s equivalent rejection path (separate new file, procedure
  document `43`).
- Any change to production code (this document creates a test file only).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Blocked until procedure documents `05`/`06` land — see Assumptions |
| 2 | Add or update tests per Validation plan | Pending | — | — | This document's Implementation IS the new test |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Depends on procedure documents `05` (`RagConfigValidator`'s new check) and `06` (`RagPipelineConfig.load()`'s validator wiring) landing first | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-009` (add regression coverage proving the RAG MCP config-loading path rejects removed keys)
- **Source issue**: issues/20260902-150340_semcacheconfig_remove_semanticcache_settings_from_config_contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-141001_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-185605
- **Related target files**: tests/mcp_servers/rag_pipeline/test_removed_config_keys_rejected.py
