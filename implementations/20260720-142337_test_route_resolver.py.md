# Implementation procedure: `tests/test_route_resolver.py` (rebaseline for no-fallback `ToolRouteResolver`)

Source plan: `plans/done/20260720-134821_plan.md`, Implementation step Phase 1 (test rebaseline,
resolving UNK-03) + Phase 2 step "Apply the Phase 1 test rewrites."

No prior implementation doc targets this filename (`grep -rl`/`ls | grep -F` over `implementations/`
and `implementations/done/` for `test_route_resolver.py` returns no hits — content-grep for the
string "test_route_resolver" only matches unrelated docs about earlier features: strict-mode
addition, `_EXACT_ROUTES` removal, coverage-classification fixes, MDQ routing, browser-server
routing). This is a new document.

## Goal

Rewrite `tests/test_route_resolver.py` so every test reflects the post-plan contract: constructing
`ToolRouteResolver(configs)` **without** a `runtime_registry=` argument means the resolver has *no*
routing source at all (not "falls back to `ToolRegistry`") — any tool name, however well-known,
raises `ValueError` unless resolved via an explicitly-passed `runtime_registry`.

## Scope

**In scope**: `tests/test_route_resolver.py` only (398 lines, 8 classes, 34 test methods — full file
read and enumerated below).

**Out of scope**: `tests/test_runtime_tool_routing_integration.py` — separate doc.
`tests/test_tool_registry.py` (if it exists) or any test of `ToolRegistry.register()`/
`get_server_for_tool()` in isolation — `TestDuplicateToolRegistration.test_duplicate_registration_raises_value_error`
(lines 386-398) tests `ToolRegistry` directly, not through the resolver, and needs **no change** —
confirmed unaffected below.

## Assumptions — full test-by-test classification (resolves UNK-03)

Read the entire file directly (`tests/test_route_resolver.py`, offset 1-398). The plan's Affected
Areas table names 12 specific tests as "rewrite/remove" candidates via grep; a full read reveals the
**actual impact is broader** — several tests not named in the plan also construct
`ToolRouteResolver(configs)` with no `runtime_registry=` and assert successful resolution of
well-known tool names (e.g. `read_text_file`, `shell_run`), which only currently succeeds via the
`ToolRegistry` fallback bootstrap inside `__init__`. This doc's classification below is the
authoritative worklist — supersedes the plan's grep-derived sample for this file.

