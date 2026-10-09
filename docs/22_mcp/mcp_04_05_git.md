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
---

# MCP Server Catalog: git-mcp

## git-mcp 

**Purpose:** Local git repository operations with two-stage safety guards.
**Startup Mode:** `subprocess` (HTTP)
**Configuration:** `config/git_mcp_server.toml`
**Authentication:** No GITHUB_TOKEN required; uses local git credentials. Calls to the server itself are authenticated with the Bearer `auth_token` (resolved from `MCP_GIT_AUTH_TOKEN`), which must match the Agent-side `[mcp_servers.git]` entry. (Explicit in code — `scripts/mcp_servers/git/git_server.py`, `config/git_mcp_server.toml`)
**Remote authorization:** `allowed_remote_urls` in `config/git_mcp_server.toml` lists the normalized remote URLs that `git_pull` and `git_push` may use. The list is fail-closed: an empty list denies every remote. It does not affect which tools are enabled, so `git_pull` and `git_push` stay listed but reject every call until a remote URL is added.

**Tools:**

All tools require configuration (`config_dependent: true`).

Git server's `enabled`/`disabled_reason` calculation: If `allowed_repo_paths` is empty, it is prioritized for disabling (reason `"allowed_repo_paths is empty"`). Otherwise, if `read_only=true`, only write tools are disabled (reason `"read_only=true"`). See [mcp_03_06_tool-runtime-availability-metadata.md](mcp_03_06_tool-runtime-availability-metadata.md) for details.

### Availability metadata

The git-mcp server provides availability metadata through `/v1/tools`:

- `enabled`: Indicates whether the tool is available for LLM use
- `disabled_reason`: Provides the reason when the tool is disabled

#### Precedence rules

When multiple conditions could disable the tool, the following precedence applies:

1. If `allowed_repo_paths` is empty → tool is disabled regardless of other settings
2. If `read_only=true` and the operation requires write access → tool is disabled

This means `allowed_repo_paths is empty` takes precedence over `read_only=true`.

#### Disabled call behavior

When a disabled tool is called via `/v1/call_tool`, the response includes the concrete reason:

```
Tool disabled: <reason>
```

This matches the documented contract — no deviation exists between the documentation and implementation.

| Tool | Tier | read_only Guard | dry_run | config_dependent |
|---|---|---|---|---|
| `git_status` | READ_ONLY | — | — | yes |
| `git_log` | READ_ONLY | — | — | yes |
| `git_diff` | READ_ONLY | — | — | yes |
| `git_branch` | READ_ONLY | — | — | yes |
| `git_show` | READ_ONLY | — | — | yes |
| `git_add` | WRITE_SAFE | Blocked if read_only=true | yes | yes |
| `git_commit` | WRITE_SAFE | Blocked | yes | yes |
| `git_checkout` | WRITE_DANGEROUS | Blocked | yes | yes |
| `git_pull` | WRITE_DANGEROUS | Blocked | yes | yes |
| `git_push` | WRITE_DANGEROUS | Blocked | yes | yes |

The "Tier" column does not exist within the `scripts/mcp_servers/git/` directory itself; its values originate from `[tool_safety_tiers]` in `config/agent.toml` (the agent layer's authorization policy settings). The git-mcp server implementation does not internally determine or maintain tiers. (Explicit in code)

**Health:** If git is found: `{"status":"ok","ready":true,"liveness":true,"restart_recommended":false,"operator_action_required":false,"dependencies":{},"details":{}}`; if not found: `{"status":"degraded","ready":false,"dependencies":{"git":"git not found in PATH"/"check failed"}}` — returns HTTP 200 when ready, and 503 when degraded.
**Configuration:**

| Key | Notes |
|---|---|
| `allowed_repo_paths` | fail-closed; empty = reject all; the caller's `repo_path` is resolved via `Path.resolve()` and checked for component-aware containment under a configured entry (a leading `~` in an entry is expanded to the server user's home directory at load; other entries are used as written, so list canonical absolute paths) |
| `read_only` | Unless explicitly set to false, write tools are disabled (`Tool disabled: read_only=true` at `/v1/call_tool`; `[DENIED] git-mcp is configured with read_only=true` if the service guard is reached directly) |
| `max_log_entries` | Limit on `git_log` entries |
| `auth_token` | Bearer token for MCP server call authentication |
| `protected_branches` | branch names protected against write tools (see Protected branch authority); empty = none protected |
| `allow_detached_head` | when true, the detached-HEAD precondition is skipped for non-dry-run write calls; default is fail-closed |
| `allowed_remote_urls` | normalized remote URLs permitted for `git_pull`/`git_push`; empty = deny all |
| `pull_timeout` | Optional timeout (seconds) for `git_pull`; when the underlying call exceeds it, the operation raises `TimeoutError`. Unset = no timeout. |
| `push_timeout` | Optional timeout (seconds) for `git_push`; when the underlying call exceeds it, the operation raises `TimeoutError`. Unset = no timeout. |

