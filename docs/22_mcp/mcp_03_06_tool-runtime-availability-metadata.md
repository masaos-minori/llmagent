---
title: "Tool Runtime Availability Metadata: config_dependent, enabled, disabled_reason"
area: mcp
tags:
  - mcp
  - routing
  - tool-registry
  - runtime-tool-registry
related:
  - mcp_00_document-guide.md
  - mcp_03_02_tool-registry.md
  - mcp_04_01_web-search-file-read-github.md
  - mcp_04_02_file-write-file-delete-shell.md
  - mcp_04_03_rag-pipeline-and-cicd.md
  - mcp_04_05_git.md
  - agent_08_04_configuration-mcp-approval-obs.md
  - governance_03_issue-and-uncertainty-management.md
---

# Tool Runtime Availability Metadata: `config_dependent`, `enabled`, `disabled_reason`

> **Implementation status:** `config_dependent` is adopted across `git`, `file_read`/`file_write`/`file_delete`, `github`, and `web_search` (`browser_fetch`). `enabled`/`disabled_reason` fields are now wired into RuntimeToolRegistry via `_dedupe_and_build()` in `mcp_tool_discovery.py` — see `mcp_03_01_dispatch-and-routing.md` for details.

## 0. Concept distinctions

See [ADR-003](../10_adr/ADR-003-runtime-tool-registry-routing-authority.md) for the distinction between these concepts.

## 1. `config_dependent` (static)

Each server's `TOOL_LIST` includes a per-tool boolean field `config_dependent` (a boolean flag marking tools whose availability depends on configuration). `web_search-mcp`'s `browser_fetch` tool sets `config_dependent: True`.

## 2. `enabled` / `disabled_reason` (runtime, request-time-computed)

Added to each tool dict in the live `/v1/tools` response body, computed per-request from the owning server's current config state (`_cfg`). Invariant: `enabled=True` <-> `disabled_reason == ""`; `enabled=False` <-> `disabled_reason` is a non-empty standard string (enumerated in section 3).

## 3. Standard `disabled_reason` values

| `disabled_reason` value | Applies to | Status |
|---|---|---|
| `"allowed_dirs is empty"` | file read/write/delete servers, mdq | active |
| `"allowed_repo_paths is empty"` | git (takes precedence over `read_only`) | active |
| `"read_only=true"` | git write tools only, when allowlist is non-empty | active |
| `"command_allowlist is empty"` | shell | active |
| `"repo_allowlist is empty"` | cicd (all tools) | active |
| `"workflow_allowlist is empty"` | cicd (`trigger_workflow` only) | active |
| `"browser_allowed_domains is empty"` | web_search (`browser_fetch` only) | active |
| `"GITHUB_TOKEN is not set"` | github | active |
| `"embed_url is not configured"` | rag_pipeline (`rag_run_pipeline`, `rag_debug_pipeline`) | active |

**Implemented:** `git`, `file_read`/`file_write`/`file_delete`, `github`, `web_search`, `rag_pipeline`, `cicd`, `mdq`, and `shell` each compute `enabled`/`disabled_reason` per tool in their own `/v1/tools` handler. See [git-mcp availability metadata](./mcp_04_05_git.md#availability-metadata) for git's specific precedence rules. `web_search`/`github`/`rag_pipeline`/`cicd`/`mdq`/`shell` compute availability via `_web_search_tool_availability()`/`_github_tool_availability()`/`_rag_pipeline_tool_availability()`/`_cicd_tool_availability()`/`_mdq_tool_availability()`/`_shell_tool_availability()` respectively.

## 4. `/v1/tools` behavioral rules

By default (`include_disabled=false`) disabled tools (`enabled=False`) are omitted from the response; pass `include_disabled=true` to receive them. Each returned tool entry carries `config_dependent`, `enabled`, and `disabled_reason` alongside its other fields — see each server's own `/v1/tools` handler (named in section 3 above) for the exact response shape.

## /v1/tools as RuntimeToolRegistry Source

See [ADR-003](../10_adr/ADR-003-runtime-tool-registry-routing-authority.md) for the design decision that `/v1/tools` is the sole source for constructing `RuntimeToolRegistry`.

## Reload vs. restart for RuntimeToolRegistry

See [ADR-003](../10_adr/ADR-003-runtime-tool-registry-routing-authority.md) for the design decision that reload does not rediscover tools.

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

Disabled tools must be rejected by `/v1/call_tool` before reaching the dispatch table (server-side gate). The response shape is `CallToolResponse(result="Tool disabled: <reason>", is_error=True)`.

## 6. RuntimeToolRegistry (agent-side)

See [ADR-003](../10_adr/ADR-003-runtime-tool-registry-routing-authority.md) for the design decision about RuntimeToolRegistry as the sole authority.

## 6a. Static availability vs. dynamic health (distinct, unintegrated boundary)

See [ADR-003](../10_adr/ADR-003-runtime-tool-registry-routing-authority.md) for the design decision that static availability and dynamic health are separate subsystems.

## 6b. Approval is not a disabled state

See [ADR-003](../10_adr/ADR-003-runtime-tool-registry-routing-authority.md) for the design decision that approval is not a form of disabled availability.

## Wiring reference

For end-to-end tracing of how `disabled_reason` flows into `/mcp status`, see also:
- `docs/22_mcp/mcp_03_02_tool-registry.md` — `RuntimeToolRegistry` module overview and discovery wiring.
- `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md` — `/mcp status` command reference (general health/status view; does not yet detail the per-tool diagnostics table).

## `include_disabled` and `disabled_code`

**Note:** Top-level `capabilities` (on the response body, not per-tool) is not returned by `build_tools_response()`, which returns only `schema_version` and `tools`.

All MCP servers' `list_tools()` handlers accept `include_disabled` and `disabled_code` and pass them through to `mcp_servers/server.py::build_tools_response()`. `include_disabled` is opt-in: `GET /v1/tools` omits tools with `enabled=False` unless `include_disabled=true` is passed.

`disabled_code`, when provided, is compared against each tool's `disabled_reason` string (the values in section 3); no separate machine-readable enum exists. Because disabled tools are already omitted by default, `disabled_code` is only meaningful together with `include_disabled=true`. `disabled_reason` strings are therefore effectively part of the programmatic contract for this filter.

First-class `RuntimeTool.disabled_reason` field — see "Field Mapping: /v1/tools ↔ RuntimeTool" above (still deferred future work, unrelated to `include_disabled`/`disabled_code`).

## Keywords

- mcp
- routing
- tool-registry
- runtime-tool-registry
