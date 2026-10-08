---
title: "Startup Validation Behavior (`tool_definitions_strict`)"
area: mcp
tags:
  - mcp
  - startup
  - validation
related:
  - mcp_06_01_configuration-file-inventory.md
---
# Startup Validation Behavior (`tool_definitions_strict`)

> **Canonical specification.** This section describes the tool definitions check in `agent/services/tool_validation.py`.
> For routing drift detection (`validate_routing_against_live` in `shared/tool_routing_validation.py`), see [mcp_03 Drift validation](./mcp_03_02_tool-registry.md#drift-validation).
> These are different features.

The tool definitions check is executed at agent startup, comparing the `tool_definitions` in `config/agent.toml` against actual `/v1/tools` responses. Behavior varies depending on server reachability and the `tool_definitions_strict` setting:

| Scenario | `strict = false` | `strict = true` |
|---|---|---|
| **Partial Reachability** — Some servers respond | Validation proceeds for reachable servers; unreachable servers are logged as `WARNING` | Same — only compares reachable tools; any mismatch in reachable tools triggers a `RuntimeError` |
| **Total Unreachability** — No servers respond | Validation is skipped; `INFO: "All MCP servers unreachable ... skipping tool definition check"` — a SKIPPED outcome of this check means tool calls to unreachable servers fail for that session; whether startup continues is decided separately by the per-server `required` rule below | `RuntimeError: "Strict mode: all MCP servers unreachable — cannot validate tool definitions. Unreachable servers: [...]"` |
| **Tool Mismatch** — Reachable but names differ | `WARNING` per direction (missing_in_server / extra_on_servers) | `RuntimeError: "Strict mode: tool definition mismatch detected. Mismatches: .... Unreachable servers: ...."` |

### Startup validation statuses

#### WARNING
A non-critical issue. The system continues operating but the operator should be aware.
Example: optional server discovery failed.
Displayed via `write_warning()` with `[warn]` prefix.

#### FATAL
A critical issue that prevents normal operation. The system may be partially functional.
Displayed via `write_fatal()` with `[fatal]` prefix for visual distinction.
Example: required server discovery failed.

#### SKIPPED
Discovery was skipped entirely. This may indicate a full-session tool-call outage.
Displayed via `write_warning()` with `[SKIPPED]` prefix.
Example: MCP discovery skipped due to missing configuration.

### Discovery failure handling (per-server `required` flag)

MCP discovery follows the ADR-004 rule: an unavailable required server aborts startup; an unavailable non-required server is disabled and startup continues. The outcome depends on `McpServerConfig.required` and on `tool_definitions_strict`, not on any environment name (Explicit in code — scripts/agent/services/mcp_tool_discovery.py `McpToolDiscoveryService.discover_all()`, `_escalate_unreachable_findings()`).

**Unreachable servers and invalid `/v1/tools` responses or entries (per server):**
- `required = true`: FATAL outcome, startup blocked
- `required = false`: WARNING outcome, startup continues; the server's tools are missing from the `RuntimeToolRegistry` (disabled)

**Required tools:** a `tool_names` entry of a required server that is absent from the discovery results is FATAL.

**Duplicate tools:**
- Always FATAL, startup blocked, independent of `required` and `strict` (safety/integrity failure, ADR-004 Decision Group 2)

**Routing drift, tool-definition mismatch, malformed capabilities:**
- `strict = true`: FATAL outcome, startup blocked
- `strict = false`: WARNING outcome, startup continues

`ProductionConfigValidator` rejects `tool_definitions_strict = false` (Explicit in code — scripts/agent/production_config_validator.py `_REQUIRED_STRICT_KEYS`), so the strict-false rows describe the check's own behavior rather than a supported production setting.

**Key Points:**
- Tool name mismatches in `strict` mode trigger a `RuntimeError`.
- If all servers are unreachable in `strict` mode, a `RuntimeError` is raised including the list of unreachable servers. In non-strict mode, validation is skipped with an `INFO` log.
- Error messages clearly distinguish between mismatches and unreachable servers to facilitate debugging by operators.

**Important:** If discovery is `SKIPPED`, startup continues but the `RuntimeToolRegistry` remains empty or incomplete. Consequently, even if the LLM recognizes a tool, execution will fail at runtime. Operators must treat `SKIPPED` results from `mcp_tool_discovery` with the same severity as `WARNING`.

---



## Keywords

- configuration
