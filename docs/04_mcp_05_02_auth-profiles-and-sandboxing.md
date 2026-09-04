---
title: "MCP Security and Safety Model: Authentication, Security Profiles, Output Limits and Sandboxing"
area: mcp
tags:
  - mcp
  - security
  - authentication
related:
  - 04_mcp_05_01_access-control-and-allowlists.md
  - 04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md
---
# MCP Security and Safety Model: Authentication, Security Profiles, Output Limits and Sandboxing

## `read_only` Flag (git-mcp)

```toml
read_only = true   # default: all write tools return [DENIED]
```

When set to `true`: `git_add`, `git_commit`, `git_checkout`, `git_pull`, and `git_push` will all return `[DENIED]` regardless of authorization. To enable writes, you must explicitly set it to `false`.

---

## Authentication (`auth_token`)

**Note (2026-09-04)**: a non-empty `auth_token` is mandatory, unconditionally, for
every HTTP MCP server — there is no environment or profile in which an empty
token is accepted (`plans/done/20260903-092407_plan.md`, "mcpauth").
`McpServerConfig._validate_auth_token()` (`scripts/shared/mcp_config.py`) raises
`ValueError` at config-load time if `auth_token` is empty for any server using
`transport="http"`.

```toml
# In server config or McpServerConfig
auth_token = "${ENV:MCP_SHELL_AUTH_TOKEN}"   # required; non-empty for every HTTP server
```

The server requires an `Authorization: Bearer <token>` header.
Missing or mismatched token $\rightarrow$ HTTP 401.
Applies to: All servers (configured per server via `McpServerConfig.auth_token`).
Use environment-variable injection (`"${ENV:VAR_NAME}"`) rather than a literal
secret in the TOML file — see
[`02_deployment.md`'s Production-Only Migration Procedure](02_deployment.md#production-only-migration-procedure)
for the current setup steps.

---

## Security Profile (`security_profile`) — retired

**Removed 2026-09-04**: `security_profile` no longer distinguishes `local` from
`production` — `SecurityProfile` has a single `PRODUCTION` member
(`plans/done/20260903-091417_plan.md`, "localremoval"). The
authentication-mandatory behavior described above under
[Authentication](#authentication-auth_token) applies unconditionally in every
environment; there is no profile value that relaxes it.

**Enforcement Point:** `agent/services/security_audit.py::audit_security_defaults()` raises `RuntimeError` unconditionally if any HTTP MCP server has an empty `auth_token` — this check no longer branches on `security_profile`. It also raises an exception, regardless of environment, if `shell_sandbox_backend == "none"`; it separately warns about empty `tool.allowed_tools`.

**Reload Boundary:** `/reload` does not re-run these checks nor apply `auth_token` changes to running MCP servers — token changes always require a restart (see [Configuration: Hot-reload eligibility](./05_agent_08_01_configuration-loading-agent-config.md#config-file-ownership-and-hot-reload-eligibility)). Production authentication validation is performed only at startup; there are no runtime paths to weaken or bypass this.

**Audit API Isolation:** `agent/security_audit_config.py` is the sole authorized point in the agent layer for importing MCP server configuration models (`mcp_servers.shell.shell_models`, `mcp_servers.git.git_models`, `mcp_servers.github.github_models_config`, `mcp_servers.cicd.cicd_models`). It exposes four loader functions that handle four narrow scopes of DTOs (`ShellAuditConfig`, `GitAuditConfig`, `GitHubAuditConfig`, `CicdAuditConfig`) and their respective optional dependencies (`ImportError` $\rightarrow$ `None`) and config loading failures (`Exception` $\rightarrow$ `RuntimeError`).

---

## Output and Resource Limits

| Limit | Default | Server |
|---|---|---|
| Max response bytes | 512 KB (`MCP_MAX_RESPONSE_BYTES = 524288`) | All servers (truncated) |
| Max shell output | 4096 KB (config) | shell-mcp |
| Max shell memory | 512 MB (`RLIMIT_AS`) | shell-mcp |
| Max shell timeout | 300 seconds (config) | shell-mcp |
| `git_show` max chars | 8000 characters | git-mcp |
| cicd log limit | 256 KB / 5 jobs | cicd-mcp |
| Max file read | 1 MB (config) | file-read-mcp |
| Max file write | 1 MB (config) | file-write-mcp |
| GitHub per_page | 100 (config) | github-mcp |

---

## Sandbox Backend (shell-mcp)

```toml
# Development:
shell_sandbox_backend = "none"    # RuntimeError at startup (regardless of environment); no isolation
# Production:
shell_sandbox_backend = "firejail"  # RuntimeError at startup if binary missing
```

| Backend | Use Case | Required in Production? | Startup Behavior |
|---|---|---|---|
| `firejail` | Process isolation, restricted filesystem | **Yes** | `RuntimeError` if binary is missing |
| `none` | Not permitted in any environment — no isolation | No | `RuntimeError` at startup, regardless of environment |

- `"firejail"`: Prepends `["firejail", "--private", "--net=none", "--noroot", "--"]` to `argv`.
- `"none"`: No sandbox; only `RLIMIT_*` resource limits applied.

**Startup Enforcement** (added in plan 20260626-091916):
- If `backend == "firejail"` and `shutil.which("firejail")` returns `None` $\rightarrow$ `RuntimeError` at startup.
- If `backend != "firejail"` and `backend != "none"` $\rightarrow$ WARNING at startup.
- If `backend == "none"` $\rightarrow$ `RuntimeError`, regardless of environment.

Installing firejail: `sudo apt-get install firejail` (Debian/Ubuntu) or `apk add firejail` (Alpine).
Verify: `firejail --version`

**Resource Limits** (applied via `preexec_fn`): `RLIMIT_CPU`, `RLIMIT_AS`, `RLIMIT_NOFILE`, `RLIMIT_NPROC`, `RLIMIT_FSIZE`

## Related Documents

- `04_mcp_00_document-guide.md`
- `04_mcp_05_01_access-control-and-allowlists.md`
- `04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`
- `04_mcp_05_04_mdq-rag-boundary.md`
- `04_mcp_05_05_mdq-enforcement-and-lockdown.md`
- `00_security_01_architecture-and-trust-boundaries.md` — System security architecture / Trust boundaries / Threat modeling / AuthN/AuthZ / Auditing / Local vs Production / Fail-open/Fail-closed / Prompt injection responsibility boundaries
- `00_security_02_high-risk-tool-common-policy.md` — High-risk MCP tool common policy (path/repo allowlists, traversal prevention, approval-risk tier mapping)

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
