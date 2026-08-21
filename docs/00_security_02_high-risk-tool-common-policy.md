---
title: "High-Risk MCP Tool Common Policy"
category: security
tags:
  - security
  - policy
  - high-risk-tools
  - path-traversal
  - approval
  - audit
  - symlink-traversal
related:
  - 00_security_01_architecture-and-trust-boundaries.md
  - 00_governance_01_documentation-governance.md
  - 00_governance_02_canonical-source-rule.md
  - 04_mcp_05_01_access-control-and-allowlists.md
  - 04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md
  - 05_agent_06_01_tool-execution-and-approval-execution.md
  - 04_mcp_04_02_file-write-file-delete-shell.md
  - 04_mcp_04_04_mdq.md
  - 04_mcp_05_05_mdq-enforcement-and-lockdown.md
  - 05_agent_06_01_tool-execution-and-approval-execution.md
  - 05_agent_06_02_tool-execution-and-approval-approval.md
  - 04_mcp_06_16_pre-production-fail-open-checklist.md
  - 04_mcp_02_03_audit-logging-and-errors.md
source:
  - 00_security_02_high-risk-tool-common-policy.md
---

# High-Risk MCP Tool Common Policy

## Purpose / scope

This document defines a common security policy for high-risk MCP tools that perform write operations, execute commands, or modify external resources. The policy governs the following tool categories:

- **File-write** (`file-write-mcp`): Create, write, edit, move, copy, delete files/directories
- **File-delete** (`file-delete-mcp`): Delete files and directories
- **Shell** (`shell-mcp`): Execute shell commands
- **Git** (`git-mcp`): Git operations (checkout, commit, push, pull, branch)
- **GitHub** (`github-mcp`): GitHub API operations (repos, issues, PRs, files)
- **CI/CD** (`cicd-mcp`): CI/CD pipeline operations
- **DB maintenance** (`db-mcp`): Database maintenance operations

The **mdq** server is included as the reference implementation of traversal prevention patterns, which this policy generalizes to all filesystem-touching high-risk tools.

## Purpose of layered protection

Agent-side approval confirms user intent and presents the expected operation and its risk; it does not by itself guarantee technical safety. Each high-risk MCP server MUST enforce its own technical constraints independently of whether an Agent-side approval step exists or was satisfied. Approval and server-side enforcement are separate concerns that MUST NOT be treated as substitutes for one another.

## Layered protection model

