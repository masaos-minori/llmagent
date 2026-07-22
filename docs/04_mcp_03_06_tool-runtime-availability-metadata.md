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

# ツール実行時可用性メタデータ: `config_dependent`, `enabled`, `disabled_reason`

> **Implementation status:** As of 2026-07-21 `config_dependent` is adopted for `web_search-mcp`'s `browser_fetch` tool (merged from the former standalone browser-mcp server). `enabled`/`disabled_reason` fields are now wired into RuntimeToolRegistry via `_dedupe_and_build()` in `mcp_tool_discovery.py` — see `04_mcp_03_01_dispatch-and-routing.md` for details.

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

**Active example:** The git-mcp server actively uses `disabled_reason` to indicate why tools are disabled. See [git-mcp availability metadata](./04_mcp_04_05_git.md#availability-metadata) for details on its specific precedence rules.

**Not yet implemented:** The web-search server does NOT implement `disabled_reason` for `browser_fetch`, despite having `config_dependent=true`. See [web-search availability metadata](./04_mcp_04_01_web-search-file-read-github.md#availability-metadata) for details on its current limitations.

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

Any changes to tool availability (e.g., due to health degradation, config reload) will be reflected in subsequent `/v1/tools` responses and will cause `RuntimeToolRegistry` to be updated accordingly.

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

## Wiring reference

For end-to-end tracing of how `disabled_reason` flows into `/mcp status`, see also:
- `docs/04_mcp_03_02_tool-registry.md` — `RuntimeToolRegistry` module overview and discovery wiring.
- `docs/05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md` — `/mcp status` command reference (general health/status view; does not yet detail the per-tool diagnostics table).

## Future / deferred design options

**Note:** Top-level `capabilities` (on the response body, not per-tool) is also deferred unless verified otherwise. If any MCP server returns top-level `capabilities` in its `/v1/tools` response, this should be updated to reflect current implementation status.

Evaluated per requirement 20 (`requires/done/20260717_20_require.md` once filed) and
`plans/20260717-181151_plan.md`. Neither option below is implemented; both are deferred design
decisions with no dependency from the initial RuntimeToolRegistry migration (requirements 14-19).

- [ ] First-class `RuntimeTool.disabled_reason` field — see "Field Mapping: /v1/tools ↔ RuntimeTool" above

### 1. `include_disabled` query parameter

Proposed: `GET /v1/tools?include_disabled=false` as an opt-in filter on tool discovery.

- Default (no query param, or `include_disabled=true`) preserves today's behavior: every tool is
  returned, including disabled ones, each carrying `enabled=false` / `disabled_reason` set.
- Only when a caller explicitly passes `include_disabled=false` are disabled tools omitted from
  the `tools` array in the response.
- Status: unimplemented, no immediate action required.

### 2. `disabled_code` structured field

Proposed: a machine-readable enum companion to the free-text `disabled_reason`, coexisting with
it (never replacing it, never present alone without `disabled_reason`).

Candidate values, mapped to today's `config_dependent`-gated servers:

| `disabled_code`             | Server(s)                              |
|------------------------------|-----------------------------------------|
| `EMPTY_ALLOWED_DIRS`         | file read / write / delete              |
| `EMPTY_ALLOWED_REPO_PATHS`   | git (precedence over `READ_ONLY`)       |
| `READ_ONLY`                  | git write tools                         |
| `EMPTY_COMMAND_ALLOWLIST`    | shell (reserved; scoped out of req. 15) |
| `EMPTY_WORKFLOW_ALLOWLIST`   | cicd (reserved; scoped out of req. 15)  |

- `disabled_reason` remains for humans/logs; `disabled_code` is for programmatic dispatch.
- Status: unimplemented, no immediate action required.

Neither option is implemented. Both are deferred design decisions tracked for future evaluation;
the initial RuntimeToolRegistry migration (requirements 14-19) does not depend on either.
