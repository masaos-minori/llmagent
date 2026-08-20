# Major Default Values

| Parameter | Default | Production Recommendation | Config File |
|---|---|---|---|
| Max response bytes | 512 KB | — | Hardcoded in `scripts/mcp_servers/server.py` (`MCP_MAX_RESPONSE_BYTES`) |
| `call_timeout_sec` | 60.0s | — | `McpServerConfig.call_timeout_sec` (`shared/mcp_config.py`) |
| Tool cache TTL | 300s | — | `config/agent.toml::tool_cache_ttl` (Default for `ToolConfig.tool_cache_ttl` is also the same) |
| Tool cache max size | 200 entries | — | `config/agent.toml::tool_cache_max_size` (Default for `ToolConfig.tool_cache_max_size` is also the same) |
| Health registry threshold | 3 failures | — | Hardcoded in `shared/mcp_health.py` (`McpServerHealthRegistry.__init__`'s `failure_threshold` argument); `shared/mcp_config.py` only re-exports said class (Explicit in code) |
| `startup_timeout_sec` | 30s | — | `McpServerConfig.startup_timeout_sec` (`shared/mcp_config.py`) |
| GitHub `default_per_page` | 10 (module constant `DEFAULT_PER_PAGE`, `models_config.py`) | — | Hardcoded. `config/github_mcp_server.toml::default_per_page` was removed on 2026-07-13 (unused dead setting. Details: [04_mcp_04_01](04_mcp_04_01_web-search-file-read-github.md)) |
| GitHub `max_per_page` | 100 | — | `config/github_mcp_server.toml` (this is an active setting used for clamping `per_page`) |
| Shell `max_timeout_sec` | 300s | — | `config/shell_mcp_server.toml` |
| Shell `sandbox_backend` | `"none"` | **`"firejail"`** (`none` = sandbox disabled) | `config/shell_mcp_server.toml` |
| Git `max_log_entries` | 50 | — | `config/git_mcp_server.toml` |

**Note:** Comments within `config/shell_mcp_server.toml` include operational guidance stating: "In production environments, set `shell_sandbox_backend = \"firejail\"` and ensure the `firejail` binary is available in your PATH" (If `firejail` is not found when unset, a `RuntimeError` occurs: `mcp_servers/shell/service_static_helpers.py`). However, this value is a config file parameter and does not automatically switch based on the `security_profile` (Explicit in code).

---

## Related Documents

- [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)

## Keywords

configuration
