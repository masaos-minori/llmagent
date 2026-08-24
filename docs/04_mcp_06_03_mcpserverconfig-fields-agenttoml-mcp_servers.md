---
title: "McpServerConfig Fields (agent.toml `[mcp_servers.*]`)"
area: mcp
tags:
  - mcp
  - configuration
related:
  - 04_mcp_06_02_configuration-file-inventory.md
source:
  - 04_mcp_06_02_configuration-file-inventory.md
---

# McpServerConfig Fields (agent.toml `[mcp_servers.*]`)

**Ownership:** The fields described in this file are defined only in `config/agent.toml`.
Each MCP server's application settings are described in its corresponding `*_mcp_server.toml`.

## Agent-side MCP fields (agent.toml `[mcp_servers.*]`)

There are 13 configurable fields in `agent.toml`, plus an automatically derived `key` field (described below):

| Field | Type | Default | Description |
|---|---|---|---|
| `transport` | `TransportType` | Required | `TransportType.HTTP` (`"http"`); TOML string values are converted by the config loader (not at runtime) |
| `url` | `str` | Required | Base URL of the HTTP server |
| `startup_mode` | `str` | `"none"` | `"none"` / `"persistent"` / `"subprocess"` |
| `call_timeout_sec` | `float` | `60.0` | Timeout in seconds per tool call; `0` means no timeout |
| `startup_timeout_sec` | `int` | `30` | Health polling timeout during subprocess startup |
| `tool_names` | `list[str]` | `[]` | Metadata for drift validation, not used for routing (described below) |
| `auth_token` | `str` | `""` | Bearer token sent by `ToolExecutor` |
| `role` | `str` | `""` | Human-readable label (described below) |
| `cmd` | `list[str]` | `[]` | Startup command for `startup_mode=subprocess`; must not be empty when using subprocess mode |
| `env` | `dict[str, str]` | `{}` | Additional environment variables for subprocess; `LD_PRELOAD`/`LD_LIBRARY_PATH`/`PYTHONPATH` are rejected via denylist |
| `startup_stagger_delay_sec` | `float` | `0.0` | Delay between consecutive server startups (seconds) |
| `max_stderr_log_size_mb` | `float` | `100.0` | Maximum stderr log size before rotation (MB) |
| `max_stderr_log_files` | `int` | `3` | Number of rotated stderr log files to retain |

**About `tool_names`:** Not used for routing decisions. It is metadata for drift validation (see `docs/04_mcp_03_01_dispatch-and-routing.md`), used by `validate_tool_names_match()` in `scripts/shared/tool_routing_validation.py`. There are three states: field omitted (default `[]`), explicit empty list `[]`, or a list with values. In all cases, validation is skipped via `if not cfg.tool_names: continue`.

**About `role`:** A human-readable label for operators, displayed in the `ROLE` column of `/mcp status` output. It is for display only and is never referenced by routing or dispatch logic.

**Note on Deprecation (2026-07-17):** The `healthcheck_mode` field and `HealthcheckMode` enum were removed. Since HTTP is the only supported transport, `healthcheck_mode` was always derived as `HealthcheckMode.HTTP` (`"http"`) via `_derive_healthcheck_mode()`, regardless of whether the setting was present or what its content was — the field itself, the validation branch, and the `_MCP_SERVER_FIELDS` entry in `config_reload.py` were all unnecessary wiring for a second health check method that was never implemented. We will reconsider this when implementing a second transport/health check method.

**About the `key` field:** In addition to the above, `McpServerConfig` has a `key: str = ""` field, but this is not a setting specified directly in TOML. It is an internal identifier automatically set by `_build_single_server()` from the section name in `[mcp_servers.<key>]`, used as a prefix in error messages (e.g., `McpServerConfig['github']: ...`). `compare=False, repr=False` is specified, so it does not affect equality comparison between `McpServerConfig` instances (e.g., for detecting diffs during `/reload`) (Explicit in code).

**`startup_mode="none"`:** This server is not started as a subprocess, and no health check is performed at startup. All tool calls routed to this server are immediately rejected with a `"disabled (startup_mode=none)"` error by the `ToolExecutor` startup mode check before attempting network access. This is the default if `startup_mode` is omitted in the config — to make the server available, you must explicitly specify `"persistent"` or `"subprocess"`.

**Validation Rules:**
- `transport="http"` → `url` must not be empty and must be a valid HTTP/HTTPS URL.
- `startup_mode="subprocess"` → `cmd` must not be empty.

---

## Related Documents

- [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)

## Keywords

configuration
McpServerConfig
key
idle_timeout_sec (deprecated/unimplemented)