| Class | Test | Current behavior | Post-plan disposition |
|---|---|---|---|
| `TestRegistryRouting` (setup: `ToolRouteResolver(configs)`, no `runtime_registry`) | `test_read_tools`, `test_write_tools`, `test_delete_tools`, `test_shell_run`, `test_search_web`, `test_github_tools`, `test_rag_tools`, `test_cicd_tools` | Resolve via legacy `ToolRegistry` fallback | **BREAKS** — not named in plan's list, but must be fixed: rewrite `setup_method` to construct the resolver with an explicit `runtime_registry=` built from the same tool set (see Method below), or delete the class if superseded by an equivalent `test_runtime_tool_routing_integration.py` case |
| `TestRegistryRouting` | `test_unknown_tool_raises`, `test_query_sqlite_no_longer_routable` | Expect `ValueError` regardless of fallback | **No change** — still raises `ValueError` with or without fallback |
| `TestConfigDrivenRouting` | `test_config_does_not_override_registry` (line 90), `test_config_only_tools_do_not_route` (line 101, the `resolver.resolve("read_text_file")` assertion on line 112 specifically) | Resolve `search_web`/`read_text_file` via legacy fallback | **BREAKS** — plan names `test_config_does_not_override_registry` and `test_config_only_tools_do_not_route`; confirmed both need `runtime_registry=` fixtures added |
| `TestConfigDrivenRouting` | `test_empty_server_configs` (line 114) | `ToolRouteResolver({})` then resolves `read_text_file` via fallback | **BREAKS — not named in plan.** Must add `runtime_registry=` or rewrite to assert `ValueError` instead (only a `runtime_registry=` fixture preserves the test's original intent of "resolution works with no server configs at all") |
| `TestConfigDrivenRouting` | `test_unknown_tool_with_partial_config_raises` (line 118) | Expects `ValueError` | **No change** |
| `TestRegistryWithoutConfig` | `test_registry_routes_without_config_tool_names` (line 146), `test_registry_routes_all_tool_constants_tools` (line 154) | Resolve via legacy fallback for the full `tool_constants.py` tool set | **BREAKS, named in plan** — rewrite to build a `runtime_registry` covering the same tool set, or delete (the "no config tool_names needed" point these tests make is orthogonal to RuntimeToolRegistry vs. ToolRegistry and could be re-expressed with a `runtime_registry` fixture instead) |
| `TestRegistryWithoutConfig` | `test_strict_mode_error_message_mentions_any_registry` (line 164) | Asserts message contains "any registry" | **BREAKS, named in plan** — new message text from the `route_resolver.py` doc's `_raise_strict_error()` rewrite no longer says "any registry"; update the `match=` string to the new message (coordinate exact wording with that doc) |
| `TestBuildDiscoveryMap` (all 6 tests, lines 175-248) | Tests `build_discovery_map()` module function directly — no `ToolRouteResolver` involved | **No change** — this function is untouched by the plan |
| `TestDiscoveryMapValidationOnly` | `test_discovery_map_does_not_override_registry` (line 265), `test_registry_fallback_when_tool_not_in_discovery_map` (line 273, named in plan), `test_empty_discovery_map_falls_through_to_registry` (line 280, named in plan), `test_discovery_map_none_falls_through_to_registry` (line 294, named in plan) | All resolve `read_text_file` via legacy fallback regardless of `discovery_map` | **BREAK** — all four need `runtime_registry=` fixtures, or must be rewritten to assert `ValueError` (proving `discovery_map` still has zero routing effect, now against a backdrop of "no fallback" rather than "fallback still resolves it") |
| `TestDiscoveryMapValidationOnly` | `test_unknown_tool_raises_regardless_of_discovery_map` (line 286) | Expects `ValueError` | **No change** |
| `TestLogRoutingCoverage` | `test_discovery_map_only_tool_is_unmapped` (line 313, named in plan), `test_registry_mapped_tool_is_mapped` (line 337, named in plan) | `_log_routing_coverage()` classifies via legacy fallback | **BREAK** — `test_registry_mapped_tool_is_mapped` needs a `runtime_registry=` fixture so `read_text_file` is mapped; `test_discovery_map_only_tool_is_unmapped` needs re-verification that `read_text_file` becomes unmapped too now (both tools in its `known_tools` set would be unmapped without a registry — the test's "1/2 mapped" assertion no longer holds unless a `runtime_registry` covering `read_text_file` is added) |
| `TestLogRoutingCoverage` | `test_all_unmapped_when_registry_and_discovery_map_both_miss` (line 348, named in plan) | Asserts a genuinely-unknown tool is unmapped | **Likely no behavior change needed** — verify at implementation time: this test's tool (`totally_unknown_tool`) is absent from both registries today and remains absent from the sole `RuntimeToolRegistry` after the fallback is removed, so the "0/1 unmapped" assertion should still hold unmodified; the plan lists it as a rewrite candidate but a full read suggests only the docstring/comment needs updating (no legacy-registry reference to remove from the test body itself), not the assertion |
| `TestRoutingSourceIsolation` | `test_config_tool_names_do_not_affect_routing` (line 364) | Resolves `read_text_file` via legacy fallback (config `tool_names` is set but irrelevant) | **BREAKS — not named in plan.** Add `runtime_registry=` fixture, keeping the "config tool_names is ignored" assertion intact |
| `TestRoutingSourceIsolation` | `test_constants_not_used_directly_by_resolver` (line 376, named in plan) | `ToolRouteResolver({})`, expects `ValueError` for an unknown tool | **Likely no change needed** — verify: this test never expected the unknown tool to resolve; removing the fallback does not change its outcome. The plan lists it as a rewrite candidate, but on a full read no fallback-dependent behavior is actually exercised here — flag as "no-op, confirm and leave as-is" rather than force a rewrite |
| `TestDuplicateToolRegistration` | `test_duplicate_registration_raises_value_error` (line 386) | Tests `ToolRegistry.register()` directly, no resolver involved | **No change** — untouched by this plan; not named in plan's list either |

## Implementation

### Target file

`tests/test_route_resolver.py`

### Procedure

1. Add one module-level helper for building a `RuntimeToolRegistry` covering an arbitrary set of
   `(tool_name, server_key)` pairs, to replace the implicit `ToolRegistry` bootstrap the "BREAKS"
   rows above relied on. Pattern (pseudocode, mirroring
   `tests/test_runtime_tool_routing_integration.py`'s existing `_make_runtime_registry()` /
   `build_runtime_tool()` usage):
   ```
   def _runtime_registry_for(tool_to_server: dict[str, str]) -> RuntimeToolRegistry:
       tools = {
           name: build_runtime_tool(name=name, server_key=server_key, status="active",
                                     is_write=False, requires_serial=False, resource_scope="",
                                     agent_safety_tier="READ_ONLY", requires_approval=False,
                                     enabled_for_llm=True, capabilities=())
           for name, server_key in tool_to_server.items()
       }
       return RuntimeToolRegistry(tools=tools)
   ```
2. For each "BREAKS" row above, pass `runtime_registry=_runtime_registry_for({...})` to the
   `ToolRouteResolver(...)` construction so the previously-fallback-resolved tool names now resolve
   via the explicit registry instead. Keep each test's original assertions (the point being tested —
   e.g. "config does not override registry" — is unchanged; only the routing *source* changes from
   implicit-legacy to explicit-runtime).
3. For `test_strict_mode_error_message_mentions_any_registry` (both the copy in this file, line 164,
   and its near-duplicate in `test_runtime_tool_routing_integration.py`, line 129): update the
   `pytest.raises(ValueError, match="any registry")` to match whatever new message
   `_raise_strict_error()` produces per the `route_resolver.py` doc (e.g. `match="RuntimeToolRegistry"`
   — confirm exact string against that doc's implementation once landed, keep both files' copies of
   this test in lockstep).
4. For the two "Likely no change needed" rows (`test_all_unmapped_when_registry_and_discovery_map_both_miss`,
   `test_constants_not_used_directly_by_resolver`), re-run them mentally against the new `resolve()`/
   `_log_routing_coverage()` bodies before touching them — only edit docstrings/comments that
   describe a "registry" (singular, ambiguous) if they could be misread as still describing a
   two-tier model; leave assertions untouched.
5. Leave `TestBuildDiscoveryMap` (6 tests) and `TestDuplicateToolRegistration` (1 test) completely
   untouched.

### Method

Test-only edits; no production code touched by this doc. Every rewritten test keeps using
`pytest`'s existing fixtures/patterns already present in the file (`_http()` helper,
`caplog.at_level`). New tests are not required by this doc — the plan's own Design section frames
this phase as "rewrite/remove," not "add new coverage" (new no-fallback-specific tests, if desired,
are the companion `test_runtime_tool_routing_integration.py`'s `TestRuntimeRegistryPriorityInResolve`
class's job, since that file already carries the `runtime_registry`-explicit test patterns).

### Details

- Do not delete `TestRegistryRouting`, `TestConfigDrivenRouting`, `TestRegistryWithoutConfig`, or
  `TestDiscoveryMapValidationOnly` outright even though every "BREAKS" test in them needs a
  `runtime_registry=` fixture added — deleting them would silently drop real coverage (e.g., "config
  tool_names never overrides routing" is still a real, valuable invariant to test going forward, just
  against an explicit registry instead of an implicit fallback one).
  the diff-cover gate (≥90% on changed lines) in the plan's Validation Plan is the backstop against
  under-testing after this rewrite.
- `TestLogRoutingCoverage`'s three tests all construct `ToolRouteResolver(configs, known_tools=...)`
  with `caplog` assertions on `_log_routing_coverage()`'s log message ("N/M tools mapped") — since
  that method is rewritten in the companion `route_resolver.py` doc to check only
  `_lookup_runtime_registry()`, these three tests must each pass a `runtime_registry=` covering
  exactly the tools intended to be "mapped" in each test's `known_tools` set, or the counts drift
  from what each test currently asserts (e.g. `test_registry_mapped_tool_is_mapped` needs
  `read_text_file` mapped via `runtime_registry`, not via legacy fallback, to keep asserting "1/1
  tools mapped").

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Targeted unit tests | `uv run pytest tests/test_route_resolver.py -v` | All 34 tests pass; no test silently expects fallback behavior anymore |
| Full suite | `uv run pytest` | No new failures |
| Diff coverage | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | ≥ 90% on changed lines (guards against coverage loss from any deleted assertions) |
| Format/lint | `uv run ruff format tests/test_route_resolver.py && uv run ruff check tests/test_route_resolver.py` | 0 errors |
| Type check | `uv run mypy tests/test_route_resolver.py` (covered by `tests/` in pre-commit's mypy run per `rules/coding.md`) | No new errors |