Current default values are defined in `config/git_mcp_server.toml`.

**Note:** `audit_log_path` is not set in `config/git_mcp_server.toml`, and git operations are not logged to a configured path. The `GitConfig.audit_log_path` field (default "") remains in `git_models.py` but has no effect.

**Note:** `git_show` output is truncated at a fixed character limit. The `inputSchema` for `git_log` sets `max_entries` with its own default, which differs from the config's `max_log_entries` value shown in the table above.

### Implementation Notes

- The `GitConfig.audit_log_path` field is not referenced or written to anywhere in `GitService`/`git_server.py`. Call logging is attempted by `git_server.py::call_tool` via `mcp_servers.audit._audit_log` using the standard `logging.getLogger(__name__)` (module logger); there is no implementation for writing directly to a specified path. Unlike `github-mcp` (`service_security.py`), `shell-mcp` (`service.py`), and `file-delete-mcp` (`delete_service.py`), which have dedicated logic to open and append to `audit_log_path`, `git-mcp` has no equivalent implementation. (Explicit in code)
- All five write tools (`git_add`/`git_commit`/`git_checkout`/`git_pull`/`git_push`) use a common path through `GitService._run_tool()` in `git_service.py`: `_validate_repo()` checks `allowed_repo_paths` and then the `read_only` write guard determined by the `_WRITE_TOOLS` frozenset, and the call then runs through `WriteProtectionPipeline` (authorization, preconditions, HEAD re-check, execution, postcondition). `git_checkout`/`git_pull`/`git_push` additionally run `_validate_ref_allowlist()` and `_validate_protected()` on the `branch` argument (and `_validate_remote()` on `remote` for `git_pull`/`git_push`) before the pipeline. There is no Forced-Checkout rejection or pull-strategy enforcement; Force Push is not reachable because the schema has no `force` field. (Explicit in code — `scripts/mcp_servers/git/git_service.py`, `scripts/mcp_servers/git/repository_state.py`)
- `GitSecurityGuards` in `git_security.py` is not a base class of `GitService` and is not used on the request path; the guards that run are the `GitService` methods and the `RepositoryState`/`WriteProtectionPipeline` checks. (Explicit in code — `scripts/mcp_servers/git/git_service.py`)
- `git_commit` raises `GitPolicyError("nothing staged to commit")` if `dry_run=false` and there are no staged changes. This is a policy rejection, not a server error: `/v1/call_tool` returns HTTP 200 with `is_error=True`, and the audit `outcome` is `"rejected"` (see Audit). Other write tools do not have this type of "pre-execution condition check." (Explicit in code — `scripts/mcp_servers/git/format_output.py`, `scripts/mcp_servers/git/git_server.py`)
- Since repositories are opened with `search_parent_directories=False` using `git.Repo`, `repo_path` must point to the repository root (the directory containing `.git`); providing a subdirectory results in a `GitServiceError` wrapping a `git.InvalidGitRepositoryError`. (Explicit in code)

## Write protection policy

See also: `security_02_high-risk-tool-common-policy.md` Layered protection model for the general framework this section instantiates.

### Purpose

Agent-side approval confirms user intent; it does not verify that a `git_checkout`/`git_pull`/`git_push` call is technically safe. Git MCP MUST enforce its own technical constraints independently of Agent-side approval. This section states the current enforcement behavior.

### Common guard

