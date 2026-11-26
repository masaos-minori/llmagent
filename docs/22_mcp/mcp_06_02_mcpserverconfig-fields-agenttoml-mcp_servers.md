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
process's environment. `scripts/agent/http_lifecycle_launch_spec.py::build_child_env` builds the
child environment once per server, from a fixed runtime set plus that server's own derived
credentials, and merges the configured `env` on top of it.

- Fixed runtime variables: `PATH`, `HOME`, `USER`, `LOGNAME`, `SHELL`, `TMPDIR`, `TMP`,
  `TEMP`, `LANG`, `LC_*`, `LLMAGENT_CONFIG_DIR`, `LLMAGENT_SUDACHI_DICT`. Everything else in the
  Agent process's environment is absent from the child, including unrelated credentials and proxy
  variables.
- Each server additionally receives `MCP_<KEY>_AUTH_TOKEN` and `MCP_<KEY>_CONTROL_TOKEN`, derived
  from its own `[mcp_servers.<key>]` section name, plus only the variables its own
  `credential_env` declares. Another server's tokens are never present in a child's environment,
  and `GITHUB_TOKEN` reaches a child only when that server declares it.
- The derived tokens are not a convenience: each server's `auth_token =
  "${ENV:MCP_<KEY>_AUTH_TOKEN}"` is resolved inside the child, so the child must carry its own
  token or the server refuses to start.
- Control-token resolution is tolerant, so an unset or empty variable does not stop the server —
  it closes only that server's control paths, and tool authorization keeps its own behavior.
- A variable outside the fixed runtime set reaches one server only through that server's own
  `env` or `credential_env`.
- Declared `env` entries are filtered before the child sees them: a key matching the
  denylist (`LD_PRELOAD`, `LD_LIBRARY_PATH`, `PYTHONPATH`) is dropped, and a key naming a
  protected variable (`PATH`, `PYTHONPATH`, `LD_LIBRARY_PATH`, `HOME`, `USER`) is refused.
  Both are logged by key only, never by value.
- The same fixed runtime set is what a `shell_run` command sees, together with the shell
  server's configured `PATH` and the environment supplied in the request.

**Timing, logging and policy fields:** timeout, startup-stagger, and stderr-rotation fields are
defined with their constraints in `McpServerConfig`; a `0` timeout means no timeout for the
per-call and startup fields. The fields with design meaning are:

- `required`: startup criticality (ADR-004). An unavailable required server aborts startup; a non-required
  server unreachable at tool discovery is disabled (its tools are excluded) and startup continues with a
  WARNING. The effective `required` value is validated against `registry/component_mandatoriness.yaml` at
  startup: a `required = false` that contradicts a registry-`required` classification aborts startup with
  the fatal `component_mandatoriness`, and a configured server absent from the registry is likewise fatal
  (ADR-004 Group 4 "Undeterminable component mandatoriness"). A subprocess server that fails to spawn aborts
  startup regardless of `required`
  (see mcp_06_03), so `McpServerConfig` rejects `required = false` with `startup_mode = "subprocess"`.
- `control_auth_token`: the Agent-side control credential for that server, used only on the call-state
  control paths. Optional, defaults to empty, resolved from `${ENV:...}` with the tolerant resolver, so an
  unset variable yields an empty value rather than an error; an empty value closes that server's control
  paths and changes nothing about tool authorization. The value is registered as a secret and never
  logged. See [mcp_05_01](./mcp_05_01_access-control-and-allowlists.md) and
  [mcp_02_01](./mcp_02_01_endpoints-and-transport.md).
- `credential_env`: the extra credential variables this server's child process receives, written
  as variable names (`credential_env = ["GITHUB_TOKEN"]`), never as patterns. Optional, defaults
  to empty, and is validated at parse time: a name must match `[A-Za-z_][A-Za-z0-9_]*` and is
  refused when it matches the `env` denylist or names a protected variable, so a wildcard or a
  protected name is a startup error rather than a silently widened grant. Only the servers that
  read a credential declare it.
- `health_timeout`: the per-server health-check timeout. It must be greater than 0: a zero or a
  negative value is rejected at config load and at direct construction, so there is no unlimited
  branch for it and every consumer receives a positive value, the configured one when set and the
  default when unset. The rule is defined by `scripts/shared/mcp_config.py`, the canonical source
  for this field. A single health-check request timeout is this value capped by the time left to
  the startup deadline (see [mcp_02_02](mcp_02_02_startup-modes-and-health.md)).

**About `tool_names`:** Not used for routing decisions. It is metadata for drift validation (see `docs/22_mcp/mcp_03_01_dispatch-and-routing.md`), used by `validate_tool_names_match()` in `scripts/shared/tool_routing_validation.py`. An empty or omitted list skips validation.

**About `role`:** A human-readable label for operators, displayed in the `ROLE` column of `/mcp status` output. It is for display only and is never referenced by routing or dispatch logic.

**About the `key` field:** `key` is not a TOML setting. It is derived from the `[mcp_servers.<key>]` section name, used as an error-message prefix, and excluded from equality comparison so it never affects `/reload` diff detection. A section name must match `[a-z0-9][a-z0-9_-]{0,63}`: `validate_server_key()` in `scripts/shared/mcp_config.py` enforces it when the section is parsed, when `McpServerConfig` is constructed, and when the stderr log directory is opened, so a name containing a path separator or a control character is a startup error rather than a directory outside the log root.

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
- credential_env
- control_auth_token
- health_timeout
