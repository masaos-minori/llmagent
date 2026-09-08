# Unknown-top-level-key validation breaks legacy flat-key test configs across 5 test files

## Priority
High

## Summary
Commit `9a7cdb40e` ("REQ-004: Add `_check_unknown_production_keys()` method to
ProductionConfigValidator") added a new validation to
`scripts/shared/production_config_validator.py` that rejects any top-level config key
not present in its derived allowed-keys set. This breaks `build_agent_config()` for
every caller still using the old flat top-level key names, causing 278 test failures
(out of 3,142 collected) across 5 test files as of `origin/master` commit `ca031b494`.

## Background
`_get_valid_production_keys()` derives its allowed-keys set via `dataclasses.fields()`
introspection over the current nested sub-config dataclasses (`LLMConfig`,
`RAGConfig`, `ToolConfig`, `MemoryConfig`, `MCPConfig`, `ApprovalConfig`,
`ObservabilityConfig`, `DiagnosticsConfig`, `MessageRoleConfig`) plus a short explicit
list of `AgentConfig`-level and `build_agent_config()`-direct keys. Several existing
test helpers still call `build_agent_config()` with old flat top-level keys (e.g.
`tool_cache_ttl`, `top_k_search`, `top_k_rerank`, `rag_top_k`, `use_mqe`, `use_search`,
`use_rrf`, `use_rerank`, `rag_min_score`, `max_chunks_per_doc`, `use_two_stage_fetch`,
`two_stage_max_docs`) that are not in the new derived set, and the new validation now
rejects them with `SystemExit(1)`.

## Problem
`_cfg()` in `tests/agent/test_tool_policy_comprehensive.py` (and equivalent helpers in
the other affected files) constructs a config dict with these legacy flat keys and
passes it to `build_agent_config()`. `build_agent_config()` calls
`ProductionConfigValidator.validate()`, which now calls
`_check_unknown_production_keys()` and exits the process with `SystemExit(1)` and a
"Production config validation failed: ... Unknown config keys: ..." error, instead of
constructing the config.

Reproduction (both confirmed by direct execution, not by the raw test-suite `278
failed` line alone — see Evidence):
```
uv run pytest tests/agent/test_tool_policy_comprehensive.py -q
# → 29 failed, 9 passed in 0.95s
```

The 278 failures span:
- `tests/agent/test_tool_policy_comprehensive.py`
- `tests/agent/test_agent_negative_paths.py`
- `tests/integration/test_rag_llm_integration.py`
- `tests/agent/services/test_runtime_tool_routing_integration.py`
- `tests/agent/test_repl.py`

## Reason for Change
This is a real, reproducible regression against `origin/master` — not a flaky or
environment-specific failure (confirmed by a single-test run completing in under 1
second with the identical `SystemExit(1)` traceback). Left unfixed, it makes the
entire test suite an unreliable signal for every unrelated change (a genuinely broken
change and this pre-existing regression are currently indistinguishable in a full
`pytest` run), and blocks anyone relying on `uv run pytest tests/` passing cleanly
before merging further work.

## Implementation Intent
Two candidate fix directions exist; determine which is correct before implementing
either — do not apply both speculatively:

1. **Update the test helpers** to use the current nested sub-config key names, if
   `build_agent_config()`'s supported input shape has already migrated to nested
   sub-configs and the flat keys are simply stale test fixtures.
2. **Extend `_get_valid_production_keys()`/`_check_unknown_production_keys()`** to
   also accept these specific flat keys, if `build_agent_config()` still supports flat
   top-level keys as a documented/intended input shape (e.g. for backward
   compatibility or a flattened convenience API) and REQ-004's allowed-keys
   derivation simply missed them.

Resolve this by reading `build_agent_config()`'s own handling of these keys (does it
already map a flat `tool_cache_ttl` into `ToolConfig.cache_ttl`-equivalent, or does it
require the nested shape directly?) before choosing a direction — this determines
whether the bug is in the test fixtures or in REQ-004's allowed-keys derivation.

