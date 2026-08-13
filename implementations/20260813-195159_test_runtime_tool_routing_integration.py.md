## Goal

Update `tests/agent/services/test_runtime_tool_routing_integration.py`'s
`RuntimeTool`/`build_runtime_tool()` fixtures for the schema-2.0 required-
field contract, and add an incomplete-declaration-rejection case exercised
through the full discovery-to-routing path, so this integration suite keeps
proving `RuntimeToolRegistry` is the sole routing authority under the new
fail-closed discovery behavior.

## Scope

In scope:
- `tests/agent/services/test_runtime_tool_routing_integration.py` — 368
  lines today, organized into `TestRuntimeRegistryPriorityInResolve`,
  `TestLogRoutingCoverageWithRuntime`,
  `TestBrowserToolsConfigDependentMigration`,
  `TestDiscoveryToLlmVisibilityEndToEnd`.
- The module-level `_make_runtime_registry()` helper (lines 60-100), which
  constructs `RuntimeTool` fixtures directly via `build_runtime_tool(...,
  resource_scope="", ...)` — the *current* singular-field call signature.

Out of scope:
- `scripts/agent/services/mcp_tool_discovery.py` (sibling doc).
- `tests/agent/services/test_mcp_tool_discovery.py` (sibling doc, file 6).
- `scripts/shared/runtime_tool.py`'s `build_runtime_tool()` signature itself
  (a different file's change this test's fixture depends on).

## Assumptions

- Confirmed by reading the file in full: `_make_runtime_registry()` (lines
  60-100) calls `build_runtime_tool(name="browser_fetch", server_key=
  "web_search", description="Fetch a URL", input_schema={...}, status=
  "active", is_write=False, requires_serial=True, resource_scope="",
  agent_safety_tier="READ_ONLY", requires_approval=False,
  enabled_for_llm=True, capabilities=("web_fetch",))` — the current
  singular `resource_scope=""` keyword. This call site's keyword argument
  must change to `resource_scope_kind=""`, `resource_scope_keys=()` once
  `build_runtime_tool()`'s signature is renamed (per the plan's Phase 1
  step, a different file). The `extra` loop (lines 87-99) builds a second
  `build_runtime_tool()` call with the same `resource_scope=""` keyword and
  needs the identical update.
- This file's own module docstring (lines 1-6) states its purpose: "wiring
  into the routing layer, `/mcp` tools subcommand, and
  `web_search_tools.py`'s `browser_fetch` entry's `config_dependent`
  migration" — none of its 4 test classes currently exercise the discovery
  service's *validation* path directly (`_make_runtime_registry()` builds a
  `RuntimeToolRegistry` by hand, bypassing `McpToolDiscoveryService`
  entirely); `TestDiscoveryToLlmVisibilityEndToEnd` (lines 324-368) is the
  one class that does exercise discovery, per its name — confirmed by
  reading lines 324-368 (existing test:
  `test_disabled_discovered_tool_excluded_from_llm_payload`, line 352). This
  is the natural home for the new incomplete-declaration-rejection case
  required by the plan, since it is the only class in this file that
  already drives `McpToolDiscoveryService` end-to-end rather than
  hand-constructing a registry.
- 3 prior-cycle docs exist for this basename under `implementations/done/`
  (dated 2026-07-20/2026-07-21, predating this plan). Confirmed by grep that
  `resource_scope_kind`/`resource_scope_keys` do not exist anywhere in
  `tests/` today — none of those prior cycles implemented this plan's
  fields (plausibly they cover the `config_dependent` migration the file's
  own docstring references, matching `TestBrowserToolsConfigDependentMigration`,
  lines 285-322). Coincidental filename matches, not this plan's change.
- The plan's Validation plan row for this pair of files states: "Round-trip
  preserves all 4 fields; incomplete tool excluded from registry, not
  defaulted" — applied here as: the routing layer must correctly resolve a
  fully-declared tool's route (existing coverage, needs only the fixture's
  keyword-argument rename) and must correctly *fail to resolve* an
  incomplete tool that discovery rejected (new coverage, added to
  `TestDiscoveryToLlmVisibilityEndToEnd`).

## Design decisions

