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
  - mcp_03_01_dispatch-and-routing.md
  - adr_02_02_003_agent-runtime-tool-registry-routing-authority.md
  - agent_07_07_cli-and-commands-slash-commands-session-mcp.md
---

# Tool Runtime Availability Metadata: `config_dependent`, `enabled`, `disabled_reason`

> `config_dependent` is `true` for every tool of `git`, `github`, `cicd`, and `shell`, and for `browser_fetch` of `web_search`; it is `false` for the file servers, `mdq`, and `rag_pipeline` tools. `enabled`/`disabled_reason` are carried into `RuntimeToolRegistry` by `_dedupe_and_build()` in `mcp_tool_discovery_registry.py`. See `mcp_03_01_dispatch-and-routing.md` for details.

## 1. `config_dependent` (static)

Each server's `TOOL_LIST` includes a per-tool boolean field `config_dependent` (a boolean flag marking tools whose availability depends on configuration). `web_search-mcp`'s `browser_fetch` tool sets `config_dependent: True`.

## 2. `enabled` / `disabled_reason` (runtime, request-time-computed)

Added to each tool dict in the live `/v1/tools` response body, computed per-request from the owning server's current config state (`_cfg`). Invariant: `enabled=True` <-> `disabled_reason == ""`; `enabled=False` <-> `disabled_reason` is a non-empty standard string (enumerated in section 3).

## 3. Standard `disabled_reason` values

| `disabled_reason` value | Applies to |
|---|---|
| `"allowed_dirs is empty"` | file read/write/delete servers, mdq |
| `"allowed_repo_paths is empty"` | git (takes precedence over `read_only`) |
| `"read_only=true"` | git write tools only, when allowlist is non-empty |
| `"command_allowlist is empty"` | shell |
| `"repo_allowlist is empty"` | cicd (all tools) |
| `"workflow_allowlist is empty"` | cicd (`trigger_workflow` only) |
| `"browser_allowed_domains is empty"` | web_search (`browser_fetch` only) |
| `"GITHUB_TOKEN is not set"` | github |
| `"embed_url is not configured"` | rag_pipeline (`rag_run_pipeline`, `rag_debug_pipeline`) |

Every server computes `enabled`/`disabled_reason` per tool in its own `/v1/tools` handler. See [git-mcp availability metadata](./mcp_04_05_git.md#availability-metadata) for git's precedence rules.

## 4. `/v1/tools` behavioral rules

By default (`include_disabled=false`) disabled tools (`enabled=False`) are omitted from the response; pass `include_disabled=true` to receive them. Each returned tool entry carries `config_dependent`, `enabled`, and `disabled_reason` alongside its other fields — see each server's own `/v1/tools` handler (named in section 3 above) for the exact response shape.

## Field Mapping: /v1/tools ↔ RuntimeTool

`enabled` maps to `RuntimeTool.enabled_for_llm` (both indicate LLM visibility; values should match). `disabled_reason` is **not** a first-class `RuntimeTool` field: the reason a tool is disabled is determined by the source of truth (config, health status, etc.) rather than carried forward.

## 5. Dispatch rule

Every server except `mdq` rejects disabled tools at `/v1/call_tool` before reaching the dispatch table (server-side gate). The response shape is `CallToolResponse(result="Tool disabled: <reason>", is_error=True)`. `mdq` only reports `enabled`/`disabled_reason` in `/v1/tools`; its `/v1/call_tool` has no such gate and relies on the per-path `allowed_dirs` authorization (`MdqAuthorizationError`) instead.

## Design decisions

For the concept distinctions (static availability vs. dynamic health, approval vs. disabled state), `/v1/tools` as the sole source of `RuntimeToolRegistry`, and reload not rediscovering tools, see [ADR-003](../10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md).

## Wiring reference

For end-to-end tracing of how `disabled_reason` flows into `/mcp status`, see also:
- `docs/22_mcp/mcp_03_02_tool-registry.md` — `RuntimeToolRegistry` module overview and discovery wiring.
- `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md` — `/mcp status` command reference (general health/status view; does not yet detail the per-tool diagnostics table).

## `include_disabled` and `disabled_code`

**Note:** Top-level `capabilities` (on the response body, not per-tool) is not returned by `build_tools_response()`, which returns only `schema_version` and `tools`.

All MCP servers' `list_tools()` handlers accept `include_disabled` and `disabled_code` and pass them through to `mcp_servers/server.py::build_tools_response()`. `include_disabled` is opt-in: `GET /v1/tools` omits tools with `enabled=False` unless `include_disabled=true` is passed.

`disabled_code`, when provided, is compared against each tool's `disabled_reason` string (the values in section 3); no separate machine-readable enum exists. Because disabled tools are already omitted by default, `disabled_code` is only meaningful together with `include_disabled=true`. `disabled_reason` strings are therefore effectively part of the programmatic contract for this filter.

## Keywords

- mcp
- routing
- tool-registry
- runtime-tool-registry
