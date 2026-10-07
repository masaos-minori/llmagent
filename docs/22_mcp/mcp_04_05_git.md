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
| `allowed_repo_paths` | fail-closed; empty = reject all; the caller's `repo_path` is resolved via `Path.resolve()` and checked for component-aware containment under a configured entry (configured entries are used as written, so list canonical absolute paths) |
| `read_only` | Unless explicitly set to false, write tools are disabled (`Tool disabled: read_only=true` at `/v1/call_tool`; `[DENIED] git-mcp is configured with read_only=true` if the service guard is reached directly) |
| `max_log_entries` | Limit on `git_log` entries |
| `auth_token` | Bearer token for MCP server call authentication |
| `protected_branches` | branch names protected against write tools (see Protected branch authority); empty = none protected |
| `allow_detached_head` | when true, the detached-HEAD precondition is skipped for non-dry-run write calls; default is fail-closed |
| `allowed_remote_urls` | normalized remote URLs permitted for `git_pull`/`git_push`; empty = deny all |

Current default values are defined in `config/git_mcp_server.toml`.

**Note:** `audit_log_path` is not set in `config/git_mcp_server.toml`, and git operations are not logged to a configured path. The `GitConfig.audit_log_path` field (default "") remains in `git_models.py` but has no effect.

**Note:** `git_show` output is truncated at a fixed character limit. The `inputSchema` for `git_log` sets `max_entries` with its own default, which differs from the config's `max_log_entries` value shown in the table above.

### Implementation Notes

- The `GitConfig.audit_log_path` field is not referenced or written to anywhere in `GitService`/`git_server.py`. Call logging is attempted by `git_server.py::call_tool` via `mcp_servers.audit._audit_log` using the standard `logging.getLogger(__name__)` (module logger); there is no implementation for writing directly to a specified path. Unlike `github-mcp` (`service_security.py`), `shell-mcp` (`service.py`), and `file-delete-mcp` (`delete_service.py`), which have dedicated logic to open and append to `audit_log_path`, `git-mcp` has no equivalent implementation. (Explicit in code)
- All five write tools (`git_add`/`git_commit`/`git_checkout`/`git_pull`/`git_push`) use a common path through `GitService._run_tool()` in `git_service.py`: `_validate_repo()` checks `allowed_repo_paths` and then the `read_only` write guard determined by the `_WRITE_TOOLS` frozenset, and the call then runs through `WriteProtectionPipeline` (authorization, preconditions, HEAD re-check, execution, postcondition). `git_checkout`/`git_pull`/`git_push` additionally run `_validate_ref()` and `_validate_protected()` on the `branch` argument (and `_validate_ref()` on `remote`) before the pipeline. There is no Forced-Checkout rejection or pull-strategy enforcement; Force Push is not reachable because the schema has no `force` field. (Explicit in code — `scripts/mcp_servers/git/git_service.py`, `scripts/mcp_servers/git/repository_state.py`)
- `GitSecurityGuards` in `git_security.py` is not a base class of `GitService` and is not used on the request path; the guards that run are the `GitService` methods and the `RepositoryState`/`WriteProtectionPipeline` checks. (Explicit in code — `scripts/mcp_servers/git/git_service.py`)
- `git_commit` throws `GitServiceError("nothing staged to commit")` if `dry_run=false` and there are no staged changes. Other write tools do not have this type of "pre-execution condition check." (Explicit in code)
- Since repositories are opened with `search_parent_directories=False` using `git.Repo`, `repo_path` must point to the repository root (the directory containing `.git`); providing a subdirectory results in a `GitServiceError` wrapping a `git.InvalidGitRepositoryError`. (Explicit in code)

## Write protection policy

See also: `security_02_high-risk-tool-common-policy.md` Layered protection model for the general framework this section instantiates.

### Purpose

Agent-side approval confirms user intent; it does not verify that a `git_checkout`/`git_pull`/`git_push` call is technically safe. Git MCP MUST enforce its own technical constraints independently of Agent-side approval. Today it only partially does so — this section states current behavior plainly and separates it from target policy.