`git_server.py::call_tool` rejects a disabled tool (reason `allowed_repo_paths is empty` or `read_only=true`) before anything else, then resolves `repo_path` via `Path.resolve()` and checks containment in `allowed_repo_paths` (symlink- and traversal-based escapes are rejected). `GitService._validate_repo()` repeats the allowlist check and rejects write tools when `read_only` is true. These checks cover all five write tools uniformly (Explicit in code). Additionally, `WriteProtectionPipeline` in `repository_state.py` runs `verify_authorization()` (protected destination and ref validity), `verify_preconditions()`, a HEAD-identity re-check, and `verify_postcondition()` around the mutating call. Each write runs inside that pipeline on a worker thread (`asyncio.to_thread`) rather than on the event loop, so `/health` and read tools stay responsive while a slow `git_pull`/`git_push` is in flight; the pipeline also holds a per-repository serialisation lock, so writes to the same repository are ordered one at a time. Network writes carry a configurable per-operation deadline — `git_pull`/`git_push` raise `TimeoutError` once `pull_timeout`/`push_timeout` elapses — while local writes (`git_add`/`git_commit`/`git_checkout`) run without one.

### Command-specific guard status

Git MCP enforces command-specific guards for `git_checkout`, `git_pull` and `git_push` independently of Agent-side approval (see ADR-012 in `docs/10_adr/ADR-012-git-mcp-server-side-write-enforcement.md`).

- **Protected branch**: the decision is made on the operation destination, not on the current branch (see Protected branch authority). `GitService._validate_protected()` rejects early, and `RepositoryState.verify_authorization()` is the authoritative check.
- **Ref validation**: write tools validate `branch` with `GitService._validate_ref_allowlist()`, an allow-list equivalent to `git check-ref-format --branch`. It rejects `+`, `:`, `^`, `~`, `?`, `*`, `[`, backslash, `..`, `@{`, whitespace, control characters, values starting with `refs/`, and `HEAD`. Read tools (`git_log` `branch`, `git_diff` `commit`, `git_show` `ref`) use `GitService._validate_ref()`, which rejects only a leading `-`, so `git_show`'s default `ref="HEAD"` and tag refs keep working.
- **Remote validation**: `git_pull` and `git_push` validate `remote` with `GitService._validate_remote()`, which rejects a leading `-` and any value outside the `[A-Za-z0-9._-]+` pattern. The remote URL is additionally gated by `allowed_remote_urls`.
- **Not provided**: Forced-Checkout rejection and pull-strategy enforcement. Force Push is not reachable because `GitPushRequest` has no `force` field.

`git_status`, `git_branch`, `git_add`, and `git_commit` take no ref argument. (Explicit in code — `scripts/mcp_servers/git/git_service.py`, `scripts/mcp_servers/git/repository_state.py`)

### `git_checkout` policy

`verify_preconditions()` rejects a dirty worktree and a detached HEAD (unless `allow_detached_head`/`dry_run` apply). There is no distinction between branch checkout and path checkout, no Forced-Checkout rejection, and no submodule-side-effect handling. (Explicit in code)

### `git_pull` policy

Before any mutating call, the remote's current URL is resolved and must appear in `GitConfig.allowed_remote_urls` (an empty list denies all; a rejected remote is reported with a redacted URL). The remote and branch are then forwarded to `repo.git.pull()`. Git MCP does not set the pull strategy (fast-forward-only, merge, or rebase); the ambient `git` configuration of the repository/environment determines it. `verify_preconditions()` applies the same dirty-worktree/detached-HEAD guard as all write tools. Conflict handling is whatever `git`'s own failure produces, wrapped into `GitServiceError`; `verify_postcondition()` rejects a result that leaves unresolved merge conflicts. (Explicit in code)

### `git_push` policy

`GitConfig.protected_branches` is enforced (see Protected branch authority). `GitPushRequest` exposes no `force` field and `format_push()` never passes `--force` to `repo.git.push()`, so Force Push is not reachable through this tool. The schema exposes no ref-deletion, mirror-push, or multiple-ref option, and `_validate_ref_allowlist()` rejects refspec forms in `branch` before any GitPython call. The remote's current URL must appear in `GitConfig.allowed_remote_urls` before the push runs (the same gate as `git_pull`). `verify_postcondition()` rejects a push result that carries a `rejected` or `error` marker. (Explicit in code)

### Protected branch authority

`GitConfig.protected_branches` (a `list[str]`, configured via `git_mcp_server.toml`) is the policy source. The decision is made by one authoritative Stage 3 check plus a pre-pipeline early-rejection layer (Explicit in code — `scripts/mcp_servers/git/repository_state.py`, `scripts/mcp_servers/git/git_service.py`):

