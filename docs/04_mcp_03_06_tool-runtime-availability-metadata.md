---
title: "Tool Runtime Availability Metadata: config_dependent, enabled, disabled_reason"
category: mcp
tags:
  - mcp
  - routing
  - tool-registry
  - runtime-tool-registry
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_03_02_tool-registry.md
  - 04_mcp_04_01_web-search-file-read-github.md
  - 04_mcp_04_02_file-write-file-delete-shell.md
  - 04_mcp_04_03_rag-pipeline-and-cicd.md
  - 04_mcp_04_05_git.md
  - 05_agent_08_04_configuration-mcp-approval-obs.md
  - 04_mcp_90_inconsistencies_and_known_issues.md
---

# Tool Runtime Availability Metadata: `config_dependent`, `enabled`, `disabled_reason`

> **Implementation status:** `config_dependent` is adopted across `git`, `file_read`/`file_write`/`file_delete`, `github`, and `web_search` (`browser_fetch`). `enabled`/`disabled_reason` fields are now wired into RuntimeToolRegistry via `_dedupe_and_build()` in `mcp_tool_discovery.py` — see `04_mcp_03_01_dispatch-and-routing.md` for details.

## 0. Concept distinctions

Tool existence, discovery, LLM visibility, routing ownership, static availability, dynamic health, approval state, and execution eligibility are different concepts. The word "enabled" alone MUST NOT be used without identifying which of these it refers to.

| Concept | Meaning |
|---|---|
| Defined | The tool exists in an MCP server implementation |
| Discoverable | The tool is returned by the server's `/v1/tools` |
| Owned | `RuntimeToolRegistry` knows which server owns the tool |
| LLM-visible | The tool is included in the function definitions given to the LLM (`RuntimeToolRegistry.llm_tool_definitions()`, gated on `enabled_for_llm`) |
| Statically available | Current configuration/policy permits considering the tool for execution |
| Dynamically available | The owning server is currently healthy enough to attempt execution (`McpServerHealthRegistry`) |
| Routable | `RuntimeToolRegistry`/`ToolRouteResolver` can resolve the tool to exactly one owning server |
| Approved | The current invocation has satisfied its approval requirement (`agent/tool_policy.py`, `tool_approval.py` — a separate subsystem, see section 6a) |
| Executable | All of the above, plus argument validation, currently permit this specific call |

These MUST NOT be treated as interchangeable. In particular: a tool can be **LLM-visible yet not dynamically available** (server down), **statically disabled yet dynamically healthy** (config gate), or **known but not owned** (duplicate ownership, section 6).

## 1. `config_dependent` (static)

Each server's `TOOL_LIST` includes a per-tool boolean field `config_dependent` (direct rename of `requires_config` with identical boolean semantics, no compatibility shim). `requires_config` is removed; any remaining doc/code reference to it describes obsolete behavior. `web_search-mcp`'s `browser_fetch` tool is the first to adopt `config_dependent: True`.

## 2. `enabled` / `disabled_reason` (runtime, request-time-computed)

Added to each tool dict in the live `/v1/tools` response body, computed per-request from the owning server's current config state (`_cfg`). Invariant: `enabled=True` <-> `disabled_reason == ""`; `enabled=False` <-> `disabled_reason` is a non-empty standard string (enumerated in section 3).

## 3. Standard `disabled_reason` values

| `disabled_reason` value | Applies to | Status |
|---|---|---|
| `"allowed_dirs is empty"` | file read/write/delete servers | active |
| `"allowed_repo_paths is empty"` | git (takes precedence over `read_only`) | active |
| `"read_only=true"` | git write tools only, when allowlist is non-empty | active |
| `"command_allowlist is empty"` | shell | reserved — not yet implemented (requirement 15 scopes shell/cicd out) |
| `"workflow_allowlist is empty"` | cicd | reserved — not yet implemented (requirement 15 scopes shell/cicd out) |

