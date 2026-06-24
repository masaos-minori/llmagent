# MCP Security and Safety Model

- Server catalog → [04_mcp_04_server_catalog.md](04_mcp_04_server_catalog.md)

## Purpose

Document the cross-server security model: access controls, allowlists, denylist patterns,
fail-open vs fail-closed policies, sandbox, output limits, risk tiers, and AI safety notes.

---

## Access Control by Server

| Server | Control mechanism | Default policy |
|---|---|---|
| file-read-mcp | `allowed_dirs` | `["/opt/llm"]` — path jail |
| file-write-mcp | `allowed_dirs` (write) | `["/opt/llm"]` — path jail |
| file-delete-mcp | `allowed_dirs` | `["/opt/llm"]` — path jail |
| github-mcp | `allowed_repos` + `allowed_repos_mode` | fail-closed (empty = deny all writes) |
| shell-mcp | `command_allowlist` + `shell_cwd_allowed_dirs` | deny all (both empty by default) |
| sqlite-mcp | `db_allowlist` | fail-closed (empty = deny all) |
| cicd-mcp | `repo_allowlist` + `workflow_allowlist` | repo: fail-closed; workflow: fail-open |
| git-mcp | `allowed_repo_paths` + `read_only` | fail-closed (empty paths = deny all); read_only=true |

---

## Path Controls

### `allowed_dirs` (file servers)

```toml
# config/file_read_mcp_server.toml
allowed_dirs = ["/opt/llm"]
```

- All paths are resolved via `Path.resolve()` before comparison (eliminates `../` and symlinks)
- Access outside `allowed_dirs` → HTTP 403
- Empty list behavior: all access denied (fail-closed)

### `allowed_repo_paths` (git-mcp)

```toml
# config/git_mcp_server.toml
allowed_repo_paths = ["/opt/llm/myrepo"]
```

- Paths normalized at server startup via `Path.resolve()`
- Empty → all repo access denied (fail-closed)

---

## Repository Controls

### `allowed_repos` / `allowed_repos_mode` (github-mcp)

```toml
allowed_repos = ["org/myrepo", "org/otherrepo"]
allowed_repos_mode = "fail_closed"   # default
```

| Mode | Empty list | Non-empty list |
|---|---|---|
| `fail_closed` (default) | All writes denied | Only listed repos allowed |
| `fail_open` | All repos allowed | Only listed repos allowed |

Applies to 9 write operations: `github_create_branch`, `github_create_or_update_file`, `github_push_files`,
`github_delete_file`, `github_create_issue`, `github_add_issue_comment`, `github_create_pull_request`,
`github_update_pull_request`, `github_merge_pull_request`.

### `repo_allowlist` (cicd-mcp)

```toml
repo_allowlist = []   # IMPORTANT: empty = deny all (fail-closed)
```

---

## Branch and Path Denylist (github-mcp)

### `protected_branches`

```toml
protected_branches = ["main", "master", "release/*"]   # fnmatch patterns
```

- Applies to write operations that specify a target branch
- Empty list (default): all branches allowed
- `branch=""` (omitted): resolves default branch via API before checking

### `path_denylist`

```toml
path_denylist = [".github/**", "Dockerfile*"]   # fnmatch glob patterns
```

- Applies to `create_or_update_file`, `push_files`, `github_delete_file`
- Empty list (default): all paths allowed

---

## Command Allowlist (shell-mcp)

```toml
command_allowlist = ["ls", "cat", "grep", "git", "python3"]
```

- Matches `argv[0]` basename
- Empty → all commands denied (fail-closed behavior)
- `shell_cwd_allowed_dirs` empty → all `cwd` values denied

### Environment variable filtering

```
env_allowlist non-empty  → keep only listed keys (denylist ignored)
env_allowlist empty      → remove denylist pattern matches
both empty               → use req.env as-is
```

---

## Workflow Allowlist (cicd-mcp)

