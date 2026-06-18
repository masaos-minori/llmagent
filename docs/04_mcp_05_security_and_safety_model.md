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

Applies to 9 write operations: `create_branch`, `create_or_update_file`, `push_files`,
`github_delete_file`, `create_issue`, `add_issue_comment`, `create_pull_request`,
`update_pull_request`, `merge_pull_request`.

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
| `WRITE_DANGEROUS` | `delete_file`, `shell_run`, `github_push_files`, `git_push`, `trigger_workflow` | `yes` (full word) required |
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

6. **mdq-mcp tools return stub data.** Do not rely on `search_docs`, `get_chunk`, etc. for
   actual content — they are placeholder implementations.

7. **`dry_run=True` preview before destructive ops.** The approval flow in the agent
   auto-injects `dry_run=True` for registered tools before showing the user prompt.
