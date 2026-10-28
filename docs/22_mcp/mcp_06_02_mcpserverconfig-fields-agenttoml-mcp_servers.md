---
title: "McpServerConfig Fields (agent.toml `[mcp_servers.*]`)"
area: mcp
tags:
  - mcp
  - configuration
related:
  - mcp_06_01_configuration-file-inventory.md
  - mcp_03_01_dispatch-and-routing.md
---

# McpServerConfig Fields (agent.toml `[mcp_servers.*]`)

**Ownership:** The fields described in this file are defined only in `config/agent.toml`.
Each MCP server's application settings are described in its corresponding `*_mcp_server.toml`.

## Agent-side MCP fields (agent.toml `[mcp_servers.*]`)

The configurable fields, plus an automatically derived `key` field (below), are defined in `scripts/shared/mcp_config.py::McpServerConfig`.

**About the `env` field:** A subprocess server does not inherit a copy of the Agent
process's environment. `CommandValidator.filter_env` builds the child environment from an
allowlist and merges the configured `env` on top of it.

- Inherited variables: `PATH`, `HOME`, `USER`, `LOGNAME`, `SHELL`, `TMPDIR`, `TMP`,
  `TEMP`, `LANG`, `LC_*`, `MCP_*_AUTH_TOKEN`, `GITHUB_TOKEN`, `LLMAGENT_CONFIG_DIR`,
  `LLMAGENT_SUDACHI_DICT`. Everything else in the Agent process's environment is absent
  from the child, including unrelated credentials and proxy variables.
- The allowlist is not a convenience: each server's `auth_token =
  "${ENV:MCP_<NAME>_AUTH_TOKEN}"` is resolved inside the child, so the token pattern must
  stay inherited or the server refuses to start.
- A variable outside the allowlist reaches one server only through that server's own
  `env`.
- Declared `env` entries are filtered before the child sees them: a key matching the
  denylist (`LD_PRELOAD`, `LD_LIBRARY_PATH`, `PYTHONPATH`) is dropped, and a key naming a
  protected variable (`PATH`, `PYTHONPATH`, `LD_LIBRARY_PATH`, `HOME`, `USER`) is refused.
  Both are logged by key only, never by value.
- The same inherited set is what a `shell_run` command sees, together with the shell
  server's configured `PATH` and the environment supplied in the request.

**Timing, logging and policy fields:** timeout, startup-stagger, and stderr-rotation fields are
defined with their constraints in `McpServerConfig`; a `0` timeout means no timeout. The fields
with design meaning are:

- `required`: startup criticality (ADR-004). An unavailable required server aborts startup; a non-required
  server unreachable at tool discovery is disabled (its tools are excluded) and startup continues with a
  WARNING. A subprocess server that fails to spawn aborts startup regardless of `required`
  (see mcp_06_03), so `McpServerConfig` rejects `required = false` with `startup_mode = "subprocess"`.
- `failure_policy`: reserved for runtime call-failure behavior. Only `fail-fast` exists and nothing branches on it.

**About `tool_names`:** Not used for routing decisions. It is metadata for drift validation (see `docs/22_mcp/mcp_03_01_dispatch-and-routing.md`), used by `validate_tool_names_match()` in `scripts/shared/tool_routing_validation.py`. An empty or omitted list skips validation.

**About `role`:** A human-readable label for operators, displayed in the `ROLE` column of `/mcp status` output. It is for display only and is never referenced by routing or dispatch logic.

**About the `key` field:** `key` is not a TOML setting. It is derived from the `[mcp_servers.<key>]` section name, used as an error-message prefix, and excluded from equality comparison so it never affects `/reload` diff detection.

**`startup_mode="none"`:** This server is not started as a subprocess, and no health check is performed at startup. All tool calls routed to this server are immediately rejected with a `"disabled (startup_mode=none)"` error by the shared invocation-boundary guard `ToolTransportInvoker._run_precall_gates()` (inherited by `ToolExecutor`) before attempting network access. This is the default if `startup_mode` is omitted in the config — to make the server available, you must explicitly specify `"persistent"` or `"subprocess"`.

**Validation Rules:**
- `transport="http"` → `url` must not be empty and must be a valid HTTP/HTTPS URL.
- `startup_mode="subprocess"` → `cmd` must not be empty.

---

## Keywords

- configuration
- McpServerConfig
- key
- env