```toml
workflow_allowlist = []   # empty = allow all (fail-open)
```

Compared to `repo_allowlist` which is fail-closed, `workflow_allowlist` is fail-open.
AI systems should note this asymmetry.

---

## `read_only` Flag (git-mcp)

```toml
read_only = true   # default: all write tools return [DENIED]
```

When `true`: `git_add`, `git_commit`, `git_checkout`, `git_pull`, `git_push` all return
`[DENIED]` regardless of approval. Set `false` explicitly to enable writes.

---

## Authentication (`auth_token`)

```toml
# In server config or McpServerConfig
auth_token = ""   # empty = no auth
```

When non-empty: server requires `Authorization: Bearer <token>` header.
Missing or mismatched → HTTP 401.
Applies to: all servers (configured per-server via `McpServerConfig.auth_token`).

---

## Security Profile (`security_profile`)

```toml
# In config/agent.toml [mcp_servers] section
security_profile = "local"   # or "production"
```

Controls whether Bearer-token authentication is required for HTTP MCP servers:

| Profile | Behavior |
|---|---|
| `local` (default) | Auth optional. Missing `auth_token` on HTTP servers produces a warning at startup. |
| `production` | Auth required. Startup fails with `RuntimeError` if any HTTP server lacks `auth_token`. |

Stdio servers are always exempt from this check regardless of profile.

**Enforcement point:** `audit_security_defaults()` in `agent/repl_health.py` raises during startup when `security_profile == "production"` and an HTTP server has an empty `auth_token`. It also warns on `shell_sandbox_backend == "none"`, empty `github.allowed_workflows`, and empty `tool.allowed_tools`.

---

## Output and Resource Limits

| Limit | Default | Server |
|---|---|---|
| Max response bytes | 512 KB (`MCP_MAX_RESPONSE_BYTES = 524288`) | All servers (truncation) |
| stdio call timeout | 60.0 sec (`_STDIO_CALL_TIMEOUT`) | StdioTransport |
| shell max output | 4096 KB (config) | shell-mcp |
| shell max memory | 512 MB (`RLIMIT_AS`) | shell-mcp |
| shell max timeout | 300 sec (config) | shell-mcp |
| git_show max chars | 8000 chars | git-mcp |
| cicd log limit | 256 KB / 5 jobs | cicd-mcp |
| SQLite max rows | 100 (config) | sqlite-mcp |
| file max read | 1 MB (config) | file-read-mcp |
| file max write | 1 MB (config) | file-write-mcp |
| GitHub per_page | 100 (config) | github-mcp |

---

## Sandbox Backend (shell-mcp)

```toml
shell_sandbox_backend = "none"   # or "firejail"
```

- `"firejail"`: prepends `["firejail", "--private", "--net=none", "--noroot", "--"]` to argv
- `"none"`: no sandbox; only `RLIMIT_*` resource limits applied
- Firejail not found in PATH at startup → warning log + fallback to `"none"`

**Resource limits** (applied via `preexec_fn`): `RLIMIT_CPU`, `RLIMIT_AS`, `RLIMIT_NOFILE`,
`RLIMIT_NPROC`, `RLIMIT_FSIZE`

---

## Fail-Open vs Fail-Closed Summary

| Control | Policy | Behavior when empty/unconfigured |
|---|---|---|
| `allowed_dirs` | Fail-closed | All access denied |
| `allowed_repos` (github-mcp, fail_closed mode) | Fail-closed | All writes denied |
| `allowed_repos` (github-mcp, fail_open mode) | Fail-open | All repos allowed |
| `allowed_repo_paths` (git-mcp) | Fail-closed | All access denied |
| `db_allowlist` (sqlite-mcp) | Fail-closed | All DB access denied |
| `repo_allowlist` (cicd-mcp) | Fail-closed | All repos denied |
| `workflow_allowlist` (cicd-mcp) | **Fail-open** | All workflows allowed |
| `command_allowlist` (shell-mcp) | Fail-closed | All commands denied |
| `path_denylist` (github-mcp) | Fail-open (no block by default) | All paths allowed |
| `protected_branches` (github-mcp) | Fail-open (no block by default) | All branches allowed |