- Rename `_make_runtime_registry()`'s 2 `build_runtime_tool(...,
  resource_scope="", ...)` call sites to `resource_scope_kind="",
  resource_scope_keys=()` — a mechanical adaptation to the renamed
  `build_runtime_tool()` signature, not a behavior change; both call sites
  keep the same *effective* unscoped meaning (empty string kind, empty keys
  tuple) since `browser_fetch` and this helper's `extra` tools are all
  read-only and unscoped in this test suite's fixtures today.
- Add one new test to `TestDiscoveryToLlmVisibilityEndToEnd`
  (`test_incomplete_tool_declaration_excluded_from_routing`, placed after
  the existing `test_disabled_discovered_tool_excluded_from_llm_payload` at
  line 352) that drives `McpToolDiscoveryService.discover_all()` with a
  mocked HTTP response missing one schema-2.0 field, then asserts the
  resulting registry cannot route that tool name — i.e. constructing a
  `ToolRouteResolver` from the discovery result's registry and asserting
  `resolver.resolve(name)` raises `ValueError` per the existing pattern at
  line 128 (`test_unknown_tool_raises_with_runtime_only`), proving the
  end-to-end consequence (discovery rejection → routing failure, not a
  silently-defaulted route) rather than only unit-testing discovery in
  isolation (that unit-level coverage belongs to the sibling
  `test_mcp_tool_discovery.py` doc, file 6).
- This test needs its own HTTP-mock scaffolding since
  `test_runtime_tool_routing_integration.py` does not currently import
  `McpToolDiscoveryService`'s HTTP-mocking helpers (`_async_result`/`_resp`/
  `_make_ctx` are private to `test_mcp_tool_discovery.py`, not imported
  cross-file) — the new test builds its own minimal `AsyncMock`/`MagicMock`
  response inline, following the same shape as
  `test_disabled_discovered_tool_excluded_from_llm_payload`'s existing setup
  at lines 352-368 (read in full to confirm this file's own established
  mocking idiom for discovery-driving tests, reused rather than importing
  the sibling test module's private helpers).

## Alternatives considered

- Importing `_async_result`/`_resp`/`_make_ctx` from
  `test_mcp_tool_discovery.py` into this file to avoid duplicating mock
  scaffolding: rejected — cross-test-module imports of private
  (underscore-prefixed) helpers are not this codebase's existing convention
  (neither file currently imports from the other), and
  `test_disabled_discovered_tool_excluded_from_llm_payload` already
  demonstrates this file has its own working, self-contained mocking
  approach for discovery-driving tests.
- Adding the incomplete-declaration case to
  `TestRuntimeRegistryPriorityInResolve` instead of
  `TestDiscoveryToLlmVisibilityEndToEnd`: rejected — that class's existing
  tests all construct `RuntimeToolRegistry` by hand via
  `_make_runtime_registry()`, never through `McpToolDiscoveryService`; a
  discovery-rejection case belongs with the one class that actually drives
  discovery, matching this doc's stated design decision above.

## Implementation

### Target file: `tests/agent/services/test_runtime_tool_routing_integration.py`

### Procedure

1. Update `_make_runtime_registry()` (lines 60-100): change both
   `resource_scope=""` keyword arguments (in the `browser_fetch` call at
   line 80 and the `extra`-loop call at line 94) to
   `resource_scope_kind="", resource_scope_keys=()`.
2. Add `test_incomplete_tool_declaration_excluded_from_routing` to
   `TestDiscoveryToLlmVisibilityEndToEnd` (after line 368's existing test),
   mocking one HTTP-transport server's `/v1/tools` response with a tool
   entry missing `resource_scope_keys` (or another of the 4 fields), driving
   `McpToolDiscoveryService(ctx).discover_all()`, then building a
   `ToolRouteResolver` from the result and asserting
   `resolver.resolve(<that tool's name>)` raises `ValueError` (per the
   existing `pytest.raises(ValueError, match="Unknown tool")` idiom used at
   line 128).
3. No change to any of the other 3 test classes
   (`TestRuntimeRegistryPriorityInResolve` beyond step 1's fixture-helper
   rename which they all transitively use, `TestLogRoutingCoverageWithRuntime`,
   `TestBrowserToolsConfigDependentMigration`).

### Method

