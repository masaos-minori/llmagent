# Implementation procedure: `scripts/agent/context.py` (add `AppServices.runtime_tools`) +
`scripts/agent/startup.py` (populate it at startup)

Source: cross-cutting gap identified during post-review (2026-07-18) of the 2026-07-17/18
`RuntimeToolRegistry` batch. At least seven docs in that batch
(`implementations/20260717-223600_config_reload.py.md`,
`implementations/20260717-223720_test_config_reload.py.md`,
`implementations/20260718-032912_cmd_mcp.py.md`,
`implementations/20260718-032956_test_cmd_mcp.py.md`,
`implementations/20260718-033059_full_validation_pass_mcp_tools_diagnostics.md`,
`implementations/20260717-224630_startup.py.md`,
`implementations/20260718-094319_llm_turn_runner.py.md`) reference `AppServices.runtime_tools` as a
"necessary companion change" or "blocking prerequisite," each deferring its actual implementation to
some other, unnamed doc. This doc is that owning doc — it consolidates the wiring sketch already
present in `implementations/20260718-094319_llm_turn_runner.py.md`'s Procedure step 4 into its own
concrete procedure.

## Goal

Add a nullable `runtime_tools: RuntimeToolRegistry | None = None` field to `AppServices` (mirroring
the existing late-bound, nullable `gateway`/`health_registry` fields), and populate it during startup
by running `McpToolDiscoveryService(ctx).discover_all()` — which already exists in real source today
(`scripts/agent/services/mcp_tool_discovery.py`, requirement 03's base design) — folding its findings
into the existing `_check_services()` validation pipeline.

## Scope

**In scope**
- `scripts/agent/context.py`: add the `runtime_tools` field/parameter to `AppServices.__init__`.
- `scripts/agent/startup.py::_check_services()`: add one new step that constructs
  `McpToolDiscoveryService(ctx)`, awaits `.discover_all()`, assigns
  `ctx.services_required.runtime_tools = result.registry`, and folds `result.findings`/
  `result.unreachable` into the existing `pipeline` (`StartupValidationResult`).

**Out of scope**
- The `RuntimeTool`/`RuntimeToolRegistry` classes themselves — already landed in real source
  (`scripts/shared/runtime_tool.py`, `scripts/shared/runtime_tool_registry.py`), unchanged by this doc.
- Requirement 09's consolidation of `check_tool_definitions_startup()`/`check_routing_drift_vs_live()`
  into `McpToolDiscoveryService.discover_all()` (`implementations/20260717-224511_mcp_tool_discovery.py.md`,
  `implementations/20260717-224630_startup.py.md`) — that consolidation has **not** landed either (real
  `mcp_tool_discovery.py` only has the base req-03 shape: `discover_all`/`_fetch_server_tools`/
  `_validate_and_normalize_entry`/`_dedupe_and_build`, confirmed by direct read). This doc adds a new,
  independent step to `_check_services()` that calls the base `discover_all()` as it exists today; it
  does not remove or fold in steps 4/5/6 (`check_tool_definitions_startup`, `check_routing_drift`,
  `check_routing_drift_vs_live`) — that remains requirement 09's job, landed separately, at which point
  requirement 09's own doc's step should read from/reuse this step's registry-population call instead
  of introducing a second one.
- Any of the actual consumer migrations (requirements 04 routing, 05 LLM schema, 06 scheduler, 07
  policy/approval, 08 reload, 11 `/mcp tools`, 17 disabled-visibility) — each already has its own doc;
  this doc only makes `ctx.services_required.runtime_tools` a real, populated attribute for those docs
  to read from.

## Assumptions

1. Current real state (confirmed by direct read):
   - `AppServices.__init__` (`scripts/agent/context.py:134-156`) takes `http`, `llm`, `tools`,
     `lifecycle`, `hist_mgr`, `audit_logger`, `memory` (all required), plus `health_registry:
     McpServerHealthRegistry | None = None` and `gateway: RepositoryGateway | None = None` (both
     optional, late-bound). There is no `runtime_tools` parameter/attribute today.
   - `scripts/agent/factory.py::build_agent_context()` (lines 420-444) constructs `AppServices(...)`
     synchronously inside `StartupOrchestrator._initialize()` (also synchronous) — before any MCP
     server has been started (`_start_servers()` runs later, from the async `run()`). Discovery
     (an HTTP round-trip per server) cannot happen at this point; it must happen later, once servers
     are up.
   - `StartupOrchestrator._check_services()` (`scripts/agent/startup.py:189-292`) is `async`, runs
     after `_start_servers()` has completed (per `run()`'s sequencing, lines 54-63), and already
     accumulates findings into a `StartupValidationResult` pipeline via `pipeline.add_ok`/
     `add_warning`/`add_fatal`/`add_skipped`, then raises `RuntimeError` if any fatal finding exists
     (lines 286-292). This is the natural place to run discovery and assign the registry — servers
     are guaranteed started, and the existing pipeline/fatal-raise mechanism already handles
     reporting.
   - `McpToolDiscoveryService(ctx).discover_all()` (`scripts/agent/services/mcp_tool_discovery.py:62-88`)
     returns a `DiscoveryResult(registry: RuntimeToolRegistry, findings: list[StartupCheckOutcome],
     unreachable: list[str])`. Its own findings are always `WARNING` severity today (per that module's
     docstring — no `FATAL` distinction yet without requirement 09's consolidation), except duplicate-
     tool-name findings, which are `FATAL` in `SecurityProfile.PRODUCTION` and `WARNING` in `LOCAL`
     (already implemented in `_dedupe_and_build()`).
2. Making `runtime_tools` nullable (`RuntimeToolRegistry | None = None`) mirrors the existing
   `gateway`/`health_registry` pattern exactly — code that reads `ctx.services_required.runtime_tools`
   must already be `None`-safe (per the docs listed in the Source section above, all of which already
   assume and test this).

## Implementation

### Target files

- `scripts/agent/context.py` — `AppServices.__init__` (lines 134-156).
- `scripts/agent/startup.py` — `StartupOrchestrator._check_services()` (lines 189-292).

### Procedure

1. In `scripts/agent/context.py`, add `runtime_tools: RuntimeToolRegistry | None = None` as a new
   keyword parameter to `AppServices.__init__`, positioned after `gateway` (the existing last
   parameter); set `self.runtime_tools = runtime_tools` in the body, alongside the existing
   `self.gateway` assignment. Add `from shared.runtime_tool_registry import RuntimeToolRegistry` to
   this module's imports (agent-layer importing shared-layer — already legal per
   `.importlinter`'s layer contract; `scripts/agent/services/mcp_tool_discovery.py` already does the
   same import).
2. In `scripts/agent/factory.py::build_agent_context()`, do **not** pass `runtime_tools` to the
   `AppServices(...)` constructor call (lines 434-444) — leave it defaulting to `None` there, since no
   MCP server has been started yet at that point in startup (see Assumption 1). Population happens
   later, in `_check_services()`.
3. In `scripts/agent/startup.py::_check_services()`, add a new numbered step after the existing step 6
   ("Routing drift vs live", lines 255-269) and before step 7 ("RAG consistency", lines 271-282):
   - Import `McpToolDiscoveryService` from `agent.services.mcp_tool_discovery` at module level
     (alongside this file's existing imports).
   - Construct `McpToolDiscoveryService(ctx)`, `await .discover_all()`.
   - Assign `ctx.services_required.runtime_tools = result.registry` (unconditionally — even an empty
     registry, e.g. all servers unreachable, is a valid populated state, not `None`; `None` should mean
     "discovery never ran," not "discovery ran and found nothing").
   - Fold `result.findings` into `pipeline`: for each `StartupCheckOutcome`, call `pipeline.add_fatal`
     or `pipeline.add_warning` per its own `.status` (mirroring how step 3's `readiness` block already
     dispatches per-outcome status, lines 216-225) — do not force everything to one severity.
   - For each entry in `result.unreachable`, call `pipeline.add_warning("mcp_tool_discovery", ...)`
     with a message naming the unreachable server key (servers already reported unreachable by other
     checks may double-report here; this is acceptable, matching this module's own existing
     per-check-independent design).
   - Wrap the whole step in the same `try/except Exception: pipeline.add_skipped(...)` style already
     used by step 6 (lines 256-269), so a discovery failure does not abort the rest of
     `_check_services()` — `runtime_tools` simply stays `None` in that case (do not assign a partial/
     empty registry on exception).

### Method

Plain attribute addition + one new async step inside an existing method — no new class, no new
public API beyond the one new constructor parameter.

### Details

Pseudocode sketch (no production code):

```
# context.py
class AppServices:
    def __init__(
        self,
        ...,
        gateway: RepositoryGateway | None = None,
        runtime_tools: RuntimeToolRegistry | None = None,
    ) -> None:
        ...
        self.gateway = gateway
        self.runtime_tools = runtime_tools
```

```
# startup.py, inside _check_services(), after step 6:
# 6b. MCP tool discovery / RuntimeToolRegistry population
try:
    discovery = await McpToolDiscoveryService(ctx).discover_all()
    ctx.services_required.runtime_tools = discovery.registry
    for outcome in discovery.findings:
        if outcome.status == StartupCheckStatus.FATAL:
            pipeline.add_fatal("mcp_tool_discovery", outcome.message)
        else:
            pipeline.add_warning("mcp_tool_discovery", outcome.message)
    for key in discovery.unreachable:
        pipeline.add_warning("mcp_tool_discovery", f"{key}: unreachable during discovery")
    if not discovery.findings and not discovery.unreachable:
        pipeline.add_ok("mcp_tool_discovery")
except Exception as exc:  # noqa: BLE001
    pipeline.add_skipped("mcp_tool_discovery", f"MCP tool discovery skipped: {exc}")
```

## Validation plan

| Check | Command | Target |
|---|---|---|
| Format/lint | `uv run ruff format scripts/agent/context.py scripts/agent/startup.py && uv run ruff check scripts/agent/context.py scripts/agent/startup.py` | 0 errors |
| Type check | `uv run mypy scripts/agent/context.py scripts/agent/startup.py` | 0 errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations — `agent.context`/`agent.startup` importing `shared.runtime_tool_registry` and `agent.services.mcp_tool_discovery` are both already-legal agent-to-shared / agent-to-agent imports |
| Security | `uv run bandit -r scripts/agent/context.py scripts/agent/startup.py -c pyproject.toml` | 0 high/medium |
| Unit tests | `uv run pytest tests/test_context.py tests/test_startup.py -v` | all pass, including new cases: `runtime_tools` defaults to `None` when omitted; `_check_services()` assigns a populated registry on success; `_check_services()` leaves `runtime_tools` as `None` and adds a skipped finding on discovery failure |
| Downstream unblock | `grep -n "runtime_tools" scripts/agent/context.py` | at least one match — this is the exact gate condition the 7 downstream docs listed in the Source section check for before proceeding |
| Constraint | `ast-grep --pattern 'except: $$$' --lang python scripts/agent/context.py scripts/agent/startup.py` | no bare except |
| Full suite | `uv run pytest -v` | no new failures elsewhere |
