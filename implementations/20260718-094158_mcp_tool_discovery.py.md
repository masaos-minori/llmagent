# Implementation procedure: `scripts/agent/services/mcp_tool_discovery.py` (disabled-tool diagnostics variant)

Source plan: `plans/20260717-175327_plan.md` ("RuntimeToolRegistry — represent disabled MCP tools
without exposing them to the LLM", requirement 17), Implementation step 4.

## Goal

Create `scripts/agent/services/mcp_tool_discovery.py`, a new `McpToolDiscoveryService` that fetches
`/v1/tools` from every configured HTTP MCP server, reads each tool's `enabled`/`disabled_reason`
fields (once sibling requirement 15 adds them server-side — see Risks), defaults them to
`enabled=True, disabled_reason=""` when absent (backward compatible with not-yet-updated servers),
and populates a `RuntimeToolRegistry` (this plan's 6-field variant,
`implementations/20260718-094055_runtime_tool_registry.py.md`) instance with one `RuntimeTool`
per discovered tool.

**Filename note**: four other docs already target `scripts/agent/services/mcp_tool_discovery.py` —
`implementations/20260717-203830_mcp_tool_discovery.py.md` (base design, requirement 03,
`plans/done/20260717-124907_plan.md`), `implementations/20260717-224511_mcp_tool_discovery.py.md`
(consolidation extension, `plans/20260717-130506_plan.md`),
`implementations/20260718-084109_mcp_tool_discovery.py.md` (schema_version tolerance,
`plans/20260717-131019_plan.md`), and `implementations/20260718-084819_mcp_tool_discovery.py.md`
(capabilities tolerance, `plans/20260717-131133_plan.md`). All four build the *other* 13-field
`RuntimeTool`/9-method `RuntimeToolRegistry` design (routing/scheduling/policy metadata), a different
feature from this requirement's disabled-tool-visibility discovery. Checked each Goal directly —
none describes reading `enabled`/`disabled_reason` for LLM-visibility filtering the way this
requirement does. This is the same cross-plan physical-file collision already flagged in the paired
`runtime_tool.py`/`runtime_tool_registry.py` docs for this plan; not a stale match to skip against.

## Scope

**In scope**
- New file `scripts/agent/services/mcp_tool_discovery.py` — `McpToolDiscoveryService.discover()`
  only, built against this plan's 6-field `RuntimeTool`/`RuntimeToolRegistry`.

**Out of scope**
- Implementing the MCP-server-side `enabled`/`disabled_reason` computation (sibling requirement
  15's job, `plans/20260717-174024_plan.md`, target files `scripts/mcp_servers/file/*.py`,
  `scripts/mcp_servers/git/server.py` — confirmed via that requirement's own already-written
  implementation docs, e.g. `implementations/20260718-090830_full_validation_pass_tools_enabled_disabled_reason.md`,
  that its target files are the 6 listed there, none of which is this file).
- Reusing/absorbing `check_routing_drift_vs_live()` or any `ToolRegistry`-drift-detection logic
  from `scripts/agent/repl_health.py` (that consolidation is the *other* lineage's requirement, per
  `implementations/20260717-224511_mcp_tool_discovery.py.md`'s Goal) — this doc's discovery service
  is deliberately narrow: fetch, read enabled/disabled_reason, populate registry, nothing else.

## Assumptions

- Real current `/v1/tools`-fetch pattern to reuse: `scripts/agent/services/mcp_status.py:61-65`
  (`McpStatusService.probe_all()`) opens one `httpx.AsyncClient(timeout=5.0)` and loops
  `ctx.cfg.mcp.mcp_servers.items()`; `scripts/agent/repl_health.py:161-212`
  (`_collect_server_tool_names()`) and `:215-259` (`_collect_server_tool_names_per_server()`) show
  the actual `/v1/tools` GET + JSON-parse + per-server error handling this service should mirror:
  `await ctx.services_required.http.get(f"{srv_cfg.url}/v1/tools", timeout=5.0)`, checking
  `resp.status_code == HTTPStatus.OK`, catching `(httpx.HTTPError, OSError)` per server (never
  aborting the whole discovery pass on one server's failure), and logging
  `WARNING "{key} unreachable at {url}/v1/tools: ..."` on failure. This service reuses
  `ctx.services_required.http` (the shared `httpx.AsyncClient`), the same pattern
  `_collect_server_tool_names_per_server` already uses, rather than opening a second ad-hoc client
  like `McpStatusService` does — either is acceptable; reusing the shared client avoids a second
  connection pool.
- Real current `/v1/tools` response shape per tool (confirmed via
  `scripts/mcp_servers/server.py:128-136`'s `list_tools_with_server_key()`): each entry has `name`,
  `description`, `inputSchema`, `server_key` (added by that method), and whatever the server's own
  `TOOL_LIST` dict carries verbatim — today that is `requires_config: bool` (not yet renamed to
  `config_dependent` — confirmed still `"requires_config"` at
  `scripts/mcp_servers/file/read_tools.py:54` and `scripts/mcp_servers/git/tools.py:30`; the rename
  to `config_dependent` is sibling requirement 16's/13602's job, tracked separately). **No** `enabled`
  or `disabled_reason` key exists in any real `/v1/tools` response today — confirmed via
  `grep -rn "disabled_reason" .` returning zero matches repo-wide (per this plan's own Unknowns
  table). This service's per-tool parsing must therefore read `tool.get("enabled", True)` and
  `tool.get("disabled_reason", "")` defensively, not assume the keys exist.
- `config_dependent` on the resulting `RuntimeTool` is read from the same live tool dict as
  `tool.get("config_dependent", tool.get("requires_config", False))` — tolerating both the old and
  new key name during the transition, per this plan's Design step 3 ("trusts the server's `enabled`
  bit rather than re-deriving it").
- Only HTTP-transport servers are probed (mirrors `_collect_server_tool_names`'s
  `if srv_cfg.transport == TransportType.HTTP` guard at `repl_health.py:182`); non-HTTP servers
  (e.g. stdio) are skipped, consistent with existing discovery/probing code.

## Implementation

### Target file

`scripts/agent/services/mcp_tool_discovery.py` (new).

### Procedure

1. Module docstring: state this service's narrow purpose (populate a disabled-tool-aware
   `RuntimeToolRegistry` for requirement 17); state it does not perform drift detection or
   `ToolRegistry` validation (that stays in `repl_health.py`); state the backward-compat defaulting
   behavior for servers that predate requirement 15's `enabled`/`disabled_reason` rollout; flag the
   physical-filename collision with the other `mcp_tool_discovery.py` design lineage (requirement
   03 and its extensions) so a future integrator does not merge the two service implementations.
2. Import `RuntimeTool` from `shared.runtime_tool`, `RuntimeToolRegistry` from
   `shared.runtime_tool_registry`, `TransportType` from `shared.mcp_config` (already used the same
   way in `repl_health.py`), `httpx`, `HTTPStatus` from `http`.
3. Define `class McpToolDiscoveryService` with `__init__(self, ctx: AgentContext) -> None` (same
   constructor shape as `McpStatusService`).
4. Implement `async def discover(self) -> RuntimeToolRegistry` — loops configured HTTP servers,
   fetches `/v1/tools`, and for each valid entry builds one `RuntimeTool` and registers it. On a
   per-server fetch/parse failure, log a `WARNING` (mirroring `repl_health.py`'s message format) and
   skip that server's tools entirely for this discovery pass (do not add partial/placeholder
   entries for an unreachable server — a tool this service never saw is simply absent from the
   registry, not silently marked as "disabled" for a reason it can't attribute).
5. Implement a private `_build_runtime_tool(self, server_key: str, tool: dict[str, object]) ->
   RuntimeTool | None` that validates the entry has a non-empty `name` (returns `None` and logs a
   `WARNING` on a malformed entry, mirroring `_validate_tools_response`'s validation style referenced
   in `repl_health.py`), then reads `enabled`/`disabled_reason`/`config_dependent` per the
   Assumptions defaulting rules, and computes `enabled_for_llm` via
   `shared.runtime_tool.compute_enabled_for_llm(enabled, policy_check=None, name=tool["name"])`
   (no agent-policy predicate at discovery time — policy filtering, if any, happens downstream in
   the consumer, per this plan's Design step 4 risk note about deferring the exact merge strategy).

### Method

Plain async service class (no `Protocol`/`ABC`), parallel in shape to `McpStatusService` — a
constructor taking `ctx`, one public async entry point, private helpers for per-server/per-tool
work. Uses the shared `ctx.services_required.http` client, not a locally-opened one.

### Details

Pseudocode sketch (no production code):

```
class McpToolDiscoveryService:
    def __init__(self, ctx: AgentContext) -> None: ...
        # self._ctx = ctx

    async def discover(self) -> RuntimeToolRegistry:
        # registry = RuntimeToolRegistry()
        # ctx = self._ctx
        # for key, srv_cfg in ctx.cfg.mcp.mcp_servers.items():
        #     if srv_cfg.transport != TransportType.HTTP or not srv_cfg.url:
        #         continue
        #     try:
        #         resp = await ctx.services_required.http.get(f"{srv_cfg.url}/v1/tools", timeout=5.0)
        #     except (httpx.HTTPError, OSError) as e:
        #         logger.warning("%s unreachable at %s/v1/tools: %s", key, srv_cfg.url, e)
        #         continue
        #     if resp.status_code != HTTPStatus.OK:
        #         logger.warning("%s /v1/tools returned HTTP %s", key, resp.status_code)
        #         continue
        #     try:
        #         body = resp.json()
        #     except ValueError as e:
        #         logger.warning("%s: /v1/tools response is not valid JSON: %s", key, e)
        #         continue
        #     tools = body.get("tools", body) if isinstance(body, dict) else body
        #     for raw_tool in tools if isinstance(tools, list) else []:
        #         rt = self._build_runtime_tool(key, raw_tool)
        #         if rt is not None:
        #             registry.register(rt)
        # return registry

    def _build_runtime_tool(self, server_key: str, tool: dict[str, object]) -> RuntimeTool | None:
        # name = tool.get("name")
        # if not isinstance(name, str) or not name:
        #     logger.warning("%s: /v1/tools entry missing name: %r", server_key, tool)
        #     return None
        # enabled = bool(tool.get("enabled", True))
        # disabled_reason = str(tool.get("disabled_reason", "") or "")
        # config_dependent = bool(tool.get("config_dependent", tool.get("requires_config", False)))
        # enabled_for_llm = compute_enabled_for_llm(enabled, None, name)
        # return RuntimeTool(
        #     name=name, server_key=server_key, config_dependent=config_dependent,
        #     enabled=enabled, disabled_reason=disabled_reason, enabled_for_llm=enabled_for_llm,
        # )
```

Note: the exact top-level `/v1/tools` response shape (bare list vs. `{"tools": [...]}` envelope) is
not fully pinned down by this plan; `scripts/mcp_servers/server.py:128-136`'s
`list_tools_with_server_key()` returns a bare `list[dict]`, which is what current servers actually
serve — the `body.get("tools", body)` fallback above tolerates either shape defensively without
assuming an envelope exists.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Format/lint | `uv run ruff format scripts/agent/services/mcp_tool_discovery.py && uv run ruff check scripts/agent/services/mcp_tool_discovery.py` | 0 errors |
| Type check | `uv run mypy scripts/agent/services/mcp_tool_discovery.py` | 0 errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations — confirms `agent` layer may import `shared` freely |
| Security | `uv run bandit -r scripts/agent/services/mcp_tool_discovery.py -c pyproject.toml` | 0 high/medium |
| Unit tests | `uv run pytest tests/test_mcp_tool_discovery.py -v` | all pass (see paired test doc) |
| Constraint | `ast-grep --pattern 'except: $$$' --lang python scripts/agent/services/mcp_tool_discovery.py` | no bare except |