**Implemented:** `git`, `file_read`/`file_write`/`file_delete`, `github`, and `web_search` each compute `enabled`/`disabled_reason` per tool in their own `/v1/tools` handler. See [git-mcp availability metadata](./04_mcp_04_05_git.md#availability-metadata) for git's specific precedence rules. `web_search` (`browser_fetch`) also implements this — an earlier version of this document and of Known Issue MCP-002 stated web-search lacked it; that was stale and has been corrected here.

**Not implemented:** `rag_pipeline`, `cicd`, `mdq`, and `shell` route `TOOL_LIST` straight to `mcp_servers/server.py::build_tools_response()` with no per-tool `enabled`/`disabled_reason` computation — their tool entries carry neither key.

## 4. `/v1/tools` behavioral rules

Always returns every implemented tool; disabled tools are never omitted from the response. Example JSON response block, one enabled + one disabled tool side by side:

```json
{
  "tools": [
    {
      "name": "git_status",
      "config_dependent": true,
      "enabled": true,
      "disabled_reason": ""
    },
    {
      "name": "git_push",
      "config_dependent": true,
      "enabled": false,
      "disabled_reason": "read_only=true"
    }
  ]
}
```

## /v1/tools as RuntimeToolRegistry Source

The `/v1/tools` endpoint is **not just an informational endpoint** — it is the primary source used to construct `RuntimeToolRegistry`.

When a client calls `/v1/tools`, the MCP server returns the current state of all tools including their availability metadata. This response is consumed by the agent's runtime to populate `RuntimeToolRegistry`, which determines:
- Which tools are available for routing
- Current tool status (enabled/disabled)
- Tool configuration dependencies

`RuntimeToolRegistry` is populated once at agent startup via `McpToolDiscoveryService.discover_all()`; neither `/reload` nor any live health-check path triggers a rebuild of the registry from a fresh `/v1/tools` fetch.

## Reload vs. restart for RuntimeToolRegistry

- `/reload` (`_ConfigMixin._cmd_reload()`) calls `ConfigReloadService.apply_config_dict()`, which calls `RuntimeToolRegistry.apply_policy()`.
- `apply_policy()` only updates policy-derived fields (`agent_safety_tier`, `requires_approval`, `enabled_for_llm`) and does not touch `raw_definition`, `disabled_reason`, or `status`.
- A full agent process restart is required for the registry's discovery-derived state (including `/mcp status`'s `DISABLED_REASON` column) to reflect config changes.
- Per-server config files (e.g. `allowed_dirs` in `file_read_mcp_server.toml`) require restarting that MCP server process itself, separate from the agent restart above.

`docs/04_mcp_06_17_local-to-production-auth-migration.md`'s [`Difference between /reload and full restart`](04_mcp_06_17_local-to-production-auth-migration.md#difference-between-reload-and-full-restart) deals with restart requirements for `[mcp_servers.*]` connection definitions, which is outside the scope of the broader `RuntimeToolRegistry` availability snapshot requirements discussed in this section.

## Field Mapping: /v1/tools ↔ RuntimeTool

The following table shows how /v1/tools response fields map to RuntimeTool fields:

| /v1/tools field | RuntimeTool field | Notes |
|---|---|---|
| `enabled` | `enabled_for_llm` | Both indicate LLM visibility; values should match |
| `disabled_reason` | *(not a first-class field)* | Currently not stored in RuntimeTool; deferred future task |

### Key points

- `enabled` and `enabled_for_llm` serve the same purpose: indicating whether the tool is visible to the LLM
- `disabled_reason` from /v1/tools is **not** currently a first-class RuntimeTool field
- The reason a tool is disabled is determined by the source of truth (config, health status, etc.) rather than being carried forward in RuntimeTool
- Future work will add `RuntimeTool.disabled_reason` as a first-class field to close this gap

## 5. Dispatch rule

Disabled tools must be rejected by `/v1/call_tool` before reaching the dispatch table (server-side gate). Reference requirement 16's plan (`plans/20260717-174848_plan.md`) for the exact response shape: `CallToolResponse(result="Tool disabled: <reason>", is_error=True)`.

## 6. RuntimeToolRegistry (agent-side)

Disabled tools are tracked for diagnostics (`enabled_for_llm` derived field) but never included in the LLM-facing tool list and never dispatchable through the registry's own routing path. Four states: discovered / MCP-server-enabled / agent-policy-enabled / LLM-visible. Reference requirement 17's plan (`plans/20260717-175327_plan.md`) — per the post-review decision, this section describes the disabled-visibility fields/methods as an extension of the adopted 13-field/9-method `RuntimeTool`/`RuntimeToolRegistry` lineage (`implementations/20260717-203121_runtime_tool.py.md`, `implementations/20260717-203200_runtime_tool_registry.py.md`, `implementations/20260718-084710_runtime_tool.py.md`), not as a separate 6-field class.

`RuntimeToolRegistry.diagnostics()` (consumed by `/mcp status`'s `DISABLED_REASON` column, see `cmd_mcp.py`) computes each row's `disabled_reason` by first checking `tool.raw_definition.get("disabled_reason")` — the raw string a server actually sent in its `/v1/tools` entry, if present and non-empty — and only falls back to a `tool.status`-derived value (`""` when `status == "active"`, otherwise the status string) when the raw entry carried no such key. This lets `/mcp status` surface a server's real audit-trail reason once servers adopt the `enabled`/`disabled_reason` schema from section 2, while preserving the pre-existing status-derived value for every tool discovered today, none of which yet sends `disabled_reason` (see section 1's implementation-status callout).

## 6a. Static availability vs. dynamic health (distinct, unintegrated boundary)

`McpToolDiscoveryService` (static, computed once at startup) and `McpServerHealthRegistry`/`ToolExecutor` (dynamic, updated continuously from live call outcomes) own different concerns and MUST NOT be conflated:

