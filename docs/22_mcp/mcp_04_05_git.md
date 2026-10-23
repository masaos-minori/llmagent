---
title: "MCP Server Catalog: git-mcp"
area: mcp
tags:
  - mcp
  - server-catalog
  - git
related:
  - mcp_00_document-guide.md
  - mcp_04_01_web-search-file-read-github.md
  - mcp_04_02_file-write-file-delete-shell.md
  - mcp_04_03_rag-pipeline-and-cicd.md
  - mcp_04_04_mdq.md
  - security_02_high-risk-tool-common-policy.md
  - mcp_05_03_fail-open-fail-closed-and-risk-tiers.md
  - governance_03_issue-and-uncertainty-management.md
  - mcp_03_06_tool-runtime-availability-metadata.md
  - adr_02_03_012_mcp-git-server-side-write-enforcement.md
---

# MCP Server Catalog: git-mcp

Tool membership and risk tiers are owned by [mcp_01_tool_ownership_matrix.md](mcp_01_tool_ownership_matrix.md) and `[tool_safety_tiers]` in `config/agent.toml`; the git-mcp server does not determine or maintain tiers. Health response semantics common to all servers: [mcp_02_02](mcp_02_02_startup-modes-and-health.md).

## git-mcp

**Purpose:** Local git repository operations with two-stage safety guards.
**Startup Mode:** `subprocess` (HTTP)
**Configuration:** `config/git_mcp_server.toml` (defaults are owned by this file)
**Authentication:** No GITHUB_TOKEN required; uses local git credentials. Calls to the server itself are authenticated with the Bearer `auth_token` (resolved from `MCP_GIT_AUTH_TOKEN`), which must match the Agent-side `[mcp_servers.git]` entry.
**Remote authorization:** `allowed_remote_urls` lists the normalized remote URLs that `git_pull` and `git_push` may use. The list is fail-closed: an empty list denies every remote. It does not affect which tools are enabled, so `git_pull` and `git_push` stay listed but reject every call until a remote URL is added.

All tools are `config_dependent: true`. The write tools (`git_add`, `git_commit`, `git_checkout`, `git_pull`, `git_push`) are blocked when `read_only=true` and support `dry_run`.

### Availability metadata

`/v1/tools` reports `enabled`/`disabled_reason` per tool ([mcp_03_06](mcp_03_06_tool-runtime-availability-metadata.md)). Precedence when several conditions could disable a tool:

1. `allowed_repo_paths` empty: every tool is disabled (reason `"allowed_repo_paths is empty"`), regardless of other settings.
2. `read_only=true`: only write tools are disabled (reason `"read_only=true"`).

A disabled tool called via `/v1/call_tool` returns `Tool disabled: <reason>`.

### Configuration semantics

- `allowed_repo_paths`: fail-closed; empty rejects all. The caller's `repo_path` is resolved via `Path.resolve()` and checked for component-aware containment under a configured entry. A leading `~` is expanded to the server user's home directory at load; other entries are used as written, so list canonical absolute paths.
- `read_only`: unless explicitly set to false, write tools are disabled (`Tool disabled: read_only=true` at `/v1/call_tool`; `[DENIED] git-mcp is configured with read_only=true` if the service guard is reached directly).
- `protected_branches`: branch names protected against write tools (see Protected branch authority); empty protects none.
- `allow_detached_head`: when true, the detached-HEAD precondition is skipped for non-dry-run write calls; the default is fail-closed.
- `pull_timeout` / `push_timeout`: optional per-operation timeout (seconds); when exceeded the operation raises `TimeoutError`. Unset means no timeout.
- `max_log_entries` limits `git_log`; the `git_log` `inputSchema` `max_entries` has its own default. `git_show` output is truncated at a fixed character limit.
- `/health`: `dependencies.git` reports `git` not found in PATH (degraded, HTTP 503).
- Audit has no configured path: `GitConfig.audit_log_path` exists but is unused and no code path writes to it. Call logging goes through `_audit_log` in `git_server.py::call_tool` into the server's application log `git-mcp.log`, unlike github-mcp, shell-mcp, and file-delete-mcp, which keep dedicated audit files.

### Implementation Notes

- All five write tools share one path through `GitService._run_tool()`: `_validate_repo()` checks `allowed_repo_paths` and then the `read_only` guard, and the call runs through `WriteProtectionPipeline` (authorization, preconditions, HEAD re-check, execution, postcondition). `git_checkout`/`git_pull`/`git_push` additionally run `validate_ref_allowlist()` and `validate_protected()` on `branch` (and `validate_remote()` on `remote` for pull/push) before the pipeline. There is no Forced-Checkout rejection or pull-strategy enforcement; Force Push is prevented by the `branch` allow-list (it rejects refspec forms such as a leading `+` or `:`); the absence of a `force` field is a supporting fact, not the control (ADR-012 Rationale). Enforcement points: `git_service.py`, `git_ref_validation.py`, `repository_state.py`, `write_protection_pipeline.py` under `scripts/mcp_servers/git/`.
- `git_commit` raises `GitPolicyError("nothing staged to commit")` if `dry_run=false` and nothing is staged. This is a policy rejection, not a server error: `/v1/call_tool` returns HTTP 200 with `is_error=True`, and the audit `outcome` is `"rejected"`.
- Repositories are opened with `search_parent_directories=False`, so `repo_path` must be the repository root (the directory containing `.git`); a subdirectory yields a `GitServiceError` wrapping `git.InvalidGitRepositoryError`.

