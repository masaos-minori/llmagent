---
title: "MCP Security and Safety Model: Authentication, Security Profiles, Output Limits and Sandboxing"
area: mcp
tags:
  - mcp
  - security
  - authentication
related:
  - mcp_05_01_access-control-and-allowlists.md
  - mcp_05_03_fail-open-fail-closed-and-risk-tiers.md
---
# MCP Security and Safety Model: Authentication, Security Profiles, Output Limits and Sandboxing

## `read_only` Flag (git-mcp)

```toml
read_only = true   # default: write tools are disabled
```

When set to `true`: `git_add`, `git_commit`, `git_checkout`, `git_pull`, and `git_push` are reported as disabled (`disabled_reason` `read_only=true`) and `/v1/call_tool` rejects them with `Tool disabled: read_only=true`; the service-level guard returns `[DENIED] git-mcp is configured with read_only=true` as a second layer. To enable writes, you must explicitly set it to `false`. (Explicit in code — `scripts/mcp_servers/git/git_server.py`, `scripts/mcp_servers/git/git_service.py`)

---

## Authentication (`auth_token`)

A non-empty `auth_token` is mandatory for every enabled MCP server entry —
there is no environment or profile in which an empty token is accepted.
`McpServerConfig._validate_auth_token()` (`scripts/shared/mcp_config.py`) raises
`ValueError` at config-load time if `auth_token` is empty, unless the server is
disabled (`startup_mode="none"`).

```toml
# In server config or McpServerConfig
auth_token = "${ENV:MCP_SHELL_AUTH_TOKEN}"   # required; non-empty for every HTTP server
```

The server requires an `Authorization: Bearer <token>` header.
Missing or mismatched token → HTTP 401.
Applies to: All servers except mdq-mcp (configured per server via `McpServerConfig.auth_token`). mdq-mcp attaches the auth middleware with an empty token, so it does not verify Bearer tokens at the HTTP layer (see `mcp_05_05_mdq-enforcement-and-lockdown.md`); the agent-side `auth_token` entry is still required to be non-empty.
Use environment-variable injection (`"${ENV:VAR_NAME}"`) rather than a literal
secret in the TOML file — see the Production-Only Migration Procedure for the current setup steps.

---

## Security Profile (`security_profile`)

`SecurityProfile` has a single `PRODUCTION` member, so `security_profile` does not distinguish environments. The authentication-mandatory behavior described above under [Authentication](#authentication-auth_token) applies unconditionally in every environment; there is no profile value that relaxes it.

**Enforcement Point:** `agent/services/security_audit.py::audit_security_defaults()` raises `RuntimeError` unconditionally if any HTTP MCP server has an empty `auth_token` — this check no longer branches on `security_profile`. It also raises an exception, regardless of environment, if `shell_sandbox_backend == "none"`; it separately warns about empty `tool.allowed_tools`.

**Reload Boundary:** `/reload` does not re-run these checks nor apply `auth_token` changes to running MCP servers — token changes always require a restart (see [Configuration: Hot-reload eligibility](../23_agent/agent_08_01_configuration-loading-agent-config.md#configuration-file-ownership)). Production authentication validation is performed only at startup; there are no runtime paths to weaken or bypass this.

**Audit API Isolation:** `agent/security_audit_config.py` is the sole authorized point in the agent layer for importing MCP server configuration models (`mcp_servers.shell.shell_models`, `mcp_servers.git.git_models`, `mcp_servers.github.github_models_config`, `mcp_servers.cicd.cicd_models`). It exposes four loader functions that handle four narrow scopes of DTOs (`ShellAuditConfig`, `GitAuditConfig`, `GitHubAuditConfig`, `CicdAuditConfig`) and their respective optional dependencies (`ImportError` → `None`) and config loading failures (`Exception` → `RuntimeError`).

---

## Output and Resource Limits

| Limit | Source | Server |
|---|---|---|
| Max response bytes | `MCP_MAX_RESPONSE_BYTES` | All servers (truncated) |
| Max shell output | config (`max_output_kb`) | shell-mcp |
| Max shell memory | config (`max_memory_mb`, `RLIMIT_AS`) | shell-mcp |
| Max shell timeout | config (`max_timeout_sec`) | shell-mcp |
| `git_show` max chars | fixed code limit | git-mcp |
| cicd log limit | config (`max_log_size_kb`) and fixed job limit | cicd-mcp |
| Max file read | config (`max_read_bytes`) | file-read-mcp |
| Max file write | config (`max_write_bytes`) | file-write-mcp |
| GitHub per_page | config (`max_per_page`) | github-mcp |

---

## Sandbox Backend (shell-mcp)

```toml
# Supported:
shell_sandbox_backend = "firejail"  # RuntimeError at startup if binary missing
# Rejected:
shell_sandbox_backend = "none"      # rejected by Agent startup audit (RuntimeError); no isolation
```

| Backend | Use Case | Permitted? | Startup Behavior |
|---|---|---|---|
| `firejail` | Process isolation, restricted filesystem | Yes | `RuntimeError` if binary is missing |
| `none` | Not permitted — no isolation | No | Agent startup audit raises `RuntimeError` regardless of environment; shell-mcp itself accepts the value if started independently |

- The code default and the checked-in `config/shell_mcp_server.toml` value are both `"firejail"`. (Explicit in code — `scripts/mcp_servers/shell/shell_models.py`)
- `"firejail"`: Prepends `["firejail", "--private", "--net=none", "--noroot", "--"]` to `argv`.
- `"none"`: No sandbox; only `RLIMIT_*` resource limits applied.

**Startup Enforcement**:
- If `backend == "firejail"` and `shutil.which("firejail")` returns `None` → `RuntimeError` at startup.
- If `backend != "firejail"` and `backend != "none"` → WARNING at startup.
- If `backend == "none"` → `RuntimeError`, regardless of environment.

Installing firejail: `sudo apt-get install firejail` (Debian/Ubuntu) or `apk add firejail` (Alpine).
Verify: `firejail --version`

**Resource Limits** (applied via `preexec_fn`): `RLIMIT_CPU`, `RLIMIT_AS`, `RLIMIT_NOFILE`, `RLIMIT_NPROC`, `RLIMIT_FSIZE`

## Keywords

mcp
security
safety-model
auth-token
security-profile
production
firejail
sandbox-backend
resource-limits
output-limits
