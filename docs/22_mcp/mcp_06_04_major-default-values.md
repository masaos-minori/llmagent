---
title: "Major Default Values"
area: mcp
tags:
  - mcp
  - configuration
  - defaults
related:
  - mcp_06_02_configuration-file-inventory.md
---
# Major Default Values

| Parameter | Meaning | Production Recommendation | Config File |
|---|---|---|---|
| Max response bytes | Upper bound on a single MCP response body | — | Hardcoded in `scripts/mcp_servers/server.py` (`MCP_MAX_RESPONSE_BYTES`) |
| `call_timeout_sec` | Per-call timeout for tool calls | — | `McpServerConfig.call_timeout_sec` (`shared/mcp_config.py`) |
| Health registry threshold | Consecutive failures before a server is marked unhealthy | — | Hardcoded in `shared/mcp_health.py` (`McpServerHealthRegistry.__init__`'s `failure_threshold` argument); `shared/mcp_config.py` only re-exports said class (Explicit in code) |
| `startup_timeout_sec` | Wait limit for subprocess server readiness | — | `McpServerConfig.startup_timeout_sec` (`shared/mcp_config.py`) |
| GitHub `default_per_page` | Page size used when the caller omits `per_page` (module constant `DEFAULT_PER_PAGE`, `github_models_config.py`) | — | Hardcoded; not a configuration key (Details: [mcp_04_01](mcp_04_01_web-search-file-read-github.md)) |
| GitHub `max_per_page` | Upper clamp for `per_page` (active setting) | — | `config/github_mcp_server.toml` |
| Shell `max_timeout_sec` | Upper limit for a shell command timeout | — | `config/shell_mcp_server.toml` |
| Shell `sandbox_backend` | Sandbox backend selection (`none` = sandbox disabled) | **`"firejail"`** | `config/shell_mcp_server.toml` |
| Git `max_log_entries` | Upper limit on log entries returned | — | `config/git_mcp_server.toml` |

Current default values are defined in the config files and code symbols listed above.

**Note:** Comments within `config/shell_mcp_server.toml` include operational guidance stating: "In production environments, set `shell_sandbox_backend = \"firejail\"` and ensure the `firejail` binary is available in your PATH" (If `firejail` is not found when unset, a `RuntimeError` occurs: `mcp_servers/shell/service_static_helpers.py`). However, this value is a config file parameter and does not automatically switch based on the `security_profile` (Explicit in code).

---

## Keywords

configuration
