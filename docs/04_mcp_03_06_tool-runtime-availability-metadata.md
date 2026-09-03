---
title: "Tool Runtime Availability Metadata: config_dependent, enabled, disabled_reason"
area: mcp
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
  - 00_governance_03_issue-and-uncertainty-management.md
---

# Tool Runtime Availability Metadata: `config_dependent`, `enabled`, `disabled_reason`

> **Implementation status:** `config_dependent` is adopted across `git`, `file_read`/`file_write`/`file_delete`, `github`, and `web_search` (`browser_fetch`). `enabled`/`disabled_reason` fields are now wired into RuntimeToolRegistry via `_dedupe_and_build()` in `mcp_tool_discovery.py` — see `04_mcp_03_01_dispatch-and-routing.md` for details.

## 0. Concept distinctions

See [ADR-003](adr/ADR-003-runtime-tool-registry-routing-authority.md) for the distinction between these concepts.

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
| `"command_allowlist is empty"` | shell | active |
| `"workflow_allowlist is empty"` | cicd | active |

**Implemented:** `git`, `file_read`/`file_write`/`file_delete`, `github`, `web_search`, `rag_pipeline`, `cicd`, `mdq`, and `shell` each compute `enabled`/`disabled_reason` per tool in their own `/v1/tools` handler. See [git-mcp availability metadata](./04_mcp_04_05_git.md#availability-metadata) for git's specific precedence rules. `rag_pipeline`/`cicd`/`mdq`/`shell` compute availability via `_rag_pipeline_tool_availability()`/`_cicd_tool_availability()`/`_mdq_tool_availability()`/`_shell_tool_availability()` respectively.

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

See [ADR-003](adr/ADR-003-runtime-tool-registry-routing-authority.md) for the design decision that `/v1/tools` is the sole source for constructing `RuntimeToolRegistry`.

## Reload vs. restart for RuntimeToolRegistry

See [ADR-003](adr/ADR-003-runtime-tool-registry-routing-authority.md) for the design decision that reload does not rediscover tools.

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

See [ADR-003](adr/ADR-003-runtime-tool-registry-routing-authority.md) for the design decision about RuntimeToolRegistry as the sole authority.

## 6a. Static availability vs. dynamic health (distinct, unintegrated boundary)

See [ADR-003](adr/ADR-003-runtime-tool-registry-routing-authority.md) for the design decision that static availability and dynamic health are separate subsystems.

## 6b. Approval is not a disabled state

See [ADR-003](adr/ADR-003-runtime-tool-registry-routing-authority.md) for the design decision that approval is not a form of disabled availability.

## Wiring reference

For end-to-end tracing of how `disabled_reason` flows into `/mcp status`, see also:
- `docs/04_mcp_03_02_tool-registry.md` — `RuntimeToolRegistry` module overview and discovery wiring.
- `docs/05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md` — `/mcp status` command reference (general health/status view; does not yet detail the per-tool diagnostics table).

## `include_disabled` and `disabled_code`

**Note:** Top-level `capabilities` (on the response body, not per-tool) is also deferred unless verified otherwise. If any MCP server returns top-level `capabilities` in its `/v1/tools` response, this should be updated to reflect current implementation status.

All MCP servers' `list_tools()` handlers accept `include_disabled` and `disabled_code` and pass them through to `mcp_servers/server.py::build_tools_response()`. `GET /v1/tools?include_disabled=false` omits disabled tools from the `tools` array; the default (no query param, or `include_disabled=true`) preserves the original behavior of returning every tool, including disabled ones.

`disabled_code` is a machine-readable enum companion to the free-text `disabled_reason`, mapped to each `config_dependent`-gated server:

| `disabled_code`             | Server(s)                              |
|------------------------------|-----------------------------------------|
| `EMPTY_ALLOWED_DIRS`         | file read / write / delete              |
| `EMPTY_ALLOWED_REPO_PATHS`   | git (precedence over `READ_ONLY`)       |
| `READ_ONLY`                  | git write tools                         |
| `EMPTY_COMMAND_ALLOWLIST`    | shell                                    |
| `EMPTY_WORKFLOW_ALLOWLIST`   | cicd                                     |

`disabled_reason` remains for humans/logs; `disabled_code` is for programmatic dispatch. A `disabled_code` MUST be stable enough for machine handling; `disabled_reason` MAY change for clarity and MUST NOT be used as the programmatic contract.

First-class `RuntimeTool.disabled_reason` field — see "Field Mapping: /v1/tools ↔ RuntimeTool" above (still deferred future work, unrelated to `include_disabled`/`disabled_code`).
