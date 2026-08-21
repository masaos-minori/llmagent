title: "MCP Security and Safety Model: Fail-Open vs Fail-Closed Summary, Dry-Run, Risk Tiers and AI Notes"
category: mcp
tags:
  - mcp
  - security
  - safety-model
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_05_01_access-control-and-allowlists.md
  - 04_mcp_05_02_auth-profiles-and-sandboxing.md
  - 04_mcp_05_04_mdq-rag-boundary.md
  - 04_mcp_05_05_mdq-enforcement-and-lockdown.md
  - 00_security_01_architecture-and-trust-boundaries.md
  - 00_security_02_high-risk-tool-common-policy.md

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

`agent/repl_health.py::audit_security_defaults()` runs at agent startup and logs a summary of the security posture. It reads each server's config file and checks the following:

| Setting | Server Config File | Check Details |
|---|---|---|
| `shell_sandbox_backend` | `shell_mcp_server.toml` | RuntimeError if `"firejail"` + binary missing; WARNING if not `"firejail"` or `"none"`; RuntimeError in production if `"none"` |
| `command_allowlist` | `shell_mcp_server.toml` | DENY-ALL warning if empty (fail-closed) |
| `allowed_repo_paths` | `git_mcp_server.toml` | DENY-ALL warning if empty (fail-closed) |
| `workflow_allowlist` | `cicd_mcp_server.toml` | DENY-ALL warning at both agent and server layers if empty (see [04_mcp_05_01_access-control-and-allowlists.md](./04_mcp_05_01_access-control-and-allowlists.md)) |

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

Tool risk tiers (from `config/agent.toml::tool_safety_tiers`):

| Tier | Example | Approval Method |
|---|---|---|
| `READ_ONLY` | `read_text_file`, `git_status`, `search_web`, `rag_run_pipeline` | Automatic approval |
| `WRITE_SAFE` | `write_file`, `edit_file`, `git_add`, `git_commit` | `y/N` prompt |
| `WRITE_DANGEROUS` | `delete_file`, `shell_run`, `github_push_files`, `git_checkout`, `git_pull`, `git_push`, `trigger_workflow` | Requires `yes` (full word) input **only for tools with an explicit `"high"` override in `approval_risk_rules`** (e.g. `delete_file`, `shell_run`, `github_push_files`). Tools without such an override fall back to the `WRITE_DANGEROUS`→`RiskLevel.MEDIUM` tier mapping and get the `y/N` single-character prompt instead — this currently includes `git_checkout`, `git_pull`, and `git_push` (Explicit in code: `agent/tool_policy.py::_TIER_TO_RISK`, `config/agent.toml::approval_risk_rules`). See `04_mcp_04_05_git.md` Approval level for the Git-specific gap. |
| `ADMIN` | (Custom; unconfigured by default) | Requires `yes` input |

Tools not listed in `tool_safety_tiers` are treated as `WRITE_DANGEROUS` by default (fail-safe).

Entries in `tool_safety_tiers` must match registered tool names exactly (not server keys). Bidirectional validation is performed at startup.

- **Missing Tiers:** If a registered tool is not in `tool_safety_tiers`, it causes an error (fatal `RuntimeError`) in production, and a warning in local/development.
- **Unknown Keys:** If a key in `tool_safety_tiers` does not match a registered tool name, it causes an error (fatal `RuntimeError`) in production, and a warning in local/development.

Both checks are performed via `ProductionConfigValidator.validate()`, which integrates all validations for strict-key, safety-tier, and allowed-tools in a single pass.

---

## Notes for AI Systems

1. **Do not assume write access to GitHub.** `allowed_repos` is empty by default (fail-closed). Verify `allowed_repos` is configured before attempting GitHub writes.

2. **Do not assume shell commands can be executed.** `command_allowlist` is empty by default. Verify the allowlist before calling `shell_run`.

3. **Empty `allowed_repo_paths` = Git access denied.** Configure this before using git-mcp tools.

4. **`workflow_allowlist` is fail-closed** (similar to `repo_allowlist`). An empty list denies all workflow triggers. Explicitly enumerate allowed workflows in `cicd_mcp_server.toml`.

5. **mdq-mcp is production-ready.** FTS5 indexing and searching is implemented. For production RAG workloads, use `rag-pipeline-mcp`. See [04_mcp_05 MDQ vs RAG Boundary](./04_mcp_05_04_mdq-rag-boundary.md#mdq-vs-rag-boundary) for guidelines.

6. **Preview with `dry_run=True` before destructive operations.** The agent's approval flow automatically injects `dry_run=True` for registered tools before displaying a user prompt.

## Related Documents

- `04_mcp_00_document-guide.md`
- `04_mcp_05_01_access-control-and-allowlists.md`
- `04_mcp_05_02_auth-profiles-and-sandboxing.md`
- `04_mcp_05_04_mdq-rag-boundary.md`
- `04_mcp_05_05_mdq-enforcement-and-lockdown.md`
- `00_security_01_architecture-and-trust-boundaries.md` — System architecture / trust boundaries / threat modeling / authentication & authorization / auditing / local vs production / Fail-open/Fail-closed / prompt injection responsibility boundaries
- `00_security_02_high-risk-tool-common-policy.md` — High-risk MCP tool common policy (path/repo allowlists, traversal prevention, approval-risk tier mapping)
