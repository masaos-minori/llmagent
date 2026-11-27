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
| `allowed_repos` (github-mcp) | Fail-closed | All repository access denied, reads and writes included (`_get_repo` and `_assert_allowed_repo` in `github_service_security.py`; no mode switch exists) |
| `allowed_repo_paths` (git-mcp) | Fail-closed | All access denied |
| `repo_allowlist` (cicd-mcp) | Fail-closed | All repositories denied |
| `workflow_allowlist` (cicd-mcp) | **Fail-closed** | All workflows denied |
| `command_allowlist` (shell-mcp) | Fail-closed | All commands denied |
| `path_denylist` (github-mcp) | Fail-open (registered ADR-004 exception; rationale pending — open item NC-001 in `docs/00_governance/governance_03_issue-and-uncertainty-management.md`) | All paths allowed |
| `protected_branches` (github-mcp, git-mcp) | Fail-closed at load (empty is a config load error; the server does not start) | Branch protection always configured |

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
| `protected_branches` | github-mcp | `server.protected_branches` | `failed` with `REASON_CONFIG_INVALID` when empty (Explicit in code — scripts/mcp_servers/github/github_service_security.py); in practice an empty value is rejected earlier at config load and the server does not start (`github_models_config.py`) |
| `allowed_repos` | github-mcp | `server.repo_allowlist` | `failed` when empty (Explicit in code — `_get_repo` and `_assert_allowed_repo` in scripts/mcp_servers/github/github_service_security.py) |
| `allow_force_push` | github-mcp | `server.force_push_policy` | `warning` when `true` (Explicit in code — `merge_pull_request` in scripts/mcp_servers/github/github_service_pull_requests.py) |
| `require_pr_review` | github-mcp | `server.pr_review_required` | `warning` when `false` (Explicit in code — `merge_pull_request` in scripts/mcp_servers/github/github_service_pull_requests.py) |
| `max_file_size_kb` | github-mcp | `server.max_file_size` | `not_applicable` at `0` (Explicit in code — `_assert_max_file_size` in scripts/mcp_servers/github/github_service_security.py) |
| `audit_log_path` | github-mcp | `server.audit_log_writable` | `failed` when the configured path has no writable parent directory; `not_applicable` when empty (Explicit in code — `_write_github_audit_log` in scripts/mcp_servers/github/github_service_security.py) |
| `max_per_page` | github-mcp | `server.per_page_bounds` | `failed` when `max_per_page` is not positive or `default_per_page` exceeds it (Explicit in code — `_clamp_per_page` in scripts/mcp_servers/github/github_service_security.py) |
| `allow_global_search` | github-mcp | `server.global_search` | `warning` when `true`, because search queries then reach outside `allowed_repos` (Explicit in code — `_resolve_search_query` in scripts/mcp_servers/github/github_service_security.py) |
| `max_file_read_size_kb` | github-mcp | `server.max_file_read_size` | `not_applicable` at `0`, which means unlimited (Explicit in code — `_assert_max_read_file_size` in scripts/mcp_servers/github/github_service_security.py) |

An empty capability-gating allowlist is a posture failure, not a warning: the server refuses to bind its HTTP port and the Agent refuses to start. `path_denylist` is the only fail-open setting; it is reported as `not_applicable` instead of being omitted, so a missing restriction is visible in the posture rather than silently absent.

Runtime denial is enforced independently by each server, so a running server keeps its fail-closed behavior for whatever its allowlists permit. An empty fail-closed setting is an intended safe default (access is denied); an empty `path_denylist` allows unrestricted path access and is surfaced as `not_applicable` in the posture. On the Agent side both fail closed: an empty `allowed_tools` denies every tool (also after `/reload`) and an empty `allowed_root` is a config load error (Explicit in code — scripts/agent/config_section_builders.py).

Retry classification follows the same fail-closed rule. Every GitHub write declares `retry_policy = never`, so a dedup-store failure refuses the call instead of dispatching it, and a write is never retried. A timeout or an ambiguous transport failure on a write never implies that the write did not apply, so the `outcome_unknown` result is not retried either.

The retryable side is the registered exception: a store acquisition failure for a retryable tool does not fail closed — the call proceeds overlay-only with the audited `dedup_state="store_error"` marker, while the non-retryable counterpart fails closed with `error_type="dedup_store_error"` (`tests/mcp_servers/test_mcp_dispatch.py::test_store_error_retryable_proceeds_non_retryable_fails_closed`). The overlay path itself is described in [mcp_03_03_transport-and-health.md](mcp_03_03_transport-and-health.md). Both relaxations are ADR-004 exceptions whose maintainer approval is still open (MCP-001 for the overlay-only path, MCP-002 for the post-open warning-only write failure); they are referenced here as open, not resolved.

---

## Dry-Run Support

`dry_run=True` previews a call without side effects. It is supported by the file-write tools, the file-delete tools, `shell_run`, the five git write tools, and cicd-mcp `trigger_workflow`; see each server in the Server Catalog.

