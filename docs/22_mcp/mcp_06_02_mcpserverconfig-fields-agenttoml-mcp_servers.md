---
title: "McpServerConfig Fields (agent.toml `[mcp_servers.*]`)"
area: mcp
tags:
  - mcp
  - configuration
related:
  - mcp_06_01_configuration-file-inventory.md
---

# McpServerConfig Fields (agent.toml `[mcp_servers.*]`)

**Ownership:** The fields described in this file are defined only in `config/agent.toml`.
Each MCP server's application settings are described in its corresponding `*_mcp_server.toml`.

## Agent-side MCP fields (agent.toml `[mcp_servers.*]`)

The configurable fields, plus an automatically derived `key` field (described
below), are defined in `scripts/shared/mcp_config.py::McpServerConfig`. The `env`
field's values are filtered through a denylist that rejects `LD_PRELOAD`,
`LD_LIBRARY_PATH`, and `PYTHONPATH`.

**Timing, logging and policy fields:**

| Field | Meaning | Constraint |
|---|---|---|
| `call_timeout_sec` | Per-call timeout of the HTTP transport. `0` disables the timeout. | `>= 0` |
| `health_timeout` | Per-server health-check timeout. When unset the global default applies; `0` means no timeout. | `>= 0` |
| `startup_timeout_sec` | How long the startup health poll of a subprocess server waits for it to become healthy. | `>= 0` |
| `startup_stagger_delay_sec` | Delay inserted between consecutive subprocess starts. | `>= 0` |
| `max_stderr_log_size_mb` | Size at which a subprocess stderr log is rotated. | `> 0` |
| `max_stderr_log_files` | Number of rotated stderr logs kept. | `>= 1` |
| `required` | Startup criticality of the server (see ADR-004): an unavailable required server aborts startup, while an unavailable non-required server is disabled (its tools are excluded) and startup continues with a WARNING. | boolean |
| `failure_policy` | Reserved for runtime call-failure behavior. Only `fail-fast` exists and nothing branches on it yet. | enum |

**About `tool_names`:** Not used for routing decisions. It is metadata for drift validation (see `docs/22_mcp/mcp_03_01_dispatch-and-routing.md`), used by `validate_tool_names_match()` in `scripts/shared/tool_routing_validation.py`. There are three states: field omitted (default `[]`), explicit empty list `[]`, or a list with values. In all cases, validation is skipped via `if not cfg.tool_names: continue`.

**About `role`:** A human-readable label for operators, displayed in the `ROLE` column of `/mcp status` output. It is for display only and is never referenced by routing or dispatch logic.

**About the `key` field:** In addition to the above, `McpServerConfig` has a `key: str = ""` field, but this is not a setting specified directly in TOML. It is an internal identifier automatically set by `_build_single_server()` from the section name in `[mcp_servers.<key>]`, used as a prefix in error messages (e.g., `McpServerConfig['github']: ...`). `compare=False, repr=False` is specified, so it does not affect equality comparison between `McpServerConfig` instances (e.g., for detecting diffs during `/reload`) (Explicit in code).

**`startup_mode="none"`:** This server is not started as a subprocess, and no health check is performed at startup. All tool calls routed to this server are immediately rejected with a `"disabled (startup_mode=none)"` error by the `ToolExecutor` startup mode check before attempting network access. This is the default if `startup_mode` is omitted in the config — to make the server available, you must explicitly specify `"persistent"` or `"subprocess"`.

**Validation Rules:**
- `transport="http"` → `url` must not be empty and must be a valid HTTP/HTTPS URL.
- `startup_mode="subprocess"` → `cmd` must not be empty.

---

## Keywords

- configuration
- McpServerConfig
- key
