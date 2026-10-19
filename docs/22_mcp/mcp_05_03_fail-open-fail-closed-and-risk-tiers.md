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
| `allowed_repos` (github-mcp) | Fail-closed | All writes denied (no mode switch exists; `_assert_allowed_repo` in `scripts/mcp_servers/github/github_service_security.py`) |
| `allowed_repo_paths` (git-mcp) | Fail-closed | All access denied |
| `repo_allowlist` (cicd-mcp) | Fail-closed | All repositories denied |
| `workflow_allowlist` (cicd-mcp) | **Fail-closed** | All workflows denied |
| `command_allowlist` (shell-mcp) | Fail-closed | All commands denied |
| `path_denylist` (github-mcp) | Fail-open (no blocking by default) | All paths allowed |
| `protected_branches` (github-mcp) | Fail-open (no blocking by default) | All branches allowed |

### Startup Security Validation

Each MCP server validates its own security settings when its process starts and publishes the result as the `security` block of its `/health` response (see [mcp_02_02_startup-modes-and-health.md](./mcp_02_02_startup-modes-and-health.md)). The Agent reads that block during startup readiness and MCP tool discovery; a `failed` check blocks Agent startup whatever the server's `required` classification says (see [ADR-004](../10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md)). There is no Agent-side audit pass over server config files.

| Setting | Server | Check id | Result when the setting is unsafe |
|---|---|---|---|
| `shell_sandbox_backend` | shell-mcp | `server.sandbox_backend` | `failed` when the backend is not `"firejail"` |
| `shell_sandbox_backend` | shell-mcp | `server.sandbox_binary` | `failed` when `"firejail"` is configured but the binary is missing; `not_applicable` when the backend itself was rejected |
| `command_allowlist` | shell-mcp | `server.command_allowlist` | `failed` when empty |
| `allowed_repo_paths` | git-mcp | `server.repo_allowlist` | `failed` when empty |
| `allowed_repo_paths` | git-mcp | `server.repo_allowlist_resolvable` | `failed` when a configured root does not resolve inside the allowlist; `not_applicable` when the allowlist is empty |
| `repo_allowlist` | cicd-mcp | `server.repo_allowlist` | `failed` when empty |
| `workflow_allowlist` | cicd-mcp | `server.workflow_allowlist` | `failed` when empty |
| `workflow_allowlist` | cicd-mcp | `server.workflow_pattern_valid` | `failed` when a configured pattern contains a path separator; `not_applicable` when the allowlist is empty |
| `path_denylist` | github-mcp | `server.path_denylist` | `not_applicable` when empty (fail-open setting; never `failed`) |
| `protected_branches` | github-mcp | `server.protected_branches` | `not_applicable` when empty (fail-open setting; never `failed`) |

An empty capability-gating allowlist is a posture failure, not a warning: the server refuses to bind its HTTP port and the Agent refuses to start. Fail-open settings are reported as `not_applicable` instead of being omitted, so a missing restriction is visible in the posture rather than silently absent.

Runtime denial is enforced independently by each server, so a running server keeps its fail-closed behavior for whatever its allowlists permit. An empty fail-closed setting is an intended safe default (access is denied); an empty fail-open setting allows unrestricted access and is now surfaced as `not_applicable` in the posture.

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

Safety tiers (from `config/agent.toml::tool_safety_tiers`) supply a default approval risk (`none`/`medium`/`high`); an explicit `config/agent.toml::approval_risk_rules` entry takes precedence (Explicit in code — `agent/tool_policy.py::classify_risk`, `_TIER_TO_RISK`). The approval method follows the effective risk, not the tier name alone:

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

1. **Do not assume write access to GitHub.** An empty `allowed_repos` (the code default) denies all writes (fail-closed); the checked-in configuration lists repositories explicitly. Verify `allowed_repos` is configured before attempting GitHub writes.

2. **Do not assume shell commands can be executed.** `command_allowlist` is empty by default. Verify the allowlist before calling `shell_run`.

3. **Empty `allowed_repo_paths` = Git access denied.** Configure this before using git-mcp tools.

4. **`workflow_allowlist` is fail-closed** (similar to `repo_allowlist`). An empty list denies all workflow triggers. Explicitly enumerate allowed workflows in `cicd_mcp_server.toml`.

5. **mdq-mcp is production-ready.** FTS5 indexing and searching is implemented. For production RAG workloads, use `rag-pipeline-mcp`. See [mcp_05 MDQ vs RAG Boundary](./mcp_05_04_mdq-rag-boundary.md#mdq-vs-rag-boundary) for guidelines.

6. **Preview with `dry_run=True` before destructive operations.** The agent's approval flow automatically injects `dry_run=True` for registered tools before displaying a user prompt.

## Keywords

- fail-open
- fail-closed
- dry-run
- risk tiers
- approval
- MCP safety model
