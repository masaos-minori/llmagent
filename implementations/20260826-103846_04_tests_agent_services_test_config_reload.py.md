## Goal

Add regression tests proving that `/reload` now rejects out-of-range `llm`/`rag`/
`tool` field values via `ConfigReloadValidationError` (leaving `ctx.cfg` unchanged),
while valid multi-field reloads still apply correctly, covering the behavior added by
the sibling document
`implementations/20260826-103846_01_scripts_agent_services_config_reload.py.md`
(REQ-005).

## Scope

- In scope: `tests/agent/services/test_config_reload.py` — extend `TestApplyConfig`
  (or add a new test class in the same file) with the 3 regression cases required by
  AC-01, AC-02, AC-03.
- Out of scope: `tests/agent/services/test_config_reload_classification.py` (covers
  unrelated MCP server-change classification, not llm/rag/tool field validation — no
  change needed there); any change to `config_validators.py` test coverage (unrelated
  to this plan, see `plans/20260825-142749_plan.md` cross-reference in the sibling
  code-change document).

## Assumptions

- The code change in
  `implementations/20260826-103846_01_scripts_agent_services_config_reload.py.md`
  lands first (or is implemented together) — these tests exercise the new
  `dataclasses.replace()`-based rejection path and will fail against the pre-change
  `setattr`-based code (which silently accepts out-of-range values).
- The existing `svc()` fixture (`tests/agent/services/test_config_reload.py:13-39`)
  builds `ctx` as a bare `MagicMock()` with individual scalar attributes stubbed on
  `ctx.cfg.llm`/`ctx.cfg.tool` (e.g. `ctx.cfg.llm.llm_temperature = 0.7`) — `ctx.cfg.llm`
  itself is a `MagicMock`, not a real `LLMConfig` instance. `dataclasses.replace()`
  requires a real dataclass instance (calling it on a `MagicMock` raises `TypeError`,
  not the `ValueError`/`ConfigReloadValidationError` these tests need to assert), so
  the new tests need `ctx.cfg.llm`/`ctx.cfg.rag`/`ctx.cfg.tool` set to real
  `LLMConfig()`/`RAGConfig()`/`ToolConfig()` instances while `ctx` itself stays a
  `MagicMock`. This exact pattern already exists elsewhere in the test suite —
  `tests/agent/commands/test_cmd_config_char.py:30`:
  `ctx.cfg.llm = overrides.get("llm", LLMConfig())` — confirming this is a supported,
  precedented style, not a new invention.

## Design decisions

- Add a dedicated fixture (e.g. `svc_real_cfg()`) alongside the existing `svc()`
  fixture rather than modifying `svc()` in place — `svc()` is used by
  `TestApplyConfig`'s existing type-validation tests
  (`test_invalid_masked_fields_type_raises`, etc.) which only exercise
  `apply_config()`'s masked_fields type check (never reaching `apply_config_dict()`'s
  real per-field logic) and patch `apply_config_dict()` out entirely in 2 of the 3
  cases; changing `svc()`'s `ctx.cfg.llm` to a real `LLMConfig()` is unnecessary churn
  for those tests and risks breaking their `MagicMock`-attribute-based assertions if
  any exist.
- Assert both the raised exception type (`ConfigReloadValidationError`) and that the
  rejected field's value on `ctx.cfg.<sub>` is unchanged after the raise (AC-01) —
  asserting only the exception type would not catch a bug where `ctx.cfg.<sub>` was
  already reassigned before the validator ran.
- Cover one llm field (`llm_temperature`, matching AC-01's example), and one
  multi-field-success case spanning llm+tool+rag in a single request (AC-03), reusing
  fields already present in the existing `svc` fixtures' vocabulary
  (`llm_temperature`, `tool_cache_ttl`/`serial_tool_calls`,
  `semantic_cache_threshold`/`use_semantic_cache`) to keep the new tests readable
  against the existing file's style.

## Alternatives considered

- Patch `dataclasses.replace` to raise, instead of using a real out-of-range value:
  rejected — an integration-style test using a real validator-rejected value (e.g.
  `llm_temperature=5.0`, which exceeds `LLM_TEMPERATURE_MAX = 2.0` in
  `config_dataclasses.py:109`) exercises the real `LLMConfig.__post_init__` path
  end-to-end and is less brittle to refactors than mocking `dataclasses.replace`
  itself.
- Reuse the existing `MagicMock`-based `svc()` fixture by making `ctx.cfg.llm` a
  `MagicMock(spec=LLMConfig)`: rejected — `dataclasses.replace()` inspects
  `dataclasses.fields(obj)` and calls `obj.__class__(**kwargs)`, which a `spec`'d
  `MagicMock` does not satisfy; a real instance is simplest and matches the existing
  `test_cmd_config_char.py` precedent.

## Implementation

### Target file
`tests/agent/services/test_config_reload.py`

### Procedure
1. Add `from agent.config_dataclasses import LLMConfig, RAGConfig, ToolConfig` to the
   test file's imports.
2. Add a new fixture that builds `ctx = MagicMock()` with `ctx.cfg.llm = LLMConfig()`,
   `ctx.cfg.tool = ToolConfig()`, `ctx.cfg.rag = RAGConfig()` (defaults), plus whatever
   `ctx.services_required.*` stubs `apply_config_dict()` needs to avoid touching real
   services (mirror the `None` stubs already used in `svc()`,
   `tests/agent/services/test_config_reload.py:35-38`), and returns
   `ConfigReloadService(ctx)` alongside `ctx` itself (so tests can assert on
   `ctx.cfg.llm.llm_temperature` post-call).
3. Add a test asserting that `svc.apply_config_dict({"llm_temperature": 5.0})` (a
   value exceeding `LLM_TEMPERATURE_MAX`) raises `ConfigReloadValidationError`, and
   that `ctx.cfg.llm.llm_temperature` is still the default (`0.2`,
   `config_dataclasses.py:120`) afterward (AC-01).
4. Add a test asserting that a valid single-field reload (e.g.
   `{"llm_temperature": 0.5}`) applies without raising and that
   `ctx.cfg.llm.llm_temperature == 0.5` afterward (AC-02).
5. Add a test asserting that a single reload request touching multiple llm/tool/rag
   fields at once (e.g. `{"llm_temperature": 0.5, "tool_cache_ttl": 120.0,
   "use_semantic_cache": True}`) applies all 3 fields correctly in one call (AC-03).

### Method
Real-dataclass-instance fixture + direct-call assertions: construct `ctx.cfg.llm`/
`.tool`/`.rag` as real config dataclass instances (not `MagicMock`), call
`apply_config_dict()` with a raw dict matching its existing `new_cfg` contract, and
assert both the exception behavior and the resulting field values.

### Details
- New fixture lives alongside, not replacing, the existing `svc()` fixture
  (`test_config_reload.py:13-39`).
- Tests target `ConfigReloadService.apply_config_dict()` directly (not
  `apply_config()`) since the request-to-dict conversion (`_req_to_dict`) is already
  covered by `test_req_to_dict_skips_none_fields`
  (`test_config_reload.py:77-85`) and is orthogonal to this plan's concern.
- `LLM_TEMPERATURE_MAX = 2.0` (`config_dataclasses.py:109`) is the exact boundary the
  rejection test relies on — confirm this constant's value has not changed if this
  test starts failing unexpectedly.

## Compatibility considerations

- N/A: test-only file; no production behavior touched.

## Security considerations

- N/A: test-only change, no new input path.

## Rollback considerations

- Test-only addition; revert via `git revert` of this file's commit with no
  production-code impact.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/agent/services/test_config_reload.py` | Unit | `uv run pytest tests/agent/services/test_config_reload.py -v` | New AC-01/AC-02/AC-03 tests green, all existing tests in the file still green |
| Repository-wide | Regression | `uv run pytest` | No new failures |

## Completion criteria

- 3 new test cases exist and pass: reject-out-of-range (AC-01), accept-valid-value
  (AC-02), accept-multi-field-single-request (AC-03).
- No existing test in `test_config_reload.py` regresses.

## Out of scope

- `test_config_reload_classification.py` — unrelated MCP classification tests, no
  change needed.
- Any test of `config_validators.py`'s individual `validate_*` functions directly —
  those are exercised indirectly through `LLMConfig`/`RAGConfig`/`ToolConfig`
  construction, already covered by `tests/agent/test_config_dataclasses.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add real-instance fixture for llm/tool/rag reload tests | Pending | — | — | |
| 2 | Add AC-01 rejection test | Pending | — | — | |
| 3 | Add AC-02/AC-03 acceptance tests | Pending | — | — | |
| 4 | Run `uv run pytest tests/agent/services/test_config_reload.py -v` and full suite | Pending | — | — | |

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
- **Requirement ID**: REQ-005 (regression tests for validator re-execution on reload)
- **Source issue**: `issues/20260825_cfgreload_missing_validator_reexecution_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-142225_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260826-103846
- **Related target files**: `tests/agent/services/test_config_reload.py`