## Target Files or Areas
- `scripts/shared/production_config_validator.py` (`_get_valid_production_keys()`, `_check_unknown_production_keys()`)
- `scripts/agent/config_builders.py` (`build_agent_config()`)
- `tests/agent/test_tool_policy_comprehensive.py`
- `tests/agent/test_agent_negative_paths.py`
- `tests/integration/test_rag_llm_integration.py`
- `tests/agent/services/test_runtime_tool_routing_integration.py`
- `tests/agent/test_repl.py`

## Required Changes
- Determine `build_agent_config()`'s current intended input shape for the keys listed
  in Problem (flat vs. nested), per Implementation Intent.
- Apply exactly one of the two fix directions above, consistently across all 5
  affected test files.
- Re-run the full suite and confirm the failure count drops to zero for this cause.

## Constraints
Do not weaken or bypass the unknown-key rejection itself merely to make the tests
pass — REQ-004 added it intentionally (to catch genuine config typos/mistakes in
production). Any fix must preserve that protection for keys that are genuinely
invalid, and only accommodate keys that are a legitimate current input shape.

## Acceptance Criteria
- [ ] `uv run pytest tests/agent/test_tool_policy_comprehensive.py -q` passes with no failures
- [ ] `uv run pytest tests/agent/test_agent_negative_paths.py -q` passes with no failures
- [ ] `uv run pytest tests/integration/test_rag_llm_integration.py -q` passes with no failures
- [ ] `uv run pytest tests/agent/services/test_runtime_tool_routing_integration.py -q` passes with no failures
- [ ] `uv run pytest tests/agent/test_repl.py -q` passes with no failures
- [ ] `uv run pytest tests/shared/test_production_config_validator.py -q` (REQ-004's own new tests) still passes unchanged — the fix must not remove the unknown-key protection itself
- [ ] A full `uv run pytest tests/ -q` run shows no failures attributable to `SystemExit(1)` from `ProductionConfigValidator`

## Testing Expectations
Full `uv run pytest tests/ -q` run before and after the fix, to confirm the failure
count for this specific cause drops from 278 to 0 with no new regressions introduced
by whichever fix direction is chosen.

## Documentation Impact
Needs confirmation: if a canonical doc enumerates `AgentConfig`'s supported top-level
config keys (flat vs. nested), it should reflect whichever shape is confirmed correct
by this issue's investigation. Not confirmed whether such a doc currently exists.

## Out of Scope
- Any other validation rule already present in `ProductionConfigValidator` before commit `9a7cdb40e`.
- Any change to REQ-004's own new tests (`TestProductionConfigValidatorUnknownTopLevelKeys`) beyond what's needed to keep them passing.
- Any unrelated refactor of `config_builders.py` or the affected test files.

## Dependencies
Depends on understanding commit `9a7cdb40e` ("REQ-004: Add
`_check_unknown_production_keys()` method to ProductionConfigValidator"), which
introduced the regression.

## Unresolved Questions
- Whether `build_agent_config()`'s intended, current input shape is flat top-level
  keys, nested sub-config keys, or both (accepting one shape and normalizing) — this
  determines which of the two Implementation Intent directions is correct.
- Why this regression was not caught when commit `9a7cdb40e` was made — whether
  REQ-004's own implementation/validation step ran the full test suite before that
  commit, or only its own new tests.

## AI Implementation Instruction
Read `build_agent_config()`'s current handling of the listed legacy flat keys first —
do not guess between the two fix directions. Fix exactly one direction consistently
across all 5 affected files; do not patch some files with the test-update direction
and others with the validator-allowlist direction. Do not modify unrelated parts of
`production_config_validator.py`, `config_builders.py`, or the affected test files.
Re-run the full test suite (not just the previously-failing files) to confirm no new
regression was introduced, and confirm REQ-004's own new tests
(`TestProductionConfigValidatorUnknownTopLevelKeys`) still pass unchanged.
