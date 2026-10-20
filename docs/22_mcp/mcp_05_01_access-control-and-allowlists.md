---
title: "MCP Security and Safety Model: Access Control, Paths, Repos and Allowlists"
area: mcp
tags:
  - mcp
  - security
  - safety-model
  - access-control
related:
  - mcp_00_document-guide.md
  - mcp_05_02_auth-profiles-and-sandboxing.md
  - mcp_05_03_fail-open-fail-closed-and-risk-tiers.md
  - mcp_05_04_mdq-rag-boundary.md
  - mcp_05_05_mdq-enforcement-and-lockdown.md
  - security_02_high-risk-tool-common-policy.md
  - mcp_04_01_web-search-file-read-github.md
  - mcp_04_05_git.md
---

# MCP Security and Safety Model: Access Control, Paths, Repos and Allowlists

- Server Catalog → [mcp_04_01_web-search-file-read-github.md](mcp_04_01_web-search-file-read-github.md)

## Purpose

To document a common security model across servers. It covers access control, allowlist/denylist patterns, fail-open vs fail-closed policies, sandboxing, output restrictions, risk tiers, and notes on AI safety.

---

## Per-Server Access Control

| Server | Control Mechanism | Default Policy |
|---|---|---|
| file-read-mcp | `allowed_dirs` | Path jail restricted to configured directories |
| file-write-mcp | `allowed_dirs` (write) | Path jail restricted to configured directories |
| file-delete-mcp | `allowed_dirs` | Path jail restricted to configured directories |
| github-mcp | `allowed_repos` | Fail-closed (empty = all writes denied) |
| shell-mcp | `command_allowlist` + `shell_cwd_allowed_dirs` | Deny-all (both are empty by default) |
| cicd-mcp | `repo_allowlist` + `workflow_allowlist` | Both: fail-closed |
| git-mcp | `allowed_repo_paths` + `read_only` | Fail-closed (empty paths = all denied); `read_only=true` |
| mdq-mcp | `allowed_dirs` | Fail-closed (default `[]` = all denied); raises `MdqAuthorizationError` |

---

## Path Control

### `allowed_dirs` (File Servers)

- All paths are resolved via `Path.resolve()` before comparison (eliminating `../` and symbolic links).
- Access outside `allowed_dirs` returns HTTP 403.
- An empty list denies all access (fail-closed).

### `allowed_repo_paths` (git-mcp)

- The caller-supplied `repo_path` is resolved with `Path.resolve()` per call and must be contained (component-aware) under a configured entry; a leading `~` in a configured entry is expanded to the server user's home directory when the configuration is loaded, and entries are otherwise compared as written.
- Empty denies all repository access (fail-closed); all git tools are reported disabled with reason `allowed_repo_paths is empty`.
- `read_only` (default true) disables the write tools; `protected_branches` rejects write tools on matching branches; see [mcp_04_05_git.md](./mcp_04_05_git.md).

---

## Repository Control

### `allowed_repos` (github-mcp)

- Empty denies all repository access (fail-closed); otherwise only listed repositories are allowed.
- Applies to every write operation (branch, file, issue, comment, and pull request create/update/merge, plus delete and push). The tool list is owned by [mcp_01_tool_ownership_matrix.md](mcp_01_tool_ownership_matrix.md).

### `repo_allowlist` (cicd-mcp)

- Empty denies all (fail-closed).

---

## Branch and Path Denylists (github-mcp)

### `protected_branches`

- fnmatch patterns (for example `main`, `release/*`); applies to write operations targeting a matching branch. Empty (default) allows all branches. An omitted `branch=""` resolves the default branch via the API before checking.
- A match always raises `GitHubAuthorizationError` (`_assert_allowed_branch`). No approval flow can override it: Agent-layer approval and github-mcp's `protected_branches` are independent layers.

### `path_denylist`

- fnmatch glob patterns (for example `.github/**`, `Dockerfile*`); applies to `github_create_or_update_file`, `github_push_files`, and `github_delete_file`. Empty (default) allows all paths.
- A matching change (for example to GitHub Actions workflows or Docker files) is blocked regardless of approval status.

### `allow_force_push`

- Default `false`. It only controls whether `merge_method="rebase"` can be used with `merge_pull_request` (`scripts/mcp_servers/github/github_service_pull_requests.py`); if `false`, rebase merges are rejected with `GitHubAuthorizationError`.
- Keep `false` in production: rebase merging rewrites history and can disrupt team collaboration. github-mcp has no tool that executes a force-push itself. A legitimate force-push (ref update) must not be enabled through this setting; use the GitHub UI with appropriate permissions.

### `require_pr_review`

- Default `true`. `github_merge_pull_request` rejects the merge with `GitHubAuthorizationError` unless the pull request has at least one `APPROVED` review. If `false`, a pull request can be merged without an approved review (subject to other protections).
- It does not control direct commits: writes targeting a branch matched by `protected_branches` are rejected by `protected_branches`, independent of this setting. Keeping mainline branches out of direct writes is the job of `protected_branches`.

---

## Command Allowlist (shell-mcp)

- `command_allowlist` matches the base name of `argv[0]`; empty denies all commands (fail-closed).
- If `shell_cwd_allowed_dirs` is empty, all `cwd` values are denied.

### Environment Variable Filtering

``` text
env_allowlist non-empty  → keep only listed keys (denylist ignored)
env_allowlist empty      → remove denylist pattern matches
both empty               → use req.env as is
```

---

## Workflow Allowlist (cicd-mcp)

**Policy: fail-closed.** If `workflow_allowlist` is empty, all workflow trigger requests are rejected with a `CicdAuthorizationError`. This is consistent with `repo_allowlist`.

`trigger_workflow` compares the request's `workflow` value with the entries by exact match, so entries must use the form callers pass: a workflow file name such as `ci.yml` (not a repository path). The checked-in configuration uses this file-name form.

An empty `workflow_allowlist` is reported by the cicd-mcp server process in two ways:

- **Server log:** `CiCdGuards.__init__` (`scripts/mcp_servers/cicd/cicd_service_guards.py`) logs a warning that all workflow triggers will be denied.
- **Security Posture:** `validate_cicd_security()` reports `server.workflow_allowlist` as `failed` with reason `allowlist_empty`, so cicd-mcp refuses to bind its HTTP port and Agent startup aborts. Each server validates its own settings; the Agent does not audit server configuration (see [ADR-004](../10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md)).

## Keywords

- mcp
- security
- safety-model
- access-control
- allowed-dirs
- allowed-repos
- allowed-repo-paths
- protected-branches
- path-denylist
- command-allowlist
- workflow-allowlist
- read-only
