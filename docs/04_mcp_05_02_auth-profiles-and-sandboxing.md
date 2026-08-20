# MCP Security and Safety Model: Authentication, Security Profiles, Output Limits and Sandboxing

## `read_only` Flag (git-mcp)

```toml
read_only = true   # default: all write tools return [DENIED]
```

When set to `true`: `git_add`, `git_commit`, `git_checkout`, `git_pull`, and `git_push` will all return `[DENIED]` regardless of authorization. To enable writes, you must explicitly set it to `false`.

---

## Authentication (`auth_token`)

```toml
# In server config or McpServerConfig
auth_token = ""   # empty = no auth
```

If not empty: The server requires an `Authorization: Bearer <token>` header.
Missing or mismatched token $\rightarrow$ HTTP 401.
Applies to: All servers (configured per server via `McpServerConfig.auth_token`).

**Local/Development Compatibility:** Setting `auth_token=""` (no Bearer authentication) is an intentional behavior for local/development compatibility and is not an oversight. **Do not use an empty `auth_token` in production** — enforcement during startup is described in the [Security Profile](#security-profile-security_profile) section below.

---

## Security Profile (`security_profile`)

### Security profile (security_profile)

```toml
# In config/agent.toml [mcp_servers] section
security_profile = "local"   # or "production"
```

Controls whether Bearer token authentication is mandatory for HTTP MCP servers.

| Profile | Behavior |
|---|---|
| `local` (default) | Authentication is optional. If `auth_token` is missing on an HTTP server, a warning is issued at startup. |
| `production` | Authentication is mandatory. If any HTTP server lacks an `auth_token`, startup fails with a `RuntimeError`. |

**Enforcement Point:** `agent/repl_health.py::audit_security_defaults()` raises an exception at startup if `security_profile == "production"` and an HTTP server has an empty `auth_token`. It also warns about `shell_sandbox_backend == "none"` and empty `tool.allowed_tools`.

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
shell_sandbox_backend = "none"    # WARNING at startup; no isolation
# Production:
shell_sandbox_backend = "firejail"  # RuntimeError at startup if binary missing
```

| Backend | Use Case | Required in Production? | Startup Behavior |
|---|---|---|---|
| `firejail` | Process isolation, restricted filesystem | **Yes** | `RuntimeError` if binary is missing |
| `none` | Development only — no isolation | No | Logs a WARNING; `RuntimeError` in production mode |

- `"firejail"`: Prepends `["firejail", "--private", "--net=none", "--noroot", "--"]` to `argv`.
- `"none"`: No sandbox; only `RLIMIT_*` resource limits applied.

**Startup Enforcement** (added in plan 20260626-091916):
- If `backend == "firejail"` and `shutil.which("firejail")` returns `None` $\rightarrow$ `RuntimeError` at startup.
- If `backend != "firejail"` and `backend != "none"` $\rightarrow$ WARNING at startup.
- If `backend == "none"` in production mode $\rightarrow$ `RuntimeError`.

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
