## Goal
Replace the `semantic_cache_threshold` TOML fixture key and its assertion in
`tests/shared/test_config_hot_reload.py`'s
`test_reload_loads_agent_toml_content` with a still-valid, generic placeholder key,
since it is used only as an example flat key — not to exercise RAG-specific behavior
(`REQ-006`, `REQ-009`).

## Scope
- **In-Scope**: replace `"tool_cache_ttl = 300\nsemantic_cache_threshold = 0.9\n"`
  (line 21) with `"tool_cache_ttl = 300\nsome_flat_setting = 0.9\n"`; replace
  `assert cfg.get("semantic_cache_threshold") == 0.9` (line 27) with
  `assert cfg.get("some_flat_setting") == 0.9`.
- **Out-of-Scope**: `tool_cache_ttl` (the other example key in the same TOML fixture)
  and every other test in this file (`test_reload_loads_mcp_servers_section`, etc.) —
  confirmed unrelated by reading the surrounding context.

## Assumptions
- `test_reload_loads_agent_toml_content`'s purpose is testing `ConfigLoader.load_all()`'s
  generic flat-key-loading behavior, not any RAG-specific semantics — confirmed by its
  own docstring ("`load_all()` loads `agent.toml` and makes all flat keys accessible")
  and by this Plan's Design section finding that `ConfigLoader` performs no per-key
  schema validation (it is a bare TOML/JSON-to-dict merge). Using
  `semantic_cache_threshold` as the example key was incidental, not load-bearing for
  the test's actual assertion.

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §7, narrow bullet only)
- Substitute (not delete) the fixture key, since the test needs *some* second flat key
  alongside `tool_cache_ttl` to prove `load_all()` exposes more than one arbitrary
  key — deleting it entirely would narrow the test's coverage (single-key vs.
  multi-key flat loading) for no reason.
- Use a clearly generic placeholder name (`some_flat_setting`) rather than
  substituting another real, currently-meaningful config key — avoids implying this
  test verifies anything specific about that other key's semantics, keeping the test's
  intent (arbitrary flat-key passthrough) unambiguous.

## Alternatives considered
- Substituting a real, still-active config key (e.g. `llm_temperature`) instead of a
  placeholder — rejected: could mislead a future reader into thinking this test
  verifies `llm_temperature`-specific reload behavior, when its actual purpose is
  generic flat-key passthrough.

## Implementation
### Target file
`tests/shared/test_config_hot_reload.py`

### Procedure
1. Replace `"tool_cache_ttl = 300\nsemantic_cache_threshold = 0.9\n"` (line 21) with
   `"tool_cache_ttl = 300\nsome_flat_setting = 0.9\n"`.
2. Replace `assert cfg.get("semantic_cache_threshold") == 0.9` (line 27) with
   `assert cfg.get("some_flat_setting") == 0.9`.

### Method
Direct `Edit`: two string substitutions (TOML content literal, assertion key).

### Details
- Confirm after editing: `rg -n "semantic_cache"
  tests/shared/test_config_hot_reload.py` returns zero matches.
- Confirm the test's docstring ("`load_all()` loads `agent.toml` and makes all flat
  keys accessible") remains accurate — unchanged by this substitution.

## Compatibility considerations
N/A: test-only file; `ConfigLoader.load_all()` itself is untouched by this document.

## Security considerations
N/A.

## Rollback considerations
- Revert via `git checkout` on this single file; independent of every other procedure
  document (this test never depended on `RagConfigValidator`/`RagConfigImpl`/
  `RAGConfig`).

## Validation plan
- `uv run pytest tests/shared/test_config_hot_reload.py -v` — all tests pass,
  including the substituted assertion.
- `rg -n "semantic_cache" tests/shared/test_config_hot_reload.py` — zero matches.

## Completion criteria
- No reference to `semantic_cache_threshold` remains in this file (Plan `AC-6`,
  `AC-8`).
- `test_reload_loads_agent_toml_content` continues verifying multi-key flat-loading
  behavior via the substituted key.

## Out of scope
- `tool_cache_ttl` and every other test in this file.
- `scripts/shared/config_loader.py`'s `ConfigLoader` itself (untouched by this Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Substitution is part of this document's own scope |
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
- **Requirement ID**: `REQ-006` (remove cache references from configuration reload paths' tests)
- **Source issue**: issues/20260902-150340_semcacheconfig_remove_semanticcache_settings_from_config_contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-141001_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-185605
- **Related target files**: tests/shared/test_config_hot_reload.py