One mechanical rename inside a shared fixture helper (affects every test
that calls it, transitively, with no assertion changes needed since the
helper's *effective* values are unchanged) plus one new, self-contained
integration test.

### Details

```python
def _make_runtime_registry(
    *, extra: dict[str, str] | None = None
) -> RuntimeToolRegistry:
    """Create a minimal RuntimeToolRegistry with browser_fetch, plus any extra tools.

    `extra` maps additional tool_name -> server_key pairs to register alongside
    browser_fetch, for tests that need more than one routable tool.
    """
    tool = build_runtime_tool(
        name="browser_fetch",
        server_key="web_search",
        description="Fetch a URL",
        input_schema={
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"],
        },
        status="active",
        is_write=False,
        requires_serial=True,
        resource_scope_kind="",
        resource_scope_keys=(),
        agent_safety_tier="READ_ONLY",
        requires_approval=False,
        enabled_for_llm=True,
        capabilities=("web_fetch",),
    )
    tools = {"browser_fetch": tool}
    for name, server_key in (extra or {}).items():
        tools[name] = build_runtime_tool(
            name=name,
            server_key=server_key,
            status="active",
            is_write=False,
            requires_serial=False,
            resource_scope_kind="",
            resource_scope_keys=(),
            agent_safety_tier="READ_ONLY",
            requires_approval=False,
            enabled_for_llm=True,
            capabilities=(),
        )
    return RuntimeToolRegistry(tools=tools)
```

New test in `TestDiscoveryToLlmVisibilityEndToEnd` (illustrative; exact HTTP
mock shape follows the neighboring
`test_disabled_discovered_tool_excluded_from_llm_payload`'s established
pattern in this file):

```python
    @pytest.mark.asyncio
    async def test_incomplete_tool_declaration_excluded_from_routing(self) -> None:
        """A tool missing a schema-2.0 field is excluded from the registry,
        so routing raises for it instead of resolving to a defaulted spec."""
        http = AsyncMock(spec=httpx.AsyncClient)
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {
            "tools": [
                {
                    "name": "incomplete_tool",
                    "description": "d",
                    "inputSchema": {"type": "object", "properties": {}},
                    "is_write": False,
                    "requires_serial": False,
                    "resource_scope_kind": "",
                    # resource_scope_keys deliberately omitted
                }
            ]
        }
        http.get = AsyncMock(return_value=resp)
        ctx = MagicMock()
        ctx.cfg.mcp.mcp_servers = {"srv": _http()}
        ctx.cfg.mcp.security_profile = SecurityProfile.LOCAL
        ctx.services_required.http = http

        result = await McpToolDiscoveryService(ctx).discover_all()
        resolver = ToolRouteResolver({}, runtime_registry=result.registry)

        with pytest.raises(ValueError, match="Unknown tool"):
            resolver.resolve("incomplete_tool")
```
(`SecurityProfile` needs adding to this file's existing `from shared.mcp_config
import (McpServerConfig, StartupMode, TransportType)` line 18-22.)

## Compatibility considerations

- Step 1's rename must land in the same commit/PR as the `runtime_tool.py`
  field rename (a different file) — this file's `build_runtime_tool()` call
  sites will raise `TypeError` (unexpected keyword `resource_scope`) against
  the *new* signature if left unchanged, and will raise `TypeError`
  (unexpected keyword `resource_scope_kind`) against the *old* signature if
  changed prematurely. This mirrors the same lockstep constraint noted in
  the sibling `test_mcp_tool_discovery.py` doc.
- The new end-to-end test (step 2) depends on the sibling
  `mcp_tool_discovery.py` production change already rejecting incomplete
  entries; until that lands, this test would fail because the tool would
  still be present (defaulted) in the registry and `resolver.resolve()`
  would succeed instead of raising.

## Security considerations

N/A — test-only file; no production security surface. The new test does
verify, at the integration level, that an incomplete tool declaration cannot
be silently routed to — directly exercising the plan's fail-closed intent
rather than only asserting it at the discovery-unit level.

## Rollback considerations

- Revert both the fixture-helper rename and the new test together, in
  lockstep with a revert of the `runtime_tool.py` rename and the sibling
  `mcp_tool_discovery.py` change; partial revert leaves this suite red.

## Validation plan

- `uv run pytest tests/agent/services/test_runtime_tool_routing_integration.py -v`
  — all 4 existing classes continue to pass with the renamed fixture
  keywords; the new incomplete-declaration test passes.
- `uv run pytest tests/agent/services/test_mcp_tool_discovery.py tests/agent/services/test_runtime_tool_routing_integration.py -v` — per the plan's
  combined Validation plan row.

## Out of scope

- `TestLogRoutingCoverageWithRuntime`,
  `TestBrowserToolsConfigDependentMigration` — no direct change beyond the
  transitive fixture-helper rename in step 1, which does not alter their
  existing assertions or intent.
- Unit-level discovery-rejection coverage for each of the 4 individual
  fields — that granularity belongs to the sibling
  `test_mcp_tool_discovery.py` doc (file 6); this file adds one
  representative end-to-end case, not exhaustive per-field coverage.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260813-183049_plan.md
- Source implementation procedure: N/A
- Generated at: 20260813-195159
- Related target files: tests/agent/services/test_runtime_tool_routing_integration.py