- Authoritative Stage 3 check: `WriteProtectionPipeline.verify_authorization()` (now taking `tool_name`/`requested_branch`/`protected_branches`/`active_ref`) compares the operation **destination** — `req.branch` for `git_pull`/`git_push`, the switch target for `git_checkout`, current HEAD for `git_add`/`git_commit` — against `GitConfig.protected_branches`, normalized to `refs/heads/<name>` and compared case-insensitively. It is the single authoritative check: a protected destination is rejected even if the pre-pipeline check is bypassed. The actually rejected branch name is reported (`[DENIED] {destination!r} is a protected branch`), no longer hard-coded.
- Pre-pipeline early-rejection layer: `GitService._validate_protected()` runs before the pipeline as defense-in-depth, comparing the same destination and reporting the actually rejected branch name (`[DENIED] {branch!r} is a protected branch`). It rejects an empty branch (`[DENIED] branch must not be empty`), which is now unreachable for `git_pull`/`git_push` because `branch` is required in their schemas.

Consequence: `git_checkout` away from a protected branch (target = unprotected) is allowed; only checkout *into* a protected branch is rejected.

Unlike GitHub MCP's `protected_branches` (a distinct, unrelated setting on `GitHubConfig`), which supports fnmatch patterns, the git-mcp list has no pattern support; the two settings MUST NOT be assumed equivalent.

### Approval level

`git_checkout`/`git_pull`/`git_push` are tiered `WRITE_DANGEROUS` and have an explicit `"high"` override in `agent.toml::approval_risk_rules`, so they require full-word `yes` confirmation — see `mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`.

### Structured rejection codes (current)

Git MCP returns free-form strings, not stable codes: `[DENIED] git-mcp is configured with read_only=true` (read-only), `[DENIED] repo_path not in allowed paths` (repository-path; `[DENIED] allowed_repo_paths is empty` when the list is empty), `[DENIED] {destination!r} is a protected branch` (protected-branch; see Protected branch authority — reports the actually-rejected destination, normalized case-insensitively), `[DENIED] Ref {ref!r} is not a valid simple branch name` (write-tool allow-list for `branch`/`remote`); `[DENIED] Ref {ref!r} looks like a CLI option` (read tools retain the option-injection check), `[DENIED] worktree has uncommitted changes (dirty worktree)` (dirty worktree via `verify_preconditions()`), `[DENIED] repository is in a detached HEAD state` (detached HEAD via `verify_preconditions()`), and operation-specific messages from `verify_postcondition()` (e.g., `expected branch {requested_branch!r}, got {post_state.active_branch!r}` for checkout, `pull postcondition failed: unresolved merge conflicts remain` for pull, `push postcondition failed: {result}` for push). These lack a *stable rejection code* (as opposed to a free-form message) — still true.

### Postcondition verification: implemented

`WriteProtectionPipeline.verify_postcondition()` (`scripts/mcp_servers/git/repository_state.py`) implements per-tool checks: for `git_checkout`, compares `post_state.active_branch` against `requested_branch`; for `git_pull`, checks `post_state._repo.index.unmerged_blobs()` for unresolved conflicts; for `git_push`, parses the result string for `"rejected"` or `"error"` markers. The method is called from `WriteProtectionPipeline.run()` before returning a success result.

### Audit

`git_server.py::call_tool` calls `_audit_log()` (through `_audit_log_safe()`) for every call that passes argument validation (a disabled-tool or schema-validation rejection is not audited). On a dispatched call, `target` is the resolved canonical repository path and `pre_condition`/`post_condition` carry the serialized `RepositoryState` (path, dirty flag, head type, active branch, untracked-file count, protected-branch flag, ref validity); on a path-resolution, path-containment, or repository-existence rejection, `target` is empty and `pre_condition`/`post_condition` are null. The call additionally passes `requested_target` (sanitized caller value) and `canonical_target`; the shared `_audit_log()` signature accepts these parameters, so audit records are emitted for all dispatched calls and for path-resolution and repository-existence rejections. Each audit record includes the `canonical_target` field (the resolved canonical repository path) alongside `requested_target` (the sanitized caller-provided value). Outcome values are `"ok"` (operation succeeded), `"error"` (operation failed with an exception), or `"rejected"` (operation rejected by a policy guard before execution). `GitServiceError` raises HTTP 500 (internal server error), while `GitPolicyError` raises HTTP 200 with `is_error=True` (policy rejection, not a server error). `audit_log_path` in `GitConfig` is present but unused — no code path writes to it. (Explicit in code — `scripts/mcp_servers/git/git_server.py`, `scripts/mcp_servers/audit.py`)


## Keywords

- mcp
- server-catalog
- git