**Note on cicd-mcp:** Repository and workflow allowlist checks are executed before the `dry_run` bypass inside `handle_trigger_workflow`. Requests subject to denial are always rejected even with `dry_run=True`.

At the agent level: the approval flow runs the tool with `dry_run=True` before showing a confirmation prompt when the registered tool declares `preview_capability = "dry_run"` (`_declared_dry_run_capable()` in `scripts/agent/tool_approval.py`). The `approval_dry_run_tools` config map no longer exists; it is a removed key rejected as an unknown key at config validation (`scripts/agent/production_config_validator.py`).

---

## Risk Tier Classification

Safety tiers are declared per tool as `agent_safety_tier` by the tool's producer (the tool definitions under `scripts/mcp_servers/`), and the declared tier is the single risk source: `classify_risk()` in `scripts/agent/tool_policy.py` maps it through `_TIER_TO_RISK`, then applies argument-dependent escalation. The removed `config/agent.toml` maps `tool_safety_tiers` and `approval_risk_rules` no longer exist and are rejected as unknown keys at config validation. The approval method follows the effective risk, not the tier name alone:

| Tier | Default risk | Approval Method | Plan-mode blocking | Examples |
|---|---|---|---|---|
| `READ_ONLY` | `none` | Automatic approval | Allowed (the only tier plan mode permits) | `read_text_file`, `git_status`, `search_web`, `rag_run_pipeline` |
| `WRITE_SAFE` | `none` | Automatic approval | Blocked | `git_add`, `git_commit`, `index_paths`, `write_file`, `edit_file`, `create_directory`, `github_create_issue` |
| `WRITE_DANGEROUS` | `medium` | `y/N` prompt; escalates to `high` (full `yes`) when a path argument is under `approval_protected_paths`, when `delete_directory` is called with `recursive=true` or a `force`/`overwrite`/`clobber` argument is true, or when a declared branch-kind argument is in `high_risk_branches` | Blocked | `delete_file`, `github_push_files`, `git_checkout`, `git_pull`, `git_push`, `trigger_workflow`, `rag_delete_document` |
| `ADMIN` | `high` | Requires `yes` (full word) input | Blocked | `shell_run` |

Reachability under the shipped declarations (64 declared tiers: 39 `READ_ONLY`, 11 `WRITE_SAFE`, 13 `WRITE_DANGEROUS`, 1 `ADMIN`): a base of `none` returns from `classify_risk()` before special-case and protected-path escalation, so the 50 tier-`none` tools — all 39 `READ_ONLY` tools plus all 11 `WRITE_SAFE` tools — never reach escalation. Only the 13 `WRITE_DANGEROUS` tools and `shell_run` can take a call to the prompt. The evaluation order itself is canonical in [agent_06_02](../23_agent/agent_06_02_tool-execution-and-approval-approval.md). Proven by `tests/agent/test_tool_approval_risk.py` (`test_declared_tier_is_the_only_risk_source`, `test_read_only_tier_tool_returns_none`, `test_write_to_protected_path_escalates_to_high`).

Plan mode blocks a call unless the tool's declared tier is `READ_ONLY`; a tool absent from the registry, and a call without a registry, is blocked (fail closed). `cfg.tool.plan_blocked_tools` is an explicit operational extension that names tools blocked regardless of their tier.

A tool with no declared tier cannot enter the registry: the strict builder rejects an undeclared tier (`scripts/shared/runtime_tool.py`), and a tool absent from the registry is classified `high` at call time (`tests/agent/test_tool_approval_risk.py::test_truly_unknown_tool_returns_high_risk_fail_safe`). `check_tool_safety_tiers()` and `check_unknown_tool_safety_tiers()` in `scripts/shared/tool_routing_validation.py` compare the reference seed registry with the live registry and return drift findings only — no caller may use them to classify a tool (`tests/shared/test_tool_safety_tiers.py`). The removed `tool_safety_tiers` and `approval_risk_rules` keys are rejected as unknown keys with the replacement named by `ProductionConfigValidator.validate()`.

---

## Notes for AI Systems

1. **Do not assume write access or execution rights.** Every capability-gating allowlist is fail-closed when empty: `allowed_repos` (GitHub reads and writes), `command_allowlist` (`shell_run`), `allowed_repo_paths` (all git tools), `repo_allowlist` and `workflow_allowlist` (CI/CD). Verify the relevant allowlist is configured before calling the tool; the checked-in configuration lists values explicitly.

2. **mdq-mcp is production-ready.** FTS5 indexing and searching is implemented. For production RAG workloads, use `rag-pipeline-mcp`. See [mcp_05 MDQ vs RAG Boundary](./mcp_05_04_mdq-rag-boundary.md#mdq-vs-rag-boundary) for guidelines.

3. **Preview with `dry_run=True` before destructive operations.** The agent's approval flow automatically injects `dry_run=True` for a registered tool that declares `preview_capability = "dry_run"` before displaying a user prompt; a tool that declares no dry-run capability is not previewed.

## Keywords

- fail-open
- fail-closed
- dry-run
- risk tiers
- approval
- MCP safety model