## Write protection policy

See also: `security_02_high-risk-tool-common-policy.md` Layered protection model for the general framework this section instantiates.

### Purpose

Agent-side approval confirms user intent; it does not verify that a `git_checkout`/`git_pull`/`git_push` call is technically safe. Git MCP MUST enforce its own technical constraints independently of Agent-side approval. This section states the current enforcement behavior.

### Common guard

`git_server.py::call_tool` rejects a disabled tool (reason `allowed_repo_paths is empty` or `read_only=true`) before anything else, then resolves `repo_path` via `Path.resolve()` and checks containment in `allowed_repo_paths` (symlink- and traversal-based escapes are rejected). `GitService._validate_repo()` repeats the allowlist check and rejects write tools when `read_only` is true. These checks cover all five write tools uniformly. Additionally, `WriteProtectionPipeline` (`scripts/mcp_servers/git/write_protection_pipeline.py`) runs `RepositoryState.verify_authorization()` (protected destination and ref validity) and `RepositoryState.verify_preconditions()` (both in `scripts/mcp_servers/git/repository_state.py`), a HEAD-identity re-check, and `RepositoryState.verify_postcondition()` around the mutating call. Each write runs inside that pipeline on a worker thread (`asyncio.to_thread`) rather than on the event loop, so `/health` and read tools stay responsive while a slow `git_pull`/`git_push` is in flight; the pipeline also holds a per-repository serialisation lock, so writes to the same repository are ordered one at a time. Network writes carry a configurable per-operation deadline — `git_pull`/`git_push` raise `TimeoutError` once `pull_timeout`/`push_timeout` elapses — while local writes (`git_add`/`git_commit`/`git_checkout`) run without one.

### Command-specific guard status

Git MCP enforces command-specific guards for `git_checkout`, `git_pull` and `git_push` independently of Agent-side approval (see ADR-012 in `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md`).

- **Protected branch**: the decision is made on the operation destination, not on the current branch (see Protected branch authority). `git_ref_validation.validate_protected()` rejects early, and `RepositoryState.verify_authorization()` is the authoritative check.
- **Ref validation**: write tools validate `branch` with `git_ref_validation.validate_ref_allowlist()`, an allow-list equivalent to `git check-ref-format --branch`. It rejects `+`, `:`, `^`, `~`, `?`, `*`, `[`, backslash, `..`, `@{`, whitespace, control characters, values starting with `refs/`, and `HEAD`. Read tools (`git_log` `branch`, `git_diff` `commit`, `git_show` `ref`) use `git_ref_validation.validate_ref()`, which rejects only a leading `-`, so `git_show`'s default `ref="HEAD"` and tag refs keep working.
- **Remote validation**: `git_pull` and `git_push` validate `remote` with `git_ref_validation.validate_remote()`, which rejects a leading `-` and any value outside the `[A-Za-z0-9._-]+` pattern. The remote URL is additionally gated by `allowed_remote_urls`.
- **Not provided**: Forced-Checkout rejection and pull-strategy enforcement. Force Push is prevented by the `branch` allow-list above, which rejects refspec forms such as a leading `+` or `:`; the absence of a `force` field is not itself the control (ADR-012 Rationale).

`git_status`, `git_branch`, `git_add`, and `git_commit` take no ref argument.

### `git_checkout` policy

`verify_preconditions()` rejects a dirty worktree and a detached HEAD (unless `allow_detached_head`/`dry_run` apply). There is no distinction between branch checkout and path checkout, no Forced-Checkout rejection, and no submodule-side-effect handling.

### `git_pull` policy

Before any mutating call, the remote's current URL is resolved and must appear in `GitConfig.allowed_remote_urls` (an empty list denies all; a rejected remote is reported with a redacted URL). The remote and branch are then forwarded to `repo.git.pull()`. Git MCP does not set the pull strategy (fast-forward-only, merge, or rebase); the ambient `git` configuration of the repository/environment determines it. `verify_preconditions()` applies the same dirty-worktree/detached-HEAD guard as all write tools. Conflict handling is whatever `git`'s own failure produces, wrapped into `GitServiceError`; `verify_postcondition()` rejects a result that leaves unresolved merge conflicts.

### `git_push` policy