### Common guard

`git_server.py::call_tool` rejects a disabled tool (reason `allowed_repo_paths is empty` or `read_only=true`) before anything else, then resolves `repo_path` via `Path.resolve()` and checks containment in `allowed_repo_paths` (symlink- and traversal-based escapes are rejected). `GitService._validate_repo()` repeats the allowlist check and rejects write tools when `read_only` is true. These checks cover all five write tools uniformly (Explicit in code). Additionally, `WriteProtectionPipeline` in `repository_state.py` runs `verify_authorization()` (protected current branch and ref validity), `verify_preconditions()`, a HEAD-identity re-check, and `verify_postcondition()` around the mutating call.

### Command-specific guard status: partially implemented

A command-specific guard exists for protected-branch enforcement via `GitService._validate_protected()` (requested branch) and `RepositoryState.verify_authorization()` (current branch), enforcing `GitConfig.protected_branches` (configured in `config/git_mcp_server.toml`). However, no guard distinguishes `git_checkout`/`git_pull`/`git_push` from the other write tools or from each other for the following: Forced-Checkout rejection, Force-Push blocking, pull-strategy enforcement, or remote/ref value validation. `branch` and `remote` are passed through to GitPython as unvalidated strings.

### `git_checkout` policy

- **Current:** `verify_preconditions()` rejects a dirty worktree and a detached HEAD (unless `allow_detached_head`/`dry_run` apply); no distinction between branch checkout and path checkout; no Forced-Checkout rejection (see exploitable consequence above); no submodule-side-effect handling.
- **Target:** Dirty Worktree SHOULD be rejected unless a documented safe exception applies; Forced Checkout MUST be rejected; Detached HEAD SHOULD be rejected unless explicitly permitted; the approval preview SHOULD identify the current branch, target ref, and affected worktree state.

### `git_pull` policy

- **Current:** before any mutating call, the remote's current URL is resolved and must appear in `GitConfig.allowed_remote_urls` (an empty list denies all; a rejected remote is reported with a redacted URL); the remote and branch are then forwarded to `repo.git.pull()`; pull strategy (fast-forward-only vs. merge vs. rebase) is not set by Git MCP and is entirely determined by the ambient `git` configuration of the repository/environment; `verify_preconditions()` applies the same dirty-worktree/detached-HEAD guard as all write tools; conflict handling is whatever `git`'s own failure produces, wrapped into `GitServiceError`.
- **Target:** pull SHOULD use an explicit, fast-forward-only strategy for unattended execution; merge/rebase MUST require separately documented policy; Dirty Worktree MUST cause rejection; conflicts MUST NOT be reported as success.

### `git_push` policy

- **Current:** `GitConfig.protected_branches` is enforced (see §Protected branch authority below); no technical Force-Push block — `GitPushRequest` exposes no `force` field and `format_push()` never passes `--force` to `repo.git.push()`, so Force Push is not reachable through this tool at all (a guard would have nothing to guard); no ref-deletion, mirror-push, or multiple-ref distinctions (the schema does not expose them, but option-injection-shaped `branch`/`remote` values are already rejected by `_is_safe_ref()`); the remote's current URL must appear in `GitConfig.allowed_remote_urls` before the push runs (the same gate as `git_pull`).
- **Target:** Force Push MUST be blocked by the normal `git_push` operation; protected branches MUST reject direct push unless a separately approved policy allows it; remote and destination ref MUST be resolved and validated explicitly; a push rejected by the remote MUST NOT be reported as success. If Force Push is ever required operationally, it MUST be a separate, more strongly authorized administrative capability — not an option of the normal `git_push` tool.

### Protected branch authority

`GitConfig.protected_branches` (a `list[str]`, configured via `git_mcp_server.toml`) is the policy source and is enforced in two places (Explicit in code — `scripts/mcp_servers/git/git_service.py`, `scripts/mcp_servers/git/repository_state.py`):

