---
title: "MCP Security and Safety Model: Fail-Open vs Fail-Closed Summary, Dry-Run, Risk Tiers and AI Notes"
area: mcp
tags:
  - mcp
  - security
  - safety-model
related:
  - mcp_00_document-guide.md
  - mcp_05_01_access-control-and-allowlists.md
  - mcp_05_02_auth-profiles-and-sandboxing.md
  - mcp_05_04_mdq-rag-boundary.md
  - mcp_05_05_mdq-enforcement-and-lockdown.md
  - security_01_architecture-and-trust-boundaries.md
  - security_02_high-risk-tool-common-policy.md
---

# MCP Security and Safety Model: Fail-Open vs Fail-Closed Summary, Dry-Run, Risk Tiers and AI Notes

## Fail-Open vs Fail-Closed Summary

| Control | Policy | Behavior if Empty/Not Set |
|---|---|---|
| `allowed_dirs` (file-read/write/delete-mcp) | Fail-closed | All access denied |
| `allowed_dirs` (mdq-mcp) | Fail-closed | Denies all tools that accept paths (`MdqAuthorizationError`) |
| `allowed_repos` (github-mcp, fail_closed mode) | Fail-closed | All writes denied |
| `allowed_repos` (github-mcp, fail_open mode) | Fail-open | All repositories allowed |
| `allowed_repo_paths` (git-mcp) | Fail-closed | All access denied |
| `repo_allowlist` (cicd-mcp) | Fail-closed | All repositories denied |
| `workflow_allowlist` (cicd-mcp) | **Fail-closed** | All workflows denied |
| `command_allowlist` (shell-mcp) | Fail-closed | All commands denied |
| `path_denylist` (github-mcp) | Fail-open (no blocking by default) | All paths allowed |
| `protected_branches` (github-mcp) | Fail-open (no blocking by default) | All branches allowed |

### Startup Audit

`agent/services/security_audit.py::audit_security_defaults()` runs at agent startup and logs a summary of the security posture. It reads each server's config file and checks the following:

| Setting | Server Config File | Check Details |
|---|---|---|
| `shell_sandbox_backend` | `shell_mcp_server.toml` | RuntimeError if `"firejail"` + binary missing; WARNING if not `"firejail"` or `"none"`; RuntimeError regardless of environment if `"none"` |
| `command_allowlist` | `shell_mcp_server.toml` | DENY-ALL warning if empty (fail-closed) |
| `allowed_repo_paths` | `git_mcp_server.toml` | DENY-ALL warning if empty (fail-closed) |
| `workflow_allowlist` | `cicd_mcp_server.toml` | DENY-ALL warning at both agent and server layers if empty (see [mcp_05_01_access-control-and-allowlists.md](./mcp_05_01_access-control-and-allowlists.md)) |

Warnings for empty allowlists use the following format: `DENY-ALL detected: {setting} is empty. {server} will reject ALL requests from this category. Verify this is intentional or add allowed values to config.`

At the end of the checks, the following summary line is logged:

``` text
Security posture summary — fail-closed (deny when empty): <list>; fail-open (allow when empty): <list>
```

An empty fail-closed setting is an intended safe default (access is denied). An empty fail-open setting is highlighted as a warning because it allows unrestricted access.

---

## Dry-Run Support

Tools supporting `dry_run=True` (previewing side-effect-free execution):

| Server | Tools Supporting `dry_run` |
|---|---|
| file-write-mcp | `write_file`, `edit_file`, `create_directory`, `move_file` |
| file-delete-mcp | `delete_file`, `delete_directory` |
| shell-mcp | `shell_run` (arg: `dry_run`) |
| git-mcp | `git_add`, `git_commit`, `git_checkout`, `git_pull`, `git_push` |
| cicd-mcp | `trigger_workflow` |

**Note on cicd-mcp:** Repository and workflow allowlist checks are executed before the `dry_run` bypass inside `handle_trigger_workflow`. Requests subject to denial are always rejected even with `dry_run=True`.

At the agent level: `config/agent.toml`'s `approval_dry_run_tools` lists tools where the approval flow automatically executes them with `dry_run=True` before showing a confirmation prompt to the user.

---

## Risk Tier Classification

Safety tiers (from `config/agent.toml::tool_safety_tiers`) supply a default approval risk (`none`/`medium`/`high`); an explicit `config/agent.toml::approval_risk_rules` entry takes precedence (Explicit in code: `agent/tool_policy.py::classify_risk`, `_TIER_TO_RISK`). The approval method follows the effective risk, not the tier name alone:

| Tier | Default risk | Approval Method | Examples |
|---|---|---|---|
| `READ_ONLY` | `none` | Automatic approval | `read_text_file`, `git_status`, `search_web`, `rag_run_pipeline` |
| `WRITE_SAFE` | `none` | Automatic approval unless an `approval_risk_rules` entry sets `medium` (then `y/N`) | No rule (automatic): `git_add`, `git_commit`, `index_paths`. `medium` rule (`y/N`): `write_file`, `edit_file`, `create_directory`, `github_create_issue` |
| `WRITE_DANGEROUS` | `medium` | `y/N` prompt by default; full `yes` when an `approval_risk_rules` entry sets `high` | `medium`: `trigger_workflow`, `rag_delete_document`. `high`: `delete_file`, `github_push_files`, `git_checkout`, `git_pull`, `git_push` |
| `ADMIN` | `high` | Requires `yes` (full word) input | `shell_run` |

A tool missing from `tool_safety_tiers` is not given a default tier: startup validation rejects it (see below), and a tool absent from the registry entirely is classified `high` at call time.

Entries in `tool_safety_tiers` must match registered tool names exactly (not server keys). Bidirectional validation is performed at startup.

- **Missing Tiers:** If a registered tool is not in `tool_safety_tiers`, it causes an error (fatal `RuntimeError`) regardless of environment.
- **Unknown Keys:** If a key in `tool_safety_tiers` does not match a registered tool name, it causes an error (fatal `RuntimeError`) regardless of environment.

Both checks are performed via `ProductionConfigValidator.validate()`, which integrates all validations for strict-key, safety-tier, and allowed-tools in a single pass.

---

## Notes for AI Systems

1. **Do not assume write access to GitHub.** `allowed_repos` is empty by default (fail-closed). Verify `allowed_repos` is configured before attempting GitHub writes.

2. **Do not assume shell commands can be executed.** `command_allowlist` is empty by default. Verify the allowlist before calling `shell_run`.

3. **Empty `allowed_repo_paths` = Git access denied.** Configure this before using git-mcp tools.

4. **`workflow_allowlist` is fail-closed** (similar to `repo_allowlist`). An empty list denies all workflow triggers. Explicitly enumerate allowed workflows in `cicd_mcp_server.toml`.

5. **mdq-mcp is production-ready.** FTS5 indexing and searching is implemented. For production RAG workloads, use `rag-pipeline-mcp`. See [mcp_05 MDQ vs RAG Boundary](./mcp_05_04_mdq-rag-boundary.md#mdq-vs-rag-boundary) for guidelines.

6. **Preview with `dry_run=True` before destructive operations.** The agent's approval flow automatically injects `dry_run=True` for registered tools before displaying a user prompt.

## Keywords

fail-open
fail-closed
dry-run
risk tiers
approval
MCP safety model
