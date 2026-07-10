---
title: "Startup Validation Behavior (`tool_definitions_strict`)"
category: mcp
tags:
  - mcp
  - configuration
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_06_configuration-file-inventory.md
source:
  - 04_mcp_06_configuration-file-inventory.md
---

# Startup Validation Behavior (`tool_definitions_strict`)

## Startup Validation Behavior (`tool_definitions_strict`)

> **Canonical specification.** This section describes the tool definitions check in `repl_health.py`.
> For routing drift detection (`validate_routing_against_live` in `route_resolver.py`), see
> [04_mcp_03 §Drift validation](04_mcp_03_routing_lifecycle_and_execution.md#drift-validation).
> These are different functions — see also `04_mcp_90 §SPEC-01`.

The tool definitions check runs at agent startup and compares `tool_definitions` from `config/agent.toml` against live `/v1/tools` responses. Behavior depends on server reachability and `tool_definitions_strict`:

| Scenario | `strict = false` | `strict = true` |
|---|---|---|
| **Partial unreachable** — some servers respond | Validation proceeds with reachable servers; unreachable servers logged as `WARNING` | Same — only reachable tools compared; mismatch in reachable tools raises `RuntimeError` |
| **All unreachable** — no server responds | Validation skipped; `INFO: "All MCP servers unreachable ... skipping tool definition check"` | `RuntimeError: "Strict mode: all MCP servers unreachable — cannot validate tool definitions. Unreachable servers: [...]"` |
| **Tool mismatch** — reachable but names differ | `WARNING` per direction (missing_in_server / extra_on_servers) | `RuntimeError: "Strict mode: tool definition mismatch detected. Mismatches: .... Unreachable servers: ...."` |

**Key points:**
- A tool name mismatch in strict mode raises `RuntimeError`.
- When all servers are unreachable in strict mode, `RuntimeError` is raised listing the unreachable servers. In non-strict mode, validation is skipped with an INFO log.
- The error message clearly separates mismatches from unreachable servers for operator debugging.

---


## Related Documents

- [04_mcp_06_configuration-file-inventory.md](04_mcp_06_configuration-file-inventory.md)

## Keywords

configuration
