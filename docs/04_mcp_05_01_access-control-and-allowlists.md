---
title: "MCP Security and Safety Model: Access Control, Paths, Repos and Allowlists"
area: mcp
tags:
  - mcp
  - security
  - safety-model
  - access-control
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_05_02_auth-profiles-and-sandboxing.md
  - 04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md
  - 04_mcp_05_04_mdq-rag-boundary.md
  - 04_mcp_05_05_mdq-enforcement-and-lockdown.md
  - 00_security_02_high-risk-tool-common-policy.md — High-risk MCP tool common policy (path/repo allowlists, traversal prevention, approval-risk tier mapping)
---

## config/github_mcp_server.toml

- Server Catalog → [04_mcp_04_01_web-search-file-read-github.md](04_mcp_04_01_web-search-file-read-github.md)

## Purpose

To document a common security model across servers. It covers access control, allowlist/denylist patterns, fail-open vs fail-closed policies, sandboxing, output restrictions, risk tiers, and notes on AI safety.

---

## Per-Server Access Control

| Server | Control Mechanism | Default Policy |
|---|---|---|
| file-read-mcp | `allowed_dirs` | `["/opt/llm", "/opt/llm/storage"]` — Path jail |
| file-write-mcp | `allowed_dirs` (write) | `["/opt/llm/storage"]` — Path jail |
| file-delete-mcp | `allowed_dirs` | `["/opt/llm/storage"]` — Path jail |
| github-mcp | `allowed_repos` | Fail-closed (empty = all writes denied) |
| shell-mcp | `command_allowlist` + `shell_cwd_allowed_dirs` | Deny-all (both are empty by default) |
| cicd-mcp | `repo_allowlist` + `workflow_allowlist` | Both: fail-closed |
| git-mcp | `allowed_repo_paths` + `read_only` | Fail-closed (empty paths = all denied); `read_only=true` |
| mdq-mcp | `allowed_dirs` | Fail-closed (default `[]` = all denied); raises `MdqAuthorizationError` |

---

## Path Control

### `allowed_dirs` (File Servers)

```toml
# config/file_read_mcp_server.toml
allowed_dirs = ["/opt/llm", "/opt/llm/storage"]
```

- All paths are resolved via `Path.resolve()` before comparison (eliminating `../` and symbolic links).
- Access outside `allowed_dirs` → HTTP 403.
- Behavior for empty list: Denies all access (fail-closed).

### `allowed_repo_paths` (git-mcp)

```toml
# config/git_mcp_server.toml
allowed_repo_paths = ["/opt/llm/myrepo"]
```

- Paths are normalized with `Path.resolve()` at server startup.
- Empty → Denies all repository access (fail-closed).

---

## Repository Control

### `allowed_repos` (github-mcp)

```toml
allowed_repos = ["org/myrepo", "org/otherrepo"]
```

- Empty → Denies all repository access (fail-closed).
- Not empty → Only allows repositories in the list.

Applies to the following 9 write operations: `github_create_branch`, `github_create_or_update_file`, `github_push_files`, `github_delete_file`, `github_create_issue`, `github_add_issue_comment`, `github_create_pull_request`, `github_update_pull_request`, `github_merge_pull_request`.

### `repo_allowlist` (cicd-mcp)

```toml
repo_allowlist = []   # IMPORTANT: empty = deny all (fail-closed)
```

---

## Branch and Path Denylists (github-mcp)

### `protected_branches`

```toml
# config/github_mcp_server.toml - protected_branches
protected_branches = ["main", "master", "release/*"]   # fnmatch patterns
```

- Applies to write operations targeting specified branches.
- Empty list (default): Allows all branches.
- `branch=""` (if omitted): Resolves default branch via API before checking.

**Production Example:**

```toml
# Protect mainline branches and release branches
protected_branches = [
    "main",
    "master",
    "release/*",
    "develop",
]
```

