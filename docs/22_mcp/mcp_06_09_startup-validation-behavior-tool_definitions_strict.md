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
| **Total Unreachability** — No servers respond | Validation is skipped; `INFO: "All MCP servers unreachable ... skipping tool definition check"` — **Regardless of environment: SKIPPED outcome means all tool calls will fail for that session** | `RuntimeError: "Strict mode: all MCP servers unreachable — cannot validate tool definitions. Unreachable servers: [...]"` |
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
Discovery was skipped entirely. Regardless of environment, this may indicate a full-session tool-call outage.
Displayed via `write_warning()` with `[SKIPPED]` prefix.
Example: MCP discovery skipped due to missing configuration.

### Environment-specific behavior differences

MCP discovery behavior differs based on validation strictness (`tool_definitions_strict`), not environment:

**Duplicate tools:**
- Always FATAL, startup blocked (exception to the `is_fatal = strict` scheme)

**Unreachable servers and other non-duplicate findings:**
- `strict = true`: FATAL outcome, startup blocked
- `strict = false`: WARNING outcome, startup continues; tools of unreachable servers are missing from the `RuntimeToolRegistry`

This difference exists because non-strict mode is designed to be more forgiving during iteration, while strict enforcement prevents partial functionality.

**Key Points:**
- Tool name mismatches in `strict` mode trigger a `RuntimeError`.
- If all servers are unreachable in `strict` mode, a `RuntimeError` is raised including the list of unreachable servers. In non-strict mode, validation is skipped with an `INFO` log.
- Error messages clearly distinguish between mismatches and unreachable servers to facilitate debugging by operators.

**Important:** If discovery is `SKIPPED`, startup continues but the `RuntimeToolRegistry` remains empty or incomplete. Consequently, even if the LLM recognizes a tool, execution will fail at runtime. Operators must treat `SKIPPED` results from `mcp_tool_discovery` with the same severity as `WARNING`.

---



## Keywords

configuration