- **Static / `RuntimeToolRegistry` (McpToolDiscoveryService.discover_all(), startup-only):** tool ownership, schema, scheduling metadata, and LLM-visibility eligibility (`enabled_for_llm`). A server that fails discovery entirely has all of its tools excluded from the registry via `_is_excluded_server()`. Note: the constructor also accepts a `degraded_servers` set for a softer exclusion tier, but `discover_all()` never populates it — it is a dead parameter today, not a second implemented tier.
- **Dynamic / `McpServerHealthRegistry` + `ToolExecutor` (continuous, per-call):** server reachability, circuit-breaker state (CLOSED/OPEN/HALF_OPEN), and trial-recovery behavior. This layer does not affect `RuntimeToolRegistry`, LLM visibility, or routing — a tool stays LLM-visible and routable while its owning server is circuit-open; `ToolExecutor.execute()` simply returns an error at call time instead.

A tool can be statically enabled while its server is temporarily down (dynamic-health failure at call time), and a tool can be statically disabled while its server is otherwise healthy (config gate, e.g. `read_only=true`). Discovery snapshots taken at startup MUST NOT be treated as permanent runtime health truth — only restart triggers rediscovery (Reload vs. restart above).

## 6b. Approval is not a disabled state

Approval requirement (`RuntimeTool.requires_approval`) is tracked as a distinct concept from static/dynamic availability, and in the current implementation is tracked so loosely that no code path reads it back (`requires_approval` has write sites in `runtime_tool.py`/`runtime_tool_registry.py` but no read site anywhere in the codebase — Explicit in code, confirmed by repository-wide search). Actual approval-requirement decisions are made by an entirely separate subsystem, `agent/tool_policy.py::classify_risk()` and `agent/tool_approval.py`, operating on a `PreparedToolCall` that has already passed the registry/routing phase. A tool pending approval is not represented as "disabled" anywhere in `RuntimeToolRegistry` — approval-required tools remain LLM-visible and routable; only the approval subsystem gates execution.

## Wiring reference

For end-to-end tracing of how `disabled_reason` flows into `/mcp status`, see also:
- `docs/04_mcp_03_02_tool-registry.md` — `RuntimeToolRegistry` module overview and discovery wiring.
- `docs/05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md` — `/mcp status` command reference (general health/status view; does not yet detail the per-tool diagnostics table).

## `include_disabled` and `disabled_code`: implemented but unreachable

**Note:** Top-level `capabilities` (on the response body, not per-tool) is also deferred unless verified otherwise. If any MCP server returns top-level `capabilities` in its `/v1/tools` response, this should be updated to reflect current implementation status.

Both options below have real parameters in `mcp_servers/server.py::build_tools_response()` — `include_disabled: bool = False` and `disabled_code: str | None = None` — but every route handler across all servers calls `build_tools_response()` (or the servers that skip it entirely) without ever passing these arguments, and none of the `list_tools()` handlers declare a query parameter for either. The parameters exist in code but have no reachable caller; `/v1/tools` therefore always returns every tool unconditionally today, matching Known Issue MCP-001.

- [ ] First-class `RuntimeTool.disabled_reason` field — see "Field Mapping: /v1/tools ↔ RuntimeTool" above
- [ ] Wire `include_disabled` through a query parameter on each server's `list_tools()` handler
- [ ] Wire `disabled_code` through the same handlers, as a stable machine-readable companion to `disabled_reason` (never replacing it, never present alone)

### 1. `include_disabled` query parameter (target)

`GET /v1/tools?include_disabled=false` as an opt-in filter on tool discovery. Default (no query param, or `include_disabled=true`) SHOULD preserve today's behavior: every tool returned, including disabled ones. Only when a caller explicitly passes `include_disabled=false` SHOULD disabled tools be omitted from the `tools` array.

### 2. `disabled_code` structured field (target)

A machine-readable enum companion to the free-text `disabled_reason`, coexisting with it. Candidate values, mapped to today's `config_dependent`-gated servers:

| `disabled_code`             | Server(s)                              |
|------------------------------|-----------------------------------------|
| `EMPTY_ALLOWED_DIRS`         | file read / write / delete              |
| `EMPTY_ALLOWED_REPO_PATHS`   | git (precedence over `READ_ONLY`)       |
| `READ_ONLY`                  | git write tools                         |
| `EMPTY_COMMAND_ALLOWLIST`    | shell (reserved; not yet gated by `enabled` at all) |
| `EMPTY_WORKFLOW_ALLOWLIST`   | cicd (reserved; not yet gated by `enabled` at all)  |

`disabled_reason` remains for humans/logs; `disabled_code` is for programmatic dispatch. A `disabled_code` MUST be stable enough for machine handling; `disabled_reason` MAY change for clarity and MUST NOT be used as the programmatic contract.