### Startup Audit

`audit_security_defaults()` in `agent/repl_health.py` runs at agent startup and logs a
security posture summary. It checks the following settings by loading each server's config file:

| Setting | Server config file | Checked |
|---|---|---|
| `shell_sandbox_backend` | `shell_mcp_server.toml` | warns when `"none"` |
| `command_allowlist` | `shell_mcp_server.toml` | DENY-ALL warning when empty (fail-closed) |
| `db_allowlist` | `sqlite_mcp_server.toml` | DENY-ALL warning when empty (fail-closed) |
| `allowed_repo_paths` | `git_mcp_server.toml` | DENY-ALL warning when empty (fail-closed) |

Empty allowlist warnings use the format: `DENY-ALL detected: {setting} is empty. {server} will reject ALL requests from this category. Verify this is intentional or add allowed values to config.`

At the end of the check, a summary line is logged:

```
Security posture summary — fail-closed (deny when empty): <list>; fail-open (allow when empty): <list>
```

Fail-closed settings being empty is the intended safe default (access is denied). Fail-open
settings being empty are highlighted as warnings because they allow unrestricted access.

---

## Dry-Run Support

Tools that support `dry_run=True` (pre-execution preview without side effects):

| Server | Tools with dry_run support |
|---|---|
| file-write-mcp | `write_file`, `edit_file`, `move_file` |
| file-delete-mcp | `delete_file`, `delete_directory` |
| shell-mcp | `shell_run` (arg: `dry_run`) |
| git-mcp | `git_add`, `git_commit`, `git_checkout`, `git_pull`, `git_push` |
| cicd-mcp | `trigger_workflow` |

Agent-level: `approval_dry_run_tools` in `config/security.toml` lists tools for which
the approval flow auto-executes `dry_run=True` before showing the confirmation prompt.

---

## Risk Tier Classification

Tool risk tiers (from `config/agent.toml::tool_safety_tiers`):

| Tier | Examples | Approval |
|---|---|---|
| `READ_ONLY` | `read_text_file`, `git_status`, `search_web`, `rag_run_pipeline` | Auto-approved |
| `WRITE_SAFE` | `write_file`, `edit_file`, `git_add`, `git_commit` | `y/N` prompt |
| `WRITE_DANGEROUS` | `delete_file`, `shell_run`, `github_push_files`, `git_checkout`, `git_pull`, `git_push`, `trigger_workflow` | `yes` (full word) required |
| `ADMIN` | (custom; none by default) | `yes` required |

Tools absent from `tool_safety_tiers` default to `WRITE_DANGEROUS` (fail-safe).

---

## Notes for AI Systems

1. **Never assume write access to GitHub.** `allowed_repos` defaults to empty (fail-closed).
    Confirm `allowed_repos` is configured before attempting any GitHub write.

2. **Never assume shell commands will execute.** `command_allowlist` is empty by default.
    Check allowlist before attempting `shell_run`.

3. **`allowed_repo_paths` empty = git access denied.** Configure before using any git-mcp tool.

4. **`db_allowlist` empty = SQLite access denied.** Configure `rag` and `session` entries.

5. **`workflow_allowlist` is fail-open** (unlike `repo_allowlist`). All workflows are reachable
    unless explicitly restricted.

6. **mdq-mcp is experimental.** FTS5 indexing and search are functionally implemented but not production-validated. Use `rag-pipeline-mcp` for production workloads. See [MDQ vs RAG boundary](04_mcp_07_mdq_rag_boundary.md) for guidance.

7. **`dry_run=True` preview before destructive ops.** The approval flow in the agent
    auto-injects `dry_run=True` for registered tools before showing the user prompt.