- Requested branch: `GitService._validate_protected()` rejects `git_checkout`, `git_pull`, and `git_push` when the `branch` argument equals a listed name (exact, case-sensitive string match) with `[DENIED] branch is a protected branch`. An empty `branch` is rejected with `[DENIED] branch must not be empty`; because the pull/push schemas default `branch` to an empty string, these two tools are rejected unless `branch` is supplied.
- Current branch: `RepositoryState.verify_authorization()` (Stage 3 of the pipeline) rejects every write tool, including `git_add` and `git_commit`, when HEAD is on a listed branch (names are normalized to `refs/heads/<name>` and compared case-insensitively), with `[DENIED] {active_branch!r} is a protected branch`.

Unlike GitHub MCP's `protected_branches` (a distinct, unrelated setting on `GitHubConfig`), which supports fnmatch patterns, the git-mcp list has no pattern support; the two settings MUST NOT be assumed equivalent.

### Approval level

`git_checkout`/`git_pull`/`git_push` are tiered `WRITE_DANGEROUS` and have an explicit `"high"` override in `agent.toml::approval_risk_rules`, so they require full-word `yes` confirmation — see `mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`.

### Structured rejection codes (current)

Git MCP returns free-form strings, not stable codes: `[DENIED] git-mcp is configured with read_only=true` (read-only), `[DENIED] repo_path not in allowed paths` (repository-path; `[DENIED] allowed_repo_paths is empty` when the list is empty), `[DENIED] branch is a protected branch` or `[DENIED] {active_branch!r} is a protected branch` (protected-branch; see Protected branch authority), `[DENIED] Ref {ref!r} looks like a CLI option` (option-injection via `_is_safe_ref()`/`_validate_ref()`), `[DENIED] worktree has uncommitted changes (dirty worktree)` (dirty worktree via `verify_preconditions()`), `[DENIED] repository is in a detached HEAD state` (detached HEAD via `verify_preconditions()`), and operation-specific messages from `verify_postcondition()` (e.g., `expected branch {requested_branch!r}, got {post_state.active_branch!r}` for checkout, `pull postcondition failed: unresolved merge conflicts remain` for pull, `push postcondition failed: {result}` for push). These lack a *stable rejection code* (as opposed to a free-form message) — still true.

### Postcondition verification: implemented

`WriteProtectionPipeline.verify_postcondition()` (`scripts/mcp_servers/git/repository_state.py`) implements per-tool checks: for `git_checkout`, compares `post_state.active_branch` against `requested_branch`; for `git_pull`, checks `post_state._repo.index.unmerged_blobs()` for unresolved conflicts; for `git_push`, parses the result string for `"rejected"` or `"error"` markers. The method is called from `WriteProtectionPipeline.run()` before returning a success result.

### Audit

`git_server.py::call_tool` calls `_audit_log()` (through `_audit_log_safe()`) for every call that passes argument validation (a disabled-tool or schema-validation rejection is not audited). On a dispatched call, `target` is the resolved canonical repository path and `pre_condition`/`post_condition` carry the serialized `RepositoryState` (path, dirty flag, head type, active branch, untracked-file count, protected-branch flag, ref validity); on a path-resolution, path-containment, or repository-existence rejection, `target` is empty and `pre_condition`/`post_condition` are null. The call additionally passes `requested_target` (sanitized caller value) and `canonical_target`, but the shared `_audit_log()` signature in `scripts/mcp_servers/audit.py` has no such parameters, so the call raises `TypeError`, which `_audit_log_safe()` swallows and reports only as an `audit_log failed` error log line; as a result no audit record is currently emitted for git-mcp calls. `audit_log_path` in `GitConfig` is present but unused — no code path writes to it. (Explicit in code — `scripts/mcp_servers/git/git_server.py`, `scripts/mcp_servers/audit.py`)

The audit-call failure described above is tracked as MCP-001 in `governance_03_issue-and-uncertainty-management.md`. The `git_pull`/`git_push` schema default for an empty `branch` conflicts with the validation described under Protected branch authority; this is tracked as MCP-002.


## Keywords

- mcp
- server-catalog
- git
