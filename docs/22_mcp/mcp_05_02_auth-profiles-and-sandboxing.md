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
  - mcp_05_05_mdq-enforcement-and-lockdown.md
  - agent_08_01_configuration-loading-agent-config.md
---
# MCP Security and Safety Model: Authentication, Security Profiles, Output Limits and Sandboxing

## `read_only` Flag (git-mcp)

Default `true`: write tools are disabled. When `true`: `git_add`, `git_commit`, `git_checkout`, `git_pull`, and `git_push` are reported as disabled (`disabled_reason` `read_only=true`) and `/v1/call_tool` rejects them with `Tool disabled: read_only=true`; the service-level guard returns `[DENIED] git-mcp is configured with read_only=true` as a second layer. To enable writes, you must explicitly set it to `false`.

---

## Authentication (`auth_token`)

A non-empty `auth_token` is mandatory for every enabled MCP server entry —
there is no environment or profile in which an empty token is accepted.
`McpServerConfig._validate_auth_token()` (`scripts/shared/mcp_config.py`) raises
`ValueError` at config-load time if `auth_token` is empty, unless the server is
disabled (`startup_mode="none"`).

The server requires an `Authorization: Bearer <token>` header; a missing or mismatched token returns HTTP 401. Applies to: All HTTP MCP servers, including mdq-mcp (configured per server via `McpServerConfig.auth_token`). Each server verifies the token from its own server-side `auth_token`, resolved from the same environment variable the agent configuration uses; every HTTP MCP server refuses to start when that value is empty, so an empty or missing token cannot leave it unauthenticated. mdq-mcp applies its `allowed_dirs` path authorization only after authentication (see `mcp_05_05_mdq-enforcement-and-lockdown.md`).
Use environment-variable injection (`"${ENV:VAR_NAME}"`) rather than a literal
secret in the TOML file — see section 2.5 (MCP Authentication Tokens) of the deployment document for the current setup steps.

---

## Security Profile (`security_profile`)

`SecurityProfile` has a single `PRODUCTION` member, so `security_profile` does not distinguish environments. The authentication-mandatory behavior described above under [Authentication](#authentication-auth_token) applies unconditionally in every environment; there is no profile value that relaxes it.

**Enforcement Point:** An empty `auth_token` is rejected without branching on `security_profile`: `McpServerConfig` construction itself rejects it, the shell, github, file-read, file-write, file-delete, and mdq servers refuse to start when their own server-side value is empty, and Agent startup records a FATAL `mcp_auth` outcome for any `[mcp_servers.*]` entry with an empty `auth_token`. Each server also reports `common.auth_token` in its own Security Posture as `warning` when the value is empty, so the gap stays visible on `/health`. `shell_sandbox_backend == "none"` is rejected by shell-mcp's own posture check (see [mcp_04_02_file-write-file-delete-shell.md](./mcp_04_02_file-write-file-delete-shell.md)).

**Reload Boundary:** `/reload` does not re-run these checks nor apply `auth_token` changes to running MCP servers — token changes always require a restart (see [Configuration: Hot-reload eligibility](../23_agent/agent_08_01_configuration-loading-agent-config.md#configuration-file-ownership)). Production authentication validation is performed only at startup; there are no runtime paths to weaken or bypass this.

**Config Read Boundary:** The Agent layer does not read MCP server configuration files and imports no MCP server configuration models. Each server reads only its own config file and validates it at startup; the Agent consumes only the security posture each server publishes on `GET /health` (see [ADR-002](../10_adr/adr_02_01_002_platform-config-isolation.md)).

---

## Output and Resource Limits

Every limit below is set by the owning server; values are owned by the server config files and fixed code limits.

- All servers: maximum response size (`MCP_MAX_RESPONSE_BYTES`, truncated).
- shell-mcp: output (`max_output_kb`), memory (`max_memory_mb`, `RLIMIT_AS`), timeout (`max_timeout_sec`).
- file-read-mcp `max_read_bytes`; file-write-mcp `max_write_bytes`; github-mcp `max_per_page`; cicd-mcp `max_log_size_kb` plus a fixed job limit; git-mcp `git_show` fixed character limit.

---

## Sandbox Backend (shell-mcp)

| Backend | Use Case | Permitted? | Startup Behavior |
|---|---|---|---|
| `firejail` | Process isolation, restricted filesystem | Yes | `RuntimeError` if the binary is missing |
| `none` | No isolation | No | Rejected by shell-mcp itself: `init_sandbox()` raises `RuntimeError` and the `server.sandbox_backend` posture check reports `failed`, so shell-mcp refuses to bind and Agent startup aborts, regardless of environment |

- The code default and the checked-in `config/shell_mcp_server.toml` value are both `"firejail"`, which prepends `["firejail", "--private", "--net=none", "--noroot", "--"]` to `argv`. With `"none"` only `RLIMIT_*` resource limits would apply.
- An unrecognized backend value is also rejected as unsupported by the same posture check.

Installing firejail: `sudo apt-get install firejail` (Debian/Ubuntu) or `apk add firejail` (Alpine). Verify: `firejail --version`.

**Resource Limits** (applied to the child process before exec): CPU time, address space, open files, process count, and written file size

## Keywords

- mcp
- security
- safety-model
- auth-token
- security-profile
- production
- firejail
- sandbox-backend
- resource-limits
- output-limits