`GitConfig.protected_branches` is enforced (see Protected branch authority). `git_ref_validation.validate_ref_allowlist()` rejects refspec forms in `branch` (a leading `+`, `:`, or a `refs/` prefix) before any GitPython call, so Force Push, ref deletion, and multiple-ref pushes cannot be expressed through this tool. This allow-list is the control; the absence of a `force` field in `GitPushRequest` and the absence of `--force` in `format_push()` are supporting facts, not the control. The remote's current URL must appear in `GitConfig.allowed_remote_urls` before the push runs (the same gate as `git_pull`). A rejected push is not postcondition-checked: `format_push()` returns the raw GitPython result, and a non-zero `git push` exit raises `GitCommandError`, which Stage 6 of the pipeline translates to `GitServiceError` (HTTP 500).

### Protected branch authority

`GitConfig.protected_branches` (a `list[str]`, configured via `git_mcp_server.toml`) is the policy source. The decision is made by one authoritative Stage 3 check plus a pre-pipeline early-rejection layer:

- Authoritative Stage 3 check: `RepositoryState.verify_authorization()` (taking `tool_name`/`requested_branch`/`protected_branches`), called by `WriteProtectionPipeline.run()` at Stage 3, compares the operation **destination** — `req.branch` for `git_pull`/`git_push`, the switch target for `git_checkout`, current HEAD for `git_add`/`git_commit` — against `GitConfig.protected_branches`, normalized to `refs/heads/<name>` and compared case-insensitively. It is the single authoritative check: a protected destination is rejected even if the pre-pipeline check is bypassed. The actually rejected branch name is reported (`[DENIED] {destination!r} is a protected branch`); the message is derived from the destination, not a fixed string.
- Pre-pipeline early-rejection layer: `git_ref_validation.validate_protected()` runs before the pipeline as defense-in-depth, comparing the same destination and reporting the actually rejected branch name (`[DENIED] {branch!r} is a protected branch`). It rejects an empty branch (`[DENIED] branch must not be empty`), which is unreachable for `git_pull`/`git_push` because `branch` is required in their schemas.

Consequence: `git_checkout` away from a protected branch (target = unprotected) is allowed; only checkout *into* a protected branch is rejected.

Unlike GitHub MCP's `protected_branches` (a distinct, unrelated setting on `GitHubConfig`), which supports fnmatch patterns, the git-mcp list has no pattern support; the two settings MUST NOT be assumed equivalent.

### Approval level

`git_checkout`/`git_pull`/`git_push` are tiered `WRITE_DANGEROUS` and have an explicit `"high"` override in `agent.toml::approval_risk_rules`, so they require full-word `yes` confirmation — see `mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`.

### Rejection messages

Git MCP returns free-form `[DENIED] ...` strings, not stable rejection codes. Categories: read-only mode, repository path outside `allowed_repo_paths` (or the list is empty), protected destination branch (reports the actually rejected destination, normalized case-insensitively), invalid write-tool ref or remote, option-like ref on read tools, dirty worktree and detached HEAD (from `verify_preconditions()`), and postcondition failures (`pull` with unresolved merge conflicts from `verify_postcondition()`; `checkout` from `format_checkout()`; `push` from Stage 6 as `git_push failed: ...`). Callers must not depend on message text.

### Postcondition verification: implemented

`RepositoryState.verify_postcondition(post_state, tool_name)` (`scripts/mcp_servers/git/repository_state.py`) implements one Stage 7 check: for `git_pull`, it inspects `post_state._repo.index.unmerged_blobs()` for unresolved conflicts. `git_checkout` is deliberately not checked there — the pipeline holds only the pre-operation snapshot, so comparing `post_state.active_branch` against the requested branch would falsely reject every successful checkout; the real checkout postcondition is enforced inside `format_checkout()` (`scripts/mcp_servers/git/format_output.py`), which refreshes its own snapshot after the mutating Git call and raises `GitServiceError` on mismatch. `git_add`, `git_commit` and `git_push` have no Stage 7 check. The method is called from `WriteProtectionPipeline.run()` (`scripts/mcp_servers/git/write_protection_pipeline.py`) before returning a success result.

### Audit

`git_server.py::call_tool` calls `_audit_log()` (through `_audit_log_safe()`, recorded in `git-mcp.log`) for every call that passes argument validation (a disabled-tool or schema-validation rejection is not audited). On a dispatched call, `target` is the resolved canonical repository path and `pre_condition`/`post_condition` carry the serialized `RepositoryState` (path, dirty flag, head type, active branch, untracked-file count, protected-branch flag, ref validity); on a path-resolution, path-containment, or repository-existence rejection, `target` is empty and `pre_condition`/`post_condition` are null. The record also carries `canonical_target` (the resolved canonical repository path) and, when the caller supplies a value, `requested_target` (the sanitized pre-resolution path), so requested and canonical targets can be correlated. Outcome values are `"ok"` (operation succeeded), `"error"` (operation failed with an exception), or `"rejected"` (operation rejected by a policy guard before execution). `GitServiceError` raises HTTP 500 (internal server error), while `GitPolicyError` raises HTTP 200 with `is_error=True` (policy rejection, not a server error).


## Keywords

- mcp
- server-catalog
- git
