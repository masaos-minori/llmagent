---
title: "Startup Validation Behavior"
area: mcp
tags:
  - mcp
  - startup
  - validation
related:
  - mcp_06_01_configuration-file-inventory.md
  - mcp_03_02_tool-registry.md
---
# Startup Validation Behavior

> **Canonical specification.** This section describes the tool definitions check in `agent/services/tool_validation.py`, surfaced at startup through `McpToolDiscoveryService._check_tool_definitions_finding()` in `agent/services/mcp_tool_discovery.py`.
> For routing drift detection (`validate_routing_against_live` in `shared/tool_routing_validation.py`), see [mcp_03 Drift validation](./mcp_03_02_tool-registry.md#drift-validation).
> These are different features.

The tool definitions check is executed at agent startup, comparing the `tool_definitions` in `config/agent.toml` against actual `/v1/tools` responses. The startup check is strict-only: there is no setting that downgrades its outcome. A `RuntimeError` raised by the check is converted into a `FATAL` startup finding instead of propagating (Explicit in code — scripts/agent/services/mcp_tool_discovery.py `_check_tool_definitions_finding()`).

| Scenario | Startup outcome |
|---|---|
| **Partial Reachability** — Some servers respond | Validation compares reachable servers only; unreachable servers are logged as `WARNING`. Any mismatch in reachable tools is a `FATAL` finding and blocks startup |
| **Total Unreachability** — No servers respond | `FATAL` finding: `"Strict mode: all MCP servers unreachable — cannot validate tool definitions. Unreachable servers: [...]"` and startup is blocked. Only the case with no configured reachable servers and no unreachable server produces a logged skip with no finding |
| **Tool Mismatch** — Reachable but names differ | `FATAL` finding: `"Strict mode: tool definition mismatch detected. Mismatches: .... Unreachable servers: ...."` and startup is blocked |

A separate runtime-only validation (`check_tool_definitions_runtime` in `agent/services/tool_validation.py`) logs warnings and never raises; it is not part of the startup gate.

### Startup validation statuses

#### WARNING
A non-critical issue. The system continues operating but the operator should be aware.
Example: optional server discovery failed.
Displayed via `write_warning()` with `[warn]` prefix.

#### FATAL
A condition that prevents startup: startup is aborted after the checks of the failing stage complete (ADR-004).
Displayed via `write_fatal()` with `[fatal]` prefix for visual distinction.
Example: required server discovery failed.

#### SKIPPED
Discovery was skipped entirely. This may indicate a full-session tool-call outage.
Displayed via `write_warning()` with `[SKIPPED]` prefix.
Example: MCP discovery skipped due to missing configuration.

### Discovery failure handling (per-server `required` flag)

MCP discovery follows the ADR-004 rule: an unavailable required server aborts startup; an unavailable non-required server is disabled and startup continues. The outcome depends on `McpServerConfig.required`, not on any environment name (Explicit in code — scripts/agent/services/mcp_tool_discovery.py `McpToolDiscoveryService.discover_all()`, `_escalate_unreachable_findings()`).

**Unreachable servers and invalid `/v1/tools` responses or entries (per server):**
- `required = true`: FATAL outcome, startup blocked
- `required = false`: WARNING outcome, startup continues; the server's tools are missing from the `RuntimeToolRegistry` (disabled)

**Required tools:** a `tool_names` entry of a required server that is absent from the discovery results is FATAL.

**Duplicate tools:**
- Always FATAL, startup blocked, independent of `required` (safety/integrity failure, ADR-004 Decision Group 2)

**Routing drift, tool-definition mismatch, malformed capabilities:**
- Always FATAL, startup blocked, with no toggle (safety/integrity failures)
- Unexpected failure of the routing-drift check itself (not a detected drift): FATAL outcome, startup blocked

### Pre-bind security-posture gate

Before an MCP server binds, its published security posture is positively confirmed. ADR-004 is the single normative authority for the pre-bind posture gate: a `FAILED` posture is a safety/integrity failure that aborts Agent startup regardless of the server's `required` value (fail-closed), and a `required = false` server does not permit startup to continue. A probe that cannot confirm the posture is treated as `FAILED`. The gate runs before Tool registration and is enforced in code; it is referenced here by authority (ADR-004), not by code path.

Removed settings (`tool_definitions_strict`, `routing_drift_strict`) have no effect and are rejected as unknown production keys (Explicit in code — scripts/agent/production_config_validator.py `_check_unknown_production_keys`).

**Important:** If discovery is `SKIPPED`, startup continues but the `RuntimeToolRegistry` remains empty or incomplete. Consequently, even if the LLM recognizes a tool, execution will fail at runtime. Operators must treat `SKIPPED` results from `mcp_tool_discovery` with the same severity as `WARNING`.

---



## Keywords

- configuration
