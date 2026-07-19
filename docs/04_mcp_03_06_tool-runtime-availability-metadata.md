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

> **Implementation status:** As of 2026-07-18 this contract is documented as target design; production code still uses `requires_config` and has no `enabled`/`disabled_reason`/`RuntimeToolRegistry` — see `plans/20260717-173602_plan.md` through `plans/20260717-175630_plan.md` (requirements 14-18) for the implementing work.

## 1. `config_dependent` (static)

Each server's `TOOL_LIST` includes a per-tool boolean field `config_dependent` (direct rename of `requires_config` with identical boolean semantics, no compatibility shim). `requires_config` is removed; any remaining doc/code reference to it describes obsolete behavior.

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

## 5. Dispatch rule

Disabled tools must be rejected by `/v1/call_tool` before reaching the dispatch table (server-side gate). Reference requirement 16's plan (`plans/20260717-174848_plan.md`) for the exact response shape: `CallToolResponse(result="Tool disabled: <reason>", is_error=True)`.

## 6. RuntimeToolRegistry (agent-side)

Disabled tools are tracked for diagnostics (`enabled_for_llm` derived field) but never included in the LLM-facing tool list and never dispatchable through the registry's own routing path. Four states: discovered / MCP-server-enabled / agent-policy-enabled / LLM-visible. Reference requirement 17's plan (`plans/20260717-175327_plan.md`) — per the post-review decision, this section describes the disabled-visibility fields/methods as an extension of the adopted 13-field/9-method `RuntimeTool`/`RuntimeToolRegistry` lineage (`implementations/20260717-203121_runtime_tool.py.md`, `implementations/20260717-203200_runtime_tool_registry.py.md`, `implementations/20260718-084710_runtime_tool.py.md`), not as a separate 6-field class.

## Future / deferred design options

Evaluated per requirement 20 (`requires/done/20260717_20_require.md` once filed) and
`plans/20260717-181151_plan.md`. Neither option below is implemented; both are deferred design
decisions with no dependency from the initial RuntimeToolRegistry migration (requirements 14-19).

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

Candidate values, mapped to today's `requires_config`-gated servers:

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
