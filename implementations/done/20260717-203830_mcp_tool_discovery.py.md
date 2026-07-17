# Implementation procedure: `scripts/agent/services/mcp_tool_discovery.py`

Source plan: `plans/done/20260717-124907_plan.md` (requirement `requires/20260717_03_require.md`),
Implementation step 2.

## Goal

Create `scripts/agent/services/mcp_tool_discovery.py`, a new async service that iterates
`ctx.cfg.mcp.mcp_servers`, fetches each HTTP-transport server's `/v1/tools`, validates the response
shape (richer than today's name-only check), normalizes every valid entry into a
`shared.runtime_tool.RuntimeTool` instance, detects cross-server duplicate tool names, and returns a
built `shared.runtime_tool_registry.RuntimeToolRegistry` plus a list of findings the startup pipeline
can report. This captures the tool data that today's `repl_health.py` fetch discards (per the plan's
Assumption 1) — but does not itself wire the result into `startup.py`/`AppServices`.

## Scope

**In scope**
- New file `scripts/agent/services/mcp_tool_discovery.py` only.
- `McpToolDiscoveryService` class (mirrors `agent/services/mcp_status.py`'s `McpStatusService` shape):
  fetch, validate, normalize, dedupe, and return a `DiscoveryResult` (registry + findings + unreachable
  server keys).

**Out of scope (tracked separately / already covered)**
- Wiring the discovery call into `scripts/agent/startup.py`'s `run()` sequence, and populating
  `AppServices`/`AgentContext`'s registry field from `scripts/agent/factory.py`/`scripts/agent/context.py`
  — per this workflow's filename-match convention, implementation docs already exist under
  `implementations/done/` for `context.py`, `startup.py`, and `test_startup.py` (confirmed by `ls`; the
  sibling requirement-02 doc `implementations/20260717-203121_runtime_tool.py.md` explicitly notes and
  relies on this same convention for `context.py`), so those files are treated as already-covered and are
  **not** touched by this doc.
- `scripts/agent/repl_health.py` — no change (plan's Design section recommends keeping the existing
  drift-check fetch independent; not this doc's concern either way).
- `scripts/shared/mcp_config.py` — no change (read-only dependency).
- `deploy/deploy.sh` — a doc already exists (`implementations/20260717-203339_deploy.sh.md`), treated as
  already covered per the filename-match convention.
- `scripts/shared/runtime_tool.py` / `scripts/shared/runtime_tool_registry.py` themselves — these are
  **prerequisite dependencies of this module, not yet present in the real source tree** (confirmed via
  `grep -rl "class RuntimeTool" scripts/` — no hits). Their construction is tracked by
  `implementations/20260717-203121_runtime_tool.py.md` and
  `implementations/20260717-203200_runtime_tool_registry.py.md`. This doc assumes those two files exist
  with the shape described in those docs by the time `mcp_tool_discovery.py` is actually implemented;
  if not, implement them first (or note the blocking dependency).

## Assumptions

1. **HTTP-transport filter and fetch pattern mirror `repl_health.py`'s existing
   `_collect_server_tool_names()`** (`scripts/agent/repl_health.py:161-259`, esp. lines 181-184's filter
   `srv_cfg.transport == TransportType.HTTP and srv_cfg.url` and lines 232-258's fetch/error handling):
   `await ctx.services_required.http.get(f"{srv_cfg.url}/v1/tools", timeout=5.0)`, `HTTPStatus.OK` check,
   `resp.json()` wrapped in `try/except ValueError`, and `except (httpx.HTTPError, OSError)` around the
   whole per-server call. This module duplicates that pattern independently (per the plan's Unknowns
   table, which recommends *not* unifying with `repl_health.py` for this pass) rather than importing or
   refactoring `repl_health.py`.
2. **The existing `_validate_tools_response()` (`repl_health.py:150-158`) only checks `name`** and
   discards everything else (confirmed: returns `list[str]`, not the full entry). This module cannot
   reuse it as-is — the plan's Design section requires validating `description` (present) and
   `inputSchema`/`input_schema` (object-shaped) as well, plus optionally type-checking `status`/
   `is_write`/`requires_serial`/`resource_scope` if present. This module implements its own, richer
   per-entry validator that returns the full entry (not just the name) on success.
3. **`RuntimeTool` construction goes through `shared.runtime_tool.build_runtime_tool(...)`**, not the
   frozen dataclass constructor directly (per `implementations/20260717-203121_runtime_tool.py.md`'s
   Procedure step 4) — this applies the safe-default rules for `is_write`/`requires_serial`/
   `agent_safety_tier`/`requires_approval`/`enabled_for_llm` when a server's tool entry omits them.
   `server_key` is the dict key from `ctx.cfg.mcp.mcp_servers.items()` (not a field read off the entry
   itself), matching `build_runtime_tool`'s `server_key` parameter and consistent with
   `scripts/mcp_servers/server.py:128-136`'s `list_tools_with_server_key()` convention cited in that doc.
4. **Registry construction goes through `shared.runtime_tool_registry.RuntimeToolRegistry.__init__(tools:
   dict[str, RuntimeTool] | None = None)`** (per `implementations/20260717-203200_runtime_tool_registry.py.md`),
   built from a `{name: RuntimeTool}` dict assembled by this module after dedup.
5. **Duplicate-name severity gates on `ctx.cfg.mcp.security_profile == SecurityProfile.PRODUCTION`**
   (`scripts/shared/mcp_config.py:38-42`'s `SecurityProfile` enum), per the plan's Assumption 5 and
   Design section. This doc makes the concrete decision the plan explicitly deferred ("exclude vs.
   first-wins-with-warning"): **exclude** the duplicate tool from the registry entirely in both
   production and local mode (the safer of the two options named in the plan's Design section) —
   the only difference between profiles is the finding's severity (`FATAL` in production, `WARNING` in
   local). This decision must be stated verbatim in the module's docstring, per the plan's Risk
   mitigation ("document whichever choice is made explicitly ... rather than leaving it implicit").
6. **Findings are returned as `agent.shared.health_models.StartupCheckOutcome` instances** (already
   defined at `scripts/agent/shared/health_models.py:71-77`, with `StartupCheckStatus` at lines 64-68 and
   `StartupValidationResult.add_fatal`/`add_warning` at lines 83-91) rather than inventing a parallel
   findings type — this module returns a `list[StartupCheckOutcome]` that a (separately-tracked) caller
   in `startup.py` can fold into its `StartupValidationResult` pipeline via `pipeline.outcomes.extend(...)`
   or by re-emitting each outcome through `add_fatal`/`add_warning`. This module itself never touches a
   `StartupValidationResult` instance directly (it has no reference to the pipeline; it just returns data).
7. **Structural convention mirrors `scripts/agent/services/mcp_status.py`** (per plan's Assumption 8): a
   small class taking `ctx: AgentContext` in `__init__`, an `async def discover_all(...)`  top-level
   method (analogous to `McpStatusService.probe_all()` at `mcp_status.py:57-65`), and private
   `_fetch_server_tools()`/`_validate_and_normalize_entry()` per-item helpers (analogous to
   `_probe_single_server()`/`_get_http_status()`).
8. **`McpServerConfig`'s fields are sufficient** (`scripts/shared/mcp_config.py:46-64`): `transport`,
   `url`, `key` (line 61, the same value as the dict key) are all that's needed for iteration; no change
   to `mcp_config.py` required, confirmed by direct read.

## Implementation

### Target file

`scripts/agent/services/mcp_tool_discovery.py` (new).

### Procedure

1. Module docstring: state this service discovers live MCP tools at startup and captures full schemas
   (unlike `repl_health.py`'s existing name-only fetch); state explicitly that this is an independent
   HTTP round-trip from `repl_health.py`'s drift-check fetch (not unified, per the plan's Unknowns
   recommendation) and that the two *could* theoretically observe different tool sets if servers change
   state between the two calls (known, accepted limitation — document per the plan's Risks section);
   state the concrete duplicate-handling decision from Assumption 5 (exclude in both profiles, severity
   differs).
2. Import `RuntimeTool`, `build_runtime_tool` from `shared.runtime_tool`; `RuntimeToolRegistry` from
   `shared.runtime_tool_registry`; `StartupCheckOutcome`, `StartupCheckStatus` from
   `agent.shared.health_models`; `McpServerConfig`, `TransportType` from `shared.mcp_config`; `httpx`;
   `HTTPStatus` from `http`; `AgentContext` under `TYPE_CHECKING` (mirrors `mcp_status.py:23-24`).
3. Define `@dataclass(frozen=True) class DiscoveryResult`: `registry: RuntimeToolRegistry`,
   `findings: list[StartupCheckOutcome]`, `unreachable: list[str]`.
4. Define `class McpToolDiscoveryService`: `__init__(self, ctx: AgentContext) -> None: self._ctx = ctx`.
5. `async def discover_all(self) -> DiscoveryResult`: iterate `self._ctx.cfg.mcp.mcp_servers.items()`,
   skip non-HTTP or empty-`url` servers (mirror `repl_health.py:181-184`); for each remaining server call
   `await self._fetch_server_tools(key, cfg)`; accumulate `(server_key, server_url, raw_entry)` tuples for
   every entry that passed per-entry validation, plus findings for entries/servers that failed; after all
   servers are fetched, call `self._dedupe_and_build(entries)` to get `(registry, dup_findings)`; return
   `DiscoveryResult(registry=registry, findings=[*fetch_findings, *entry_findings, *dup_findings],
   unreachable=unreachable_keys)`.
6. `async def _fetch_server_tools(self, key: str, cfg: McpServerConfig) -> tuple[list[tuple[str, str, dict]],
   StartupCheckOutcome | None]`: same try/except flow as `repl_health.py:232-258` (JSON parse failure,
   non-200 status, `httpx.HTTPError`/`OSError`) — on any failure, return `([], StartupCheckOutcome(...))`
   with `StartupCheckStatus.WARNING` (an unreachable/malformed server is a warning, not fatal — consistent
   with today's `repl_health.py` behavior of logging a warning and continuing, not raising); on success,
   validate the top-level shape (`{"tools": [...]}`, `tools` is a list) then delegate each entry to
   `self._validate_and_normalize_entry(key, cfg.url, entry)`.
7. `def _validate_and_normalize_entry(self, server_key: str, server_url: str, entry: object) -> tuple[dict
   | None, StartupCheckOutcome | None]`: validate per the plan's Design section rules (a) entry is a dict,
   (b) non-empty string `name`, (c) `description` present (str; empty-string allowed but must be a str),
   (d) `inputSchema`/`input_schema` is a dict, (e) optional `status`/`is_write`/`requires_serial`/
   `resource_scope` type-checked only if present; on any failure return `(None,
   StartupCheckOutcome(source="mcp_tool_discovery", status=StartupCheckStatus.WARNING, message=...))`
   (schema errors are per-tool warnings, not fatal — the plan's Design section does not specify fatal
   severity for shape errors, only for duplicates); on success return the raw entry dict unchanged
   (normalization into `RuntimeTool` happens in the caller, once `server_key`/`server_url` are attached).
8. `def _dedupe_and_build(self, entries: list[tuple[str, str, dict]]) -> tuple[RuntimeToolRegistry,
   list[StartupCheckOutcome]]`: group entries by `entry["name"]`; for names with exactly one
   `(server_key, server_url, entry)`, build one `RuntimeTool` via `build_runtime_tool(name=..., server_key=
   ..., server_url=..., description=..., input_schema=..., raw_definition=entry, status=entry.get(
   "status", "active"), is_write=entry.get("is_write"), requires_serial=entry.get("requires_serial"))`;
   for names with >1 distinct `server_key`, **exclude all of them from the registry** (per Assumption 5)
   and emit one finding per duplicate name: `StartupCheckStatus.FATAL` if
   `self._ctx.cfg.mcp.security_profile == SecurityProfile.PRODUCTION` else `StartupCheckStatus.WARNING`,
   message listing the tool name and the conflicting server keys; return
   `RuntimeToolRegistry(tools={t.name: t for t in built}), findings`.

### Method

Plain class wrapping `ctx` (mirrors `McpStatusService`), plus one module-level frozen result dataclass
(`DiscoveryResult`) and reuse of the existing `StartupCheckOutcome`/`StartupCheckStatus` types. No
`Protocol`/`ABC` — single concrete implementation, consistent with the "Method" sections of the sibling
`runtime_tool.py`/`runtime_tool_registry.py` docs.

### Details

Signatures (pseudocode — no production code):

```
@dataclass(frozen=True)
class DiscoveryResult:
    registry: RuntimeToolRegistry
    findings: list[StartupCheckOutcome]
    unreachable: list[str]


class McpToolDiscoveryService:
    def __init__(self, ctx: AgentContext) -> None: ...
        # self._ctx = ctx

    async def discover_all(self) -> DiscoveryResult: ...
        # entries: list[tuple[str, str, dict]] = []
        # findings: list[StartupCheckOutcome] = []
        # unreachable: list[str] = []
        # for key, cfg in self._ctx.cfg.mcp.mcp_servers.items():
        #     if cfg.transport != TransportType.HTTP or not cfg.url:
        #         continue
        #     fetched, err = await self._fetch_server_tools(key, cfg)
        #     if err is not None:
        #         findings.append(err)
        #         unreachable.append(key)
        #     entries.extend(fetched)
        # registry, dup_findings = self._dedupe_and_build(entries)
        # return DiscoveryResult(registry, [*findings, *dup_findings], unreachable)

    async def _fetch_server_tools(
        self, key: str, cfg: McpServerConfig
    ) -> tuple[list[tuple[str, str, dict]], StartupCheckOutcome | None]: ...
        # resp = await self._ctx.services_required.http.get(f"{cfg.url}/v1/tools", timeout=5.0)
        # (parse JSON, check HTTPStatus.OK, validate top-level {"tools": [...]} shape,
        #  per-entry validate via _validate_and_normalize_entry, catch httpx.HTTPError/OSError/ValueError)

    def _validate_and_normalize_entry(
        self, server_key: str, server_url: str, entry: object
    ) -> tuple[dict[str, object] | None, StartupCheckOutcome | None]: ...

    def _dedupe_and_build(
        self, entries: list[tuple[str, str, dict[str, object]]]
    ) -> tuple[RuntimeToolRegistry, list[StartupCheckOutcome]]: ...
```

## Validation plan

| Check | Command | Target |
|---|---|---|
| Format/lint | `uv run ruff format scripts/agent/services/mcp_tool_discovery.py && uv run ruff check scripts/agent/services/mcp_tool_discovery.py` | 0 errors |
| Type check | `uv run mypy scripts/agent/services/mcp_tool_discovery.py` | 0 errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations — agent layer may import shared, confirmed by `.importlinter` |
| Security | `uv run bandit -r scripts/agent/services/mcp_tool_discovery.py -c pyproject.toml` | 0 high/medium |
| Unit tests | `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -v` | all pass (see paired test doc) |
| Constraint | `ast-grep --pattern 'except: $$$' --lang python scripts/agent/services/mcp_tool_discovery.py` | no bare except |
| Dependency check | manual: confirm `shared/runtime_tool.py` and `shared/runtime_tool_registry.py` exist with the shape described in `implementations/20260717-203121_runtime_tool.py.md` / `implementations/20260717-203200_runtime_tool_registry.py.md` before implementing this file | both present |