In this configuration, write operations targeting `main`, `master`, `release/v1.0`, or `develop` are unconditionally blocked. The `protected_branches` check (`_assert_allowed_branch`) always issues a `GitHubAuthorizationError`, and there is no implementation to override this via an approval flow (the agent-layer approval and github-mcp's `protected_branches` are independent layers).

### `path_denylist`

```toml
# config/github_mcp_server.toml - path_denylist
path_denylist = [".github/**", "Dockerfile*"]   # fnmatch glob patterns
```

- Applies to `create_or_update_file`, `push_files`, and `github_delete_file`.
- Empty list (default): Allows all paths.

**Production Example:**

```toml
# Prevent modifications to CI/CD configs and container definitions
path_denylist = [
    ".github/**",           # block changes to GitHub Actions/workflows
    "Dockerfile*",          # block changes to Docker files
    "docker-compose*.yml",  # block changes to docker compose configs
]
```

With this setting, changes to GitHub Actions workflows or Docker-related files are blocked regardless of approval status.

### `allow_force_push`

```toml
# config/github_mcp_server.toml - allow_force_push
allow_force_push = false   # default: force push disabled
```

- Only controls whether `merge_method="rebase"` can be used with the `merge_pull_request` tool (`scripts/mcp_servers/github/service_pull_requests.py`). If `false`, rebase merges are rejected with a `GitHubAuthorizationError`.
- **Recommended: Keep as `false` in production.** Rebase merging rewrites history and can disrupt team collaboration.
- github-mcp does not have a tool to execute a force-push itself; it only interacts with the `protected_branches` protection.

**Production Example:**

```toml
# NEVER enable force push in production
allow_force_push = false
```

If a legitimate force-push (ref update) is required, do not enable this setting; instead, use the GitHub UI directly with appropriate permissions.

### `require_pr_review`

```toml
# config/github_mcp_server.toml - require_pr_review
require_pr_review = true   # default: PR review required
```

- If `true`, write operations to protected branches require a pull request (direct commits disallowed).
- If `false`, direct commits to protected branches are allowed (subject to other protections).

**Production Example:**

```toml
# Require PR review for all protected branch writes
require_pr_review = true
```

This ensures that changes to `main`, `master`, `release/*` branches must go through the standard code review process via pull requests.

---

## Command Allowlist (shell-mcp)

```toml
command_allowlist = ["ls", "cat", "grep", "git", "python3"]
```

- Matches against the base name of `argv[0]`.
- Empty → Denies all commands (fail-closed behavior).
- If `shell_cwd_allowed_dirs` is empty → Denies all `cwd` values.

### Environment Variable Filtering

``` text
env_allowlist non-empty  → keep only listed keys (denylist ignored)
env_allowlist empty      → remove denylist pattern matches
both empty               → use req.env as is
```

---

## Workflow Allowlist (cicd-mcp)

```toml
# config/cicd_mcp_server.toml
workflow_allowlist = []   # empty = deny all (fail-closed)
```

**Policy: fail-closed.** If `workflow_allowlist` is empty, all workflow trigger requests are rejected with a `CicdAuthorizationError`. This behavior is consistent with `repo_allowlist`.

To allow specific workflows:

```toml
workflow_allowlist = [
    "my-org/my-repo/.github/workflows/deploy.yml",
    "my-org/my-repo/.github/workflows/ci.yml",
]
```

These warnings occur in two independent layers: the Agent layer and the cicd-mcp server layer.

- **Agent Layer (Agent REPL process)**: In `scripts/agent/repl_health.py::audit_security_defaults()`, if `cicd_cfg` exists and `workflow_allowlist` is empty and not locked down, a warning is issued to the REPL startup warning list (`warnings: list[str]`).
  Message: `DENY-ALL detected: cicd.workflow_allowlist is empty. cicd-mcp will reject ALL workflow trigger requests.`
- **cicd-mcp Server Layer (cicd-mcp server process)**: In `scripts/mcp_servers/cicd/cicd_service_guards.py::CiCdGuards.__init__`, if `workflow_allowlist` is empty, a warning is recorded to the server log stream via the `mcp_servers.cicd.cicd_service_guards` logger.
  Message: `cicd-mcp: workflow_allowlist is empty — all workflow triggers will be denied`

## Related Documents

- `04_mcp_00_document-guide.md`
- `04_mcp_05_02_auth-profiles-and-sandboxing.md`
- `04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`
- `04_mcp_05_04_mdq-rag-boundary.md`
- `04_mcp_05_05_mdq-enforcement-and-lockdown.md`
- `00_security_02_high-risk-tool-common-policy.md` — High-risk MCP tool common policy (path/repo allowlists, traversal prevention, approval-risk tier mapping)

## Keywords

mcp
security
safety-model
access-control
allowed-dirs
allowed-repos
allowed-repo-paths
protected-branches
path-denylist
command-allowlist
workflow-allowlist
read-only