| Layer | Responsibility | Not responsible for |
|---|---|---|
| **Agent approval** | Confirm user intent; present the expected operation and risk before dispatch | Enforcing path/repo/branch/ref safety — it MUST NOT be treated as a bypass for server-side validation |
| **Common per-server guard** | Path/repo authorization, canonical path resolution, read-only enforcement, basic operation classification | Command- or operation-specific preconditions |
| **Command-specific guard** | Worktree-state validation, branch/remote/ref policy, dangerous-option rejection, operation-specific preconditions | General authorization (owned by the common guard) |
| **Postcondition verification** | Confirming the resulting state matches intent; detecting unresolved conflicts; preventing partial results from being reported as success | Preventing the operation from starting (that is the guard layers' job) |
| **Audit** | Recording repository/resource identity, operation type, before/after state, approval correlation, and result — without secrets or full sensitive output | Blocking or allowing the operation |

**Current coverage is uneven across tools.** Every high-risk server implements the common-guard layer (allowlist + read-only/write gating). Command-specific guards, postcondition verification, and rich audit correlation are implemented for some tool categories (e.g., mdq path/symlink checks) but are an open gap for others — see each tool's own document for its current layer coverage, and do not assume a layer is implemented here merely because this policy defines it as a concept.

## Allowed paths/repos

All high-risk tools that access filesystem or remote resources use a fail-closed allowlist model:

| Allowlist Type | Configuration Key | Applicable Tools | Behavior on Empty |
|---|---|---|---|
| Filesystem directories | `allowed_dirs` | file-read, file-write, file-delete, mdq, shell (cwd) | Fail-closed: no access if empty |
| Repository paths | `allowed_repo_paths` | git-mcp | Fail-closed: no repo access if empty |
| GitHub repositories | `allowed_repos` | github-mcp | Fail-closed: no repo access if empty |

**Common shape**: All allowlists are lists of absolute paths or repository identifiers. An empty list means "deny all" (fail-closed). Paths must be absolute and are normalized via `Path.resolve()` before comparison.

*Source: `04_mcp_05_01_access-control-and-allowlists.md`*

## Command allowlists

Tools that execute commands (shell, git, github CLI) enforce command allowlists:

- **Shell MCP**: `command_allowlist` in `config/shell_mcp_server.toml` — only listed command prefixes allowed (e.g., `ls`, `cat`, `grep`, `git log`, `git status`)
- **Git MCP**: no subcommand allowlist exists. The tool surface is a fixed, named dispatch table (`git_status`, `git_checkout`, `git_pull`, `git_push`, etc.) rather than a free-form command string, but individual tool arguments (`branch`, `remote`) are not validated against a safe-value allowlist — see `04_mcp_04_05_git.md` Command-specific guard status for the current gap. Approval is an Agent-side (client) concern, not something the Git MCP server itself checks (see Layered protection model below).
- **GitHub MCP**: Uses GitHub API directly; no shell command execution

*Source: `04_mcp_05_01_access-control-and-allowlists.md` Command Allowlist*

## Argument validation

All tool arguments are validated before execution via `agent/tool_arg_validator.py::validate_tool_arguments()`:

- **Schema validation**: Arguments validated against tool's input schema (JSON Schema)
- **Type coercion**: Primitive types coerced; complex types rejected if malformed
- **Constraint checking**: Numeric bounds, string length, enum values enforced
- **Path validation**: File paths checked against `allowed_dirs`/`allowed_repo_paths` after `Path.resolve()`

*Source: `05_agent_06_01_tool-execution-and-approval-execution.md`*

## Path-traversal prevention

**All filesystem-touching tools resolve paths via `Path.resolve()` before comparison against the allowlist root.**

This normalizes:
- Relative paths (`.`, `..`, `../etc/passwd`)
- Symlinks (resolved to target)
- Redundant separators (`//`, `./`)

The resolved absolute path is then checked against the allowlist using prefix matching. If the resolved path is not under any allowlisted root, access is denied.

This generalizes the path-traversal prevention language currently found only in `04_mcp_04_04_mdq.md` / `04_mcp_05_05_mdq-enforcement-and-lockdown.md` to all filesystem-touching high-risk tools (file-write, file-delete, shell, git).

*Source: `04_mcp_04_04_mdq.md`, `04_mcp_05_05_mdq-enforcement-and-lockdown.md`; implemented in `scripts/mcp_servers/file/write_service.py`, `delete_service.py`, `common.py`, `read_security.py`*

## Symlink-traversal prevention

**`Path.resolve()` follows and normalizes symlinks before the allowlist check.**

This prevents symlink-based traversal attacks where a symlink inside an allowed directory points outside the allowlist. The resolution happens before the allowlist comparison, so the target of the symlink must also be within the allowlist.

This generalizes the symlink-traversal prevention language from the mdq docs to all filesystem-touching high-risk tools.

## Approval requirements mapped explicitly to risk tiers

The following table reproduces the authoritative approval-to-risk-tier mapping from `04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` Risk Tier Classification:

| Risk Tier | Description | Approval Required | Example Tools |
|---|---|---|---|
| `READ_ONLY` | Read-only operations; no side effects | None (auto-approved) | `read_text_file`, `list_directory`, `github_list_issues` |
| `WRITE_SAFE` | Write operations with limited blast radius | User approval (configurable) | `write_file`, `create_directory`, `github_create_issue` |
| `WRITE_DANGEROUS` | Destructive or high-impact writes | User approval (mandatory) | `delete_file`, `delete_directory`, `shell_run`, `github_push_files`, `github_merge_pull_request` |
| `ADMIN` | Administrative/privileged operations | Admin approval + audit | `delete_repo`, `cicd_deploy`, `db_maintenance` |

**Cross-linked with approval-execution flow**: `05_agent_06_01_tool-execution-and-approval-execution.md` and `05_agent_06_02_tool-execution-and-approval-approval.md` define how approval is requested, granted, and audited.

*Source: `04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` Risk Tier Classification*

## Audit fields

All high-risk tool executions emit audit log entries with the following fields:

| Field | Description |
|---|---|
| `event` | Event type (e.g., `tool_exec`) |
| `task_id` | Agent task ID |
| `tool` | Tool name (e.g., `write_file`) |
| `mcp_request_id` | MCP request ID (if applicable) |
| `is_error` | Boolean |
| `error_type` | Error category (`transport`, `tool`, `validation`, etc.) |
| `ts` | Timestamp (ISO 8601) |
| `session_id` | Agent session ID |
| `tool_args` | Redacted tool arguments (per redaction rules) |

*Source: `04_mcp_02_03_audit-logging-and-errors.md`*

## Production restrictions

The following restrictions apply in production (`security_profile=production`):

| Restriction | Enforcement |
|---|---|
| Tool safety tiers unknown keys | Fatal error (fail-closed) |
| `approval_github_allowed_repos` empty | Deny all GitHub write operations |
| `tool_safety_tiers` missing keys | Fatal error |
| `security_lockdown_enabled` | Enforces stricter defaults |
| `allow_public_bind` | Must be `false` or require token |
| Bearer token | Required for public bind |

*Source: `04_mcp_06_16_pre-production-fail-open-checklist.md`*

## Failure behavior

**Fail-closed by default** — all high-risk operations default to denial unless explicitly allowed by configuration and approval.

This is cross-linked with `00_security_01_architecture-and-trust-boundaries.md` Fail-open-vs-fail-closed behavior table.

The fail-closed posture applies to:
- Allowlist checks (empty = deny)
- Unknown tool safety tiers (fatal in production)
- Unknown command prefixes (denied)
- Path resolution outside allowlist (denied)
- Missing approval for `WRITE_DANGEROUS`/`ADMIN` tools (denied)

## Tool-specific exceptions

**Exceptions live in each tool's own documentation, not in this common policy body.**

This policy defines the common baseline. Tool-specific deviations are documented in each tool's own documentation with clear references back to this policy. Examples:

- **GitHub MCP**: `protected_branches` and `path_denylist` are fail-open by design (documented in `04_mcp_05_01_access-control-and-allowlists.md`); `protected_branches` itself only exists for GitHub MCP, not Git MCP.
- **Git MCP**: has no protected-branch policy and no technical Force Push block — the `branch`/`remote` arguments to `git_checkout`/`git_pull`/`git_push` are passed through without command-specific validation, which is an open gap, not a deviation covered by an additional restriction (documented in `04_mcp_04_05_git.md` Command-specific guard status; tracked as a Known Issue).
- **Shell MCP**: `approval_shell_safe_prefixes` allows auto-approval for safe prefixes (documented in `04_mcp_04_02_file-write-file-delete-shell.md`)

Tool-specific docs must include a "See also: `00_security_02_high-risk-tool-common-policy.md`" reference.

## Related Documents

- `00_security_01_architecture-and-trust-boundaries.md`
- `00_governance_01_documentation-governance.md`
- `00_governance_02_canonical-source-rule.md`
- `04_mcp_05_01_access-control-and-allowlists.md`
- `04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`
- `05_agent_06_01_tool-execution-and-approval-execution.md`
- `04_mcp_04_02_file-write-file-delete-shell.md`
- `04_mcp_04_04_mdq.md`
- `04_mcp_05_05_mdq-enforcement-and-lockdown.md`
- `05_agent_06_01_tool-execution-and-approval-execution.md`
- `05_agent_06_02_tool-execution-and-approval-approval.md`
- `04_mcp_06_16_pre-production-fail-open-checklist.md`
- `04_mcp_02_03_audit-logging-and-errors.md`