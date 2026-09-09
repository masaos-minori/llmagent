# Tool-result caching was removed from `ToolExecutor`, but its config keys, a stale docstring, and a test using the removed constructor argument remain

## Priority
High

## Summary
`ToolExecutor.__init__()` (`scripts/shared/tool_executor.py`) no longer accepts a
`cache_ttl` parameter and has no caching mechanism at all (confirmed by direct read: its
current signature is `http, server_configs, concurrency_limits, lifecycle` — no
cache-related parameter or internal cache state). This is inconsistent with 3 other
pieces of the repository that still assume tool-result caching exists:
`config/agent.toml` still sets `tool_cache_ttl = 300` and `tool_cache_max_size = 200` as
live top-level config keys; `scripts/shared/tool_cache.py`'s module docstring still
describes `ToolExecutor` as having "its own internal OrderedDict-based cache (see
`_execute_with_cache()`, `_store_and_evict()` in `shared/tool_executor.py`)" — neither
method exists anywhere in the current codebase (confirmed via `rg` returning zero
matches repository-wide); and
`tests/agent/services/test_runtime_tool_routing_integration.py::TestRuntimeRegistryPriorityInResolve::test_set_runtime_registry_preserves_resolver_identity`
fails with `TypeError: ToolExecutor.__init__() got an unexpected keyword argument
'cache_ttl'`. Additionally, `tool_cache_ttl`/`tool_cache_max_size` are not present in any
current `ToolConfig`/sub-config dataclass field (confirmed via `rg` across
`scripts/agent/config_dataclasses.py`), so if `config/agent.toml` is loaded through
`ProductionConfigValidator`'s unknown-top-level-key check (`_get_valid_production_keys()`
in `scripts/shared/production_config_validator.py`), `tool_cache_ttl` would itself be
flagged as an unknown key — the same failure mode as
`plans/done/20260908-221312_plan.md` (cfgval001), but potentially against the real,
deployed `config/agent.toml` rather than only a test fixture.

## Background
Discovered while investigating `test_runtime_tool_routing_integration.py`'s failure
during a freeze-validation re-entry for `plans/done/20260908-221312_plan.md` (cfgval001).
`scripts/shared/tool_cache.py` defines a standalone `ToolResultCache` class whose own
docstring explicitly states it is "NOT currently used by `ToolExecutor`" and that
`ToolExecutor` instead "maintains its own internal ... cache" via `_execute_with_cache()`
/ `_store_and_evict()` — but a repository-wide `rg` for both method names finds no
occurrences anywhere in `scripts/`. `git log -S"_execute_with_cache" --
scripts/shared/tool_executor.py` shows historical commits that added and later removed
cache-related code from this file, but the exact removal commit was not pinpointed (see
Unresolved Questions).

## Problem
Three independent artifacts still assume `ToolExecutor` has a caching mechanism that no
longer exists:
1. `config/agent.toml`'s `tool_cache_ttl`/`tool_cache_max_size` keys have no consumer.
2. `scripts/shared/tool_cache.py`'s module docstring describes a `ToolExecutor`-internal
   cache mechanism (`_execute_with_cache()`/`_store_and_evict()`) that does not exist.
3. `test_runtime_tool_routing_integration.py` passes `cache_ttl=` to
   `ToolExecutor.__init__()`, which no longer accepts it, causing 1 test failure.

Reproduction (confirmed by direct execution):
```
uv run pytest tests/agent/services/test_runtime_tool_routing_integration.py -q
# → 1 failed, 14 passed in 1.40s
# TestRuntimeRegistryPriorityInResolve.test_set_runtime_registry_preserves_resolver_identity:
# TypeError: ToolExecutor.__init__() got an unexpected keyword argument 'cache_ttl'
```

## Reason for Change
Beyond the 1 immediate test failure, `config/agent.toml`'s `tool_cache_ttl` key is a
candidate live-production risk: if `ProductionConfigValidator`'s unknown-top-level-key
check runs against the real deployed `config/agent.toml` (as `build_agent_config()`
does by default with `security_profile="production"`), this key would be flagged
`Unknown config keys: 'tool_cache_ttl'` and could cause the same `SystemExit(1)` this
issue's sibling (`plans/done/20260908-221312_plan.md`, cfgval001) found in test fixtures
— but here against real deployed configuration. This has not been directly confirmed
against a live production startup (see Unresolved Questions) and must be checked before
assuming it is currently broken, but the config/schema mismatch itself is confirmed.

## Implementation Intent
Determine whether tool-result caching is intended to be reinstated in `ToolExecutor`
(in which case `cache_ttl`/`max_size` should be wired back into
`ToolExecutor.__init__()`, sourced from `ToolConfig`, and `tool_cache_ttl`/
`tool_cache_max_size` added back to `_get_valid_production_keys()`'s derivation) or was
intentionally dropped (in which case `config/agent.toml`'s 2 keys should be removed,
`scripts/shared/tool_cache.py`'s stale docstring corrected to stop describing a
nonexistent internal cache, and `test_runtime_tool_routing_integration.py`'s `cache_ttl=`
argument removed). Do not guess between these — confirm via the commit history that
removed `_execute_with_cache()` (see Unresolved Questions) before choosing a direction.

## Target Files or Areas
- `config/agent.toml` (`tool_cache_ttl`, `tool_cache_max_size` keys)
- `scripts/shared/tool_cache.py` (module docstring)
- `tests/agent/services/test_runtime_tool_routing_integration.py`
  (`_make_executor()`/the failing test's `cache_ttl=` argument)
- `scripts/shared/tool_executor.py` — reference only, unless reinstating caching is
  chosen
- `scripts/shared/production_config_validator.py` (`_get_valid_production_keys()`) —
  reference only, unless reinstating caching is chosen

## Required Changes
Deferred until the Implementation Intent's direction is confirmed — do not implement
either option speculatively. Whichever direction is chosen, `test_runtime_tool_routing_integration.py`'s
failing test must be corrected to match the confirmed current contract.

## Constraints
Do not silently make `tool_cache_ttl`/`tool_cache_max_size` pass validation without also
resolving whether they should have any effect — accepting them as valid keys while they
remain unconsumed would repeat the same "accept dead configuration" mistake this issue's
sibling (cfgval001) explicitly rejected as an incorrect fix direction.

## Acceptance Criteria
- [ ] An explicit decision is recorded on whether tool-result caching is reinstated or
  removed
- [ ] `config/agent.toml`, `scripts/shared/tool_cache.py`'s docstring, and
  `test_runtime_tool_routing_integration.py` are all consistent with that decision
- [ ] `uv run pytest tests/agent/services/test_runtime_tool_routing_integration.py -q`
  passes with no failure citing `cache_ttl`
- [ ] Confirmed (manually or via a targeted check) whether `config/agent.toml`'s current
  content passes `ProductionConfigValidator`'s unknown-top-level-key check as deployed

## Testing Expectations
- `uv run pytest tests/agent/services/test_runtime_tool_routing_integration.py -q` —
  zero failures
- A manual or scripted check confirming `config/agent.toml`'s current top-level keys
  all pass `_get_valid_production_keys()`'s current derivation (or a corrected one, if
  caching is reinstated)

## Documentation Impact
Update `scripts/shared/tool_cache.py`'s module docstring regardless of which direction
is chosen — it currently describes a nonexistent mechanism either way (a nonexistent
"canonical" internal cache if caching is removed, or a stale description needing an
update to reflect a newly-reinstated one).

## Out of Scope
- `plans/done/20260908-221312_plan.md` (cfgval001)'s own 12 obsolete-flat-key removal —
  unrelated root cause, tracked separately.
- `issues/20260909-183320_toolpolicy01_test-tool-policy-comprehensive-cfg-missing-strict-mode-keys.md` —
  unrelated root cause, tracked separately.
- Any other `ProductionConfigValidator` validation rule.

## Dependencies
N/A: none. Discovered independently while investigating cfgval001's revalidation;
does not block or depend on that Plan's own fix.

## Unresolved Questions
- The exact commit that removed `_execute_with_cache()`/`_store_and_evict()` from
  `ToolExecutor` was not pinpointed — `git log -S"_execute_with_cache" --
  scripts/shared/tool_executor.py` returns candidates but the removal diff itself was
  not isolated. Needed to determine whether the removal was deliberate (supporting the
  "remove the orphaned keys/docstring" direction) or an unintentional side effect of an
  unrelated refactor (supporting "reinstate caching").
- Whether `config/agent.toml`'s current content, loaded via the real production startup
  path, actually triggers `SystemExit(1)` today due to `tool_cache_ttl` — not directly
  confirmed against a live startup in this investigation; confirm before treating it as
  an active incident.

## AI Implementation Instruction
Do not implement either the "reinstate caching" or "remove the orphaned references"
direction until the commit history question above is resolved — surface it and stop if
asked only to investigate further. Do not add `tool_cache_ttl`/`tool_cache_max_size` to
`_get_valid_production_keys()` as a speculative fix without first confirming they have
(or will have, if caching is reinstated) an actual consumer.
