## Goal
Create `tests/agent/test_removed_config_keys_rejected.py`: a new regression test
proving the Agent configuration-loading path (`build_agent_config()` →
`_build_rag_config()`) rejects each of the three removed keys
(`use_semantic_cache`, `semantic_cache_threshold`, `semantic_cache_max_size`) with the
`REQ-003` migration error, individually and in combination (`REQ-009`).

## Scope
- **In-Scope**: create one new test file with a minimal test class exercising
  `build_agent_config(cfg_override)` (procedure document `04`'s new
  `RagConfigValidator().validate()` call inside `_build_rag_config()`) against a
  config dict containing one or more of the three removed keys, asserting `ValueError`
  is raised with a message naming the offending key(s).
- **Out-of-Scope**: exercising `RagPipelineConfig.load()`'s equivalent rejection path
  (a separate new file, `tests/mcp_servers/rag_pipeline/test_removed_config_keys_rejected.py`,
  its own procedure document); re-testing `_build_rag_config()`'s other,
  already-covered behavior (procedure document `16`'s `tests/agent/test_config_builders.py`
  updates already cover the non-rejection paths).

## Assumptions
- `build_agent_config(cfg_override)` (procedure document `04`) raises `ValueError`
  synchronously during `_build_rag_config(cfg)`'s call, before `AgentConfig(...)` is
  constructed — confirmed by reading `scripts/rag/pipeline.py`'s existing identical
  pattern (Plan Reference Files) and procedure document `04`'s planned
  implementation (raise inside `_build_rag_config()` itself, called from
  `build_agent_config()`'s `rag=_build_rag_config(cfg)` argument).
- A minimal config dict satisfying `build_agent_config()`'s other cross-field
  requirements (at least one HTTP `mcp_servers` entry with a `url`; non-empty
  `embed_url`, since `AgentConfig.__post_init__`'s memory-embed cross-field check
  defaults to requiring it) is needed alongside the removed key(s) under test — this
  document defines its own minimal fixture rather than importing
  `tests/agent/test_config_builders.py`'s private `_MIN_CFG` (module-private,
  leading-underscore convention discourages cross-file import; this file defines an
  equivalent local constant instead).

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §7/§10, narrow bullets only)
- Follow `tests/agent/test_config_builders.py`'s existing `_MIN_CFG`-style minimal
  fixture pattern for consistency, defining a local, equivalently-shaped constant in
  this new file rather than reaching across files for a private constant.
- Write three test methods: one per individually-removed key
  (`use_semantic_cache`, `semantic_cache_threshold`, `semantic_cache_max_size`), plus
  one combination test (all three present together) — mirroring
  `tests/shared/test_config_validator.py`'s own test structure (procedure document
  `42`) at the integration level (through `build_agent_config()`, not directly against
  `RagConfigValidator`).
- Assert on `pytest.raises(ValueError, match=...)` using a substring match on the
  removed key's name (e.g. `match="use_semantic_cache"`), not the full migration
  message text — consistent with procedure document `42`'s substring-assertion design
  choice, since the exact message wording is procedure document `05`'s implementation
  detail.

## Alternatives considered
- Testing only the three-keys-combined case, omitting individual-key tests —
  rejected: the originating issue's Testing Expectations explicitly ask to "assert
  each of the three keys, individually and together, produces the REQ-003 migration
  error via the Agent and RAG MCP loading paths respectively."

## Implementation
### Target file
`tests/agent/test_removed_config_keys_rejected.py` (new file)

### Procedure
1. Create the file with a module docstring stating its purpose (regression coverage
   for `REQ-009`/`AC-7`: the Agent config-loading path rejects removed
   SemanticCache-related keys).
2. Define a local minimal config constant equivalent in shape to
   `tests/agent/test_config_builders.py`'s `_MIN_CFG` (an `mcp_servers` entry with an
   HTTP transport/url/auth_token, and a non-empty `embed_url`).
3. Write `test_use_semantic_cache_rejected`: merge `{"use_semantic_cache": True}` into
   the minimal config; call `build_agent_config(merged_cfg)` inside
   `pytest.raises(ValueError, match="use_semantic_cache")`.
4. Write `test_semantic_cache_threshold_rejected`: same pattern with
   `{"semantic_cache_threshold": 0.5}`, `match="semantic_cache_threshold"`.
5. Write `test_semantic_cache_max_size_rejected`: same pattern with
   `{"semantic_cache_max_size": 50}`, `match="semantic_cache_max_size"`.
6. Write `test_all_three_removed_keys_rejected`: merge all three keys at once; assert
   `ValueError` is raised (per procedure document `05`'s Assumptions on combined vs.
   per-key error messages, do not over-assert the exact count/structure of key names
   in the message here — the message-content coverage is procedure document `42`'s
   responsibility at the `RagConfigValidator` unit level; this integration test only
   confirms the end-to-end path raises).

### Method
New test file, written directly, following `tests/agent/test_config_builders.py`'s
`_MIN_CFG`-style fixture convention.

### Details
- Import `build_agent_config` from `agent.config_builders` (matching this codebase's
  existing import convention, confirmed by
  `tests/agent/test_config_builders.py`'s own import).
- Merge the removed key(s) into the minimal config via dict unpacking (`{**_MIN_CFG_EQUIVALENT,
  "use_semantic_cache": True}`) rather than mutating a shared module-level dict
  in place, to keep each test's fixture independent.
- Do not import anything from `scripts/rag/cache.py` (deleted, `semcacherm` procedure
  document `02`) or reference `SemanticCache`/`invalidate_cache` — this file tests
  configuration rejection only, not the removed runtime cache itself.

## Compatibility considerations
N/A: new test file; no existing caller is affected by its creation.

## Security considerations
N/A: no security-sensitive code path is touched.

## Rollback considerations
- Revert by deleting this newly-created file; no other file depends on it existing.

## Validation plan
- `uv run pytest tests/agent/test_removed_config_keys_rejected.py -v` — all four new
  tests pass against the fully-implemented Plan (procedure documents `01`-`10` landed).
- Confirm each test fails if procedure document `04`'s validator wiring is reverted
  (manually verify by temporarily reverting that document in a scratch branch, or by
  code review confirming the assertion genuinely depends on the new
  `RagConfigValidator().validate()` call) — per the Plan's Testing Expectations
  instruction ("Confirm each replacement regression test fails against the pre-change
  code and passes afterward").

## Completion criteria
- `tests/agent/test_removed_config_keys_rejected.py` exists and contains four passing
  tests, each proving `build_agent_config()` raises `ValueError` for a removed key
  (individually and in combination) (Plan `AC-7`).

## Out of scope
- `RagPipelineConfig.load()`'s equivalent rejection path (separate new file, its own
  procedure document).
- Any change to production code (this document creates a test file only).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Blocked until procedure documents `03`/`04`/`05` land — see Assumptions |
| 2 | Add or update tests per Validation plan | Pending | — | — | This document's Implementation IS the new test |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Depends on procedure documents `03` (`RAGConfig`), `04` (`_build_rag_config()` validator wiring), and `05` (`RagConfigValidator`'s new check) landing first | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-009` (add regression coverage proving the Agent config-loading path rejects removed keys)
- **Source issue**: issues/20260902-150340_semcacheconfig_remove_semanticcache_settings_from_config_contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-141001_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-185605
- **Related target files**: tests/agent/test_removed_config_keys_rejected.py