---

## MDQ vs RAG Boundary

詳細は「[MDQ vs RAG 境界定義](04_mcp_07_mdq_rag_boundary.md)」を参照。

---

## Fail-open vs Fail-closed Defaults

"Fail-closed" means the setting denies access when the list is empty.
"Fail-open" means the setting allows all access when the list is empty.

| Server | Setting | Default | Behavior when empty |
|---|---|---|---|
| shell-mcp | `command_allowlist` | `[]` | **Fail-closed** — all shell commands denied |
| sqlite-mcp | `db_allowlist` | `[]` | **Fail-closed** — all DB queries denied |
| git-mcp | `allowed_repo_paths` | `[]` | **Fail-closed** — all repo access denied |
| github-mcp | `allowed_repos` | `[]` | **Fail-closed** — all GitHub write ops denied |
| cicd-mcp | `workflow_allowlist` | `[]` | **Fail-open** — all workflows can be triggered |
| github-mcp | `allowed_workflows` | `[]` | **Fail-open** — all workflows allowed |

### Dangerous defaults to review before production deployment

- `shell-mcp`: `sandbox_backend = "none"` (default) means no OS-level sandboxing.
  Set to `"firejail"` for production; visible in `/health` response.
- `cicd-mcp`: `workflow_allowlist = []` is fail-open; explicitly list permitted workflows.
- `github-mcp`: `allow_force_push = false` (default); `require_pr_review = true` (default).

### Startup audit

  `audit_security_defaults()` in `agent/repl_health.py` runs at startup and logs:
- All fail-closed settings that are empty (informational — access is correctly denied)
- All fail-open settings that are empty (warning — unintended access may be allowed)
- A summary line: `Security posture summary — fail-closed (...): ...; fail-open (...): ...`

---

## Intentional deny-all lockdown

An empty fail-closed allowlist disables an entire MCP server's operation category.
This is the correct behavior for security-restricted deployments that want to prevent
certain tool categories entirely (e.g., no shell commands, no DB queries).

### Which settings cause deny-all

| Setting | Server | Effect when empty |
|---------|--------|-------------------|
| `shell.command_allowlist` | shell-mcp | All shell commands denied |
| `sqlite.db_allowlist` | sqlite-mcp | All DB queries denied |
| `git.allowed_repo_paths` | git-mcp | All git operations denied |
| `github.allowed_repos` | github-mcp | All repo access denied |

### Configuring an intentional lockdown

1. Set the desired allowlist(s) to empty in the relevant TOML:
   ```toml
   # shell_mcp_server.toml
   command_allowlist = []   # deny all shell commands
   ```

2. Acknowledge the lockdown in `config/agent.toml` to suppress startup warnings:
   ```toml
   [agent]
   security_lockdown_enabled = true
   ```

3. Restart the agent. The startup log will show:
   ```
   INFO Security: security_lockdown_enabled=True — deny-all warnings suppressed
   ```

### Verifying deny-all state at runtime

At startup, `audit_security_defaults()` logs each deny-all state:
```
WARNING DENY-ALL detected: shell.command_allowlist is empty. shell-mcp will
        reject ALL shell commands. Verify this is intentional or add allowed
        commands to shell_mcp_server.toml.
```

If `security_lockdown_enabled=False` (default), these warnings appear at every
startup — a deliberate reminder to review the config. Set it to `true` only
when the deny-all state is confirmed intentional. When enabled:
- DENY-ALL warnings for fail-closed settings (`command_allowlist`, `db_allowlist`, `allowed_repo_paths`) are suppressed
- Fail-open warnings (`github.allowed_workflows`, `tool.allowed_tools`) still appear
- The security posture summary line still appears with full detail

### Reverting a lockdown

Add the allowed values back to the relevant TOML and set
`security_lockdown_enabled = false`. Restart the agent to apply.
