---
title: "MCP Inconsistencies and Known Issues"
area: mcp
tags:
  - mcp
  - inconsistencies
  - known-issues
  - bugs
related:
  - 04_mcp_00_document-guide.md
---

## Migration Notes

- Migration Date: 2026-07-23
- Source Format: Existing bullet format (Type, Impact scope, Statement A/B, Current safe interpretation, Recommended action, Notes for AI reference)
- Destination Format: Common template (17 fields)
- Note: Existing entry contents are preserved. Missing fields are filled with 'unconfirmed'.

# MCP Inconsistencies and Known Issues

This file catalogs bugs, unimplemented features, contradictions between specifications, and undefined behaviors discovered in the MCP layer during the documentation restructuring process.

---

### MCP-001: `include_disabled` filter and `disabled_code` structured code have no reachable caller

- **ID**: MCP-001
- **Title**: `include_disabled` filter and `disabled_code` structured code exist as dead parameters with no reachable caller
- **Status**: resolved
- **Severity**: Medium
- **Area**: MCP
- **Type**: implementation-bug
- **Source**: `scripts/mcp_servers/server.py::build_tools_response()`; all `list_tools()` handlers in `scripts/mcp_servers/*/`
- **Owner**: Unassigned
- **First Found**: Unconfirmed
- **Target**: `/v1/tools` endpoint
- **Related**: `docs/04_mcp_03_06_tool-runtime-availability-metadata.md`
- **Summary**: `build_tools_response()` already accepts `include_disabled`/`disabled_code` parameters, but no `list_tools()` handler declares a query parameter or passes either argument, so `/v1/tools` always returns every tool unconditionally.
- **Current Description**: `/v1/tools` currently accepts no query parameters and always returns all tools unconditionally, despite the helper function it calls already being able to filter.
- **Observed Implementation**: `include_disabled: bool = False` and `disabled_code: str | None = None` are real parameters on `build_tools_response()`, but every call site omits them, and no `list_tools()` route declares a matching FastAPI query parameter.
- **Impact**: Cannot filter out disabled tools or dispatch on a machine-readable disabled category via the API today.
- **Recommended Action**: Wire a query parameter through each server's `list_tools()` handler to the existing `build_tools_response()` parameters; no new filtering logic is required, only call-site wiring.
- **Resolution Notes**: All 10 MCP servers' `list_tools()` handlers now accept `include_disabled`/`disabled_code` and pass them through to `build_tools_response()` — `git`, `github`, `web_search`, `file_read`, `file_write`, `file_delete` were wired directly (or switched from a hand-built response dict to `build_tools_response()`); `rag_pipeline`, `cicd`, `mdq`, `shell` picked it up as part of their MCP-002 fix (Verified by test, `tests/mcp_servers/git/test_tools_endpoint.py`).

---

### MCP-002: `rag_pipeline`, `cicd`, `mdq`, and `shell` do not implement `enabled`/`disabled_reason`

- **ID**: MCP-002
- **Title**: Tool runtime availability metadata (`config_dependent`/`enabled`/`disabled_reason`) is implemented for most servers; `web_search` is now included, correcting a stale prior version of this issue
- **Status**: resolved
- **Severity**: Low
- **Area**: MCP
- **Type**: implementation-bug
- **Source**: `scripts/mcp_servers/{rag_pipeline,cicd,mdq,shell}/server.py`
- **Owner**: Unassigned
- **First Found**: Unconfirmed
- **Target**: `scripts/mcp_servers/{rag_pipeline,cicd,mdq,shell}/server.py`
- **Related**: `docs/04_mcp_03_06_tool-runtime-availability-metadata.md`
- **Summary**: `git`, `file_read`, `file_write`, `file_delete`, `github`, and `web_search` all compute `enabled`/`disabled_reason` per tool. `rag_pipeline`, `cicd`, `mdq`, and `shell` route `TOOL_LIST` straight to `build_tools_response()` with no per-tool availability computation.
- **Current Description**: A prior version of this entry stated `web_search` lacked `enabled`/`disabled_reason`; that was stale — `web_search_server.py::_web_search_tool_availability` implements it. The actual remaining gap is the servers listed above (Source field).
- **Observed Implementation**: `RuntimeToolRegistry` is live-detected by `McpToolDiscoveryService` and connected via `ToolExecutor.set_runtime_registry()`; the 4 gap servers' tools default to `enabled_for_llm=True` (no `enabled` key in their `/v1/tools` entries).
- **Impact**: `rag_pipeline`/`cicd`/`mdq`/`shell` tools cannot be statically disabled or surfaced as disabled via this mechanism, even where a config-derived reason (e.g., empty `workflow_allowlist`/`command_allowlist`) would apply.
- **Recommended Action**: Implement per-tool `enabled`/`disabled_reason` computation for the 4 remaining servers, following the pattern already used by `git`/`file_*`/`github`/`web_search`.
- **Resolution Notes**: All 4 servers now compute `enabled`/`disabled_reason`: `_rag_pipeline_tool_availability()` (gated on `embed_url`, per-tool), `_cicd_tool_availability()` (gated on `repo_allowlist`/`workflow_allowlist`, per-tool), `_mdq_tool_availability()` (gated on `allowed_dirs`, whole-service), `_shell_tool_availability()` (gated on `command_allowlist`, whole-service) — each follows the `git`/`file_*`/`github`/`web_search` pattern (Verified by test).

---

### MCP-003: Git MCP lacks Dirty-Worktree/Detached-HEAD guards; postcondition verification absent

- **ID**: MCP-003
- **Title**: `git_checkout`/`git_pull`/`git_push` lack Dirty-Worktree/Detached-HEAD guards; no postcondition verification after operations
- **Status**: open
- **Severity**: High
- **Area**: MCP
- **Type**: design-gap
- **Source**: `scripts/mcp_servers/git/git_service.py`, `format_output.py`, `tool_validators.py`
- **Owner**: Unassigned
- **First Found**: Unconfirmed
- **Target**: `04_mcp_04_05_git.md`, `00_security_02_high-risk-tool-common-policy.md`
- **Related**: SHARED-style gap in Git MCP write path; see `04_mcp_04_05_git.md` Write protection policy
- **Summary**: Git MCP enforces repository-path allowlisting, `read_only`, and protected-branch guards (via `GitConfig.protected_branches`). No guard checks Dirty Worktree or Detached HEAD. `branch`/`remote` option-injection is rejected by `_is_safe_ref()`/`_validate_ref()`. Force-Push has no guard because `git_push`'s schema exposes no `force` field. Postcondition verification (re-checking resulting branch/HEAD, detecting merge conflicts, re-fetching remote state) is absent.
- **Current Description**: `git_checkout`/`git_pull`/`git_push` all pass through the same common guard as `git_add`/`git_commit`, with no additional command-specific validation for Dirty-Worktree or Detached-HEAD. Protected-branch enforcement is implemented via `GitSecurityGuards._check_protected_branch()` / `GitService._validate_protected()`. `branch`/`remote` option-injection is rejected by `_is_safe_ref()`/`_validate_ref()` (tested by `test_is_safe_ref` and assertions in `tests/mcp_servers/git/test_git_security_compliance.py`). One gap remains: an empty `branch` argument skips the protected-branch check entirely (`_validate_protected()` short-circuits on falsy input). Force-Push has no guard because `git_push`'s schema exposes no `force` field.
- **Observed Implementation**: None of `format_checkout()`/`format_pull()`/`format_push()` re-check the resulting branch/HEAD, detect unresolved merge conflicts, or re-fetch remote state after a push. Success is inferred solely from the absence of a `GitCommandError`.
- **Impact**: A caller that can invoke `git_checkout`/`git_push` can silently discard local changes if Dirty-Worktree is not checked, or receive stale success reports if postcondition verification is missing.
- **Recommended Action**: Add explicit Dirty-Worktree/Detached-HEAD checks per `04_mcp_04_05_git.md` git_checkout/git_pull/git_push policy target design; add postcondition verification after operations. Cross-reference `GIT-001` for Dirty-Worktree/Detached-HEAD and `GIT-002` for postcondition verification. Note: protected-branch enforcement and `branch`/`remote` option-injection rejection are already implemented (see REQ-006).
- **Resolution Notes**: Narrowed from original scope: protected-branch enforcement and `branch`/`remote` option-injection rejection are implemented (see REQ-006). The remaining Dirty-Worktree/Detached-HEAD gap is tracked as `GIT-001` and the postcondition-verification gap as `GIT-002`.

---

### MCP-004: `git_checkout`/`git_pull`/`git_push` are approved at `MEDIUM` risk despite being documented as `WRITE_DANGEROUS`

- **ID**: MCP-004
- **Title**: Git write tools fall back to `y/N` approval instead of the full-word `yes` prompt their risk tier implies
- **Status**: resolved
- **Severity**: Medium
- **Area**: MCP
- **Type**: document-code-mismatch
- **Source**: `scripts/agent/tool_policy.py::_TIER_TO_RISK`, `config/agent.toml::approval_risk_rules`
- **Owner**: Unassigned
- **First Found**: Unconfirmed
- **Target**: `04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`, `04_mcp_04_05_git.md`
- **Related**: MCP-003
- **Summary**: `04_mcp_05_03`'s risk-tier table lists `git_checkout`/`git_pull`/`git_push` under `WRITE_DANGEROUS` → "Requires `yes` (full word) input," but they have no `"high"` override in `approval_risk_rules`, so they fall back to `RiskLevel.MEDIUM` and get the `y/N` prompt.
- **Current Description**: Other `WRITE_DANGEROUS` examples in the same table (`delete_file`, `shell_run`, `github_push_files`) do have explicit `"high"` overrides and behave as documented; the three git tools do not.
- **Observed Implementation**: `_TIER_TO_RISK["WRITE_DANGEROUS"] = RiskLevel.MEDIUM`; no `approval_risk_rules` entry for `git_checkout`/`git_pull`/`git_push` raises this to `HIGH`.
- **Impact**: Operators relying on the documented table to judge how much friction a Force-Push-capable operation requires will overestimate the approval friction actually presented.
- **Recommended Action**: Either add `"high"` overrides for these three tools in `approval_risk_rules`, or correct the table to reflect the current `MEDIUM` behavior — a decision from the policy owner is needed on which is the intended target.
- **Resolution Notes**: Policy owner decided to raise these three tools to the full-word-`yes` tier. `config/agent.toml::approval_risk_rules` now sets `git_checkout`/`git_pull`/`git_push = "high"`, matching the `04_mcp_05_03` table's documented intent (Verified by test, `tests/agent/test_tool_policy_comprehensive.py`). `04_mcp_05_03`'s "currently includes git_checkout, git_pull, and git_push" caveat is now stale and should be removed the next time that document is touched. Core mismatch is resolved. Remaining open items (narrower scope): (1) config floor check preventing effective risk below HIGH for git tools via ProductionConfigValidator, (2) end-to-end test exercising the shipped config/agent.toml through the actual approval-risk pipeline, (3) git-specific approval-screen preview in build_preview() instead of generic JSON-dump fallback.

---

### MCP-005: Git MCP audit log `target` field likely always empty

- **ID**: MCP-005
- **Title**: Git MCP audit call reads a nonexistent `"repo"` argument key instead of `"repo_path"`
- **Status**: open
- **Severity**: Low
- **Area**: MCP
- **Type**: ambiguous-behavior
- **Source**: `scripts/mcp_servers/git/git_server.py::call_tool`
- **Owner**: Unassigned
- **First Found**: Unconfirmed
- **Target**: `04_mcp_04_05_git.md` Audit
- **Related**: MCP-003
- **Summary**: The audit call site passes `req.args.get("repo", "")` as the audit `target`, but Git MCP's input schema uses the key `repo_path`, not `repo`.
- **Current Description**: Read from code, this means the audit `target` field for every git-mcp call is likely always the empty-string default.
- **Observed Implementation**: Not yet confirmed by capturing a live audit log line — tracked as NC-020 in `00_governance_03_issue-and-uncertainty-management.md` rather than a fully verified bug.
- **Impact**: If confirmed, Git MCP audit entries carry no repository identity, weakening the audit trail for a High-Severity write surface (see MCP-003).
- **Recommended Action**: Confirm by inspecting an actual audit log line for a git-mcp call; if `target` is empty, fix the key to `repo_path`.
- **Resolution Notes**: Open, pending confirmation.

---

### GIT-001: git_checkout/git_pull do not reject dirty worktree or detached HEAD before write operations

- **ID**: GIT-001
- **Title**: `git_checkout`/`git_pull` lack Dirty Worktree / Detached HEAD checks before write operations
- **Status**: open
- **Severity**: High
- **Area**: MCP
- **Type**: design-gap
- **Source**: `scripts/mcp_servers/git/git_service.py`
- **Owner**: Unassigned
- **First Found**: 2026-08-22
- **Target**: `docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md`
- **Related**: ADR-012
- **Summary**: ADR-012 requires that Git MCP tools check for Dirty Worktree and Detached HEAD states before performing write operations. Neither `git_checkout` nor `git_pull` implements these checks.
- **Current Description**: Both `git_checkout` and `git_pull` proceed with checkout/pull operations regardless of whether the working tree is dirty or the HEAD is detached.
- **Observed Implementation**: `git_checkout` calls `git reset --hard` unconditionally; `git_pull` calls `git pull` without checking for uncommitted changes first.
- **Impact**: A caller can silently discard uncommitted changes or create a detached HEAD state during a write operation, violating the safety guarantees ADR-012 specifies.
- **Recommended Action**: Add Dirty Worktree and Detached HEAD checks to both `git_checkout` and `git_pull`, rejecting the operation if either condition is true unless explicitly overridden.
- **Resolution Notes**: Open — design gap confirmed.

---

### GIT-002: Postcondition verification missing after write operations

- **ID**: GIT-002
- **Title**: Git MCP write operations lack postcondition verification
- **Status**: open
- **Severity**: High
- **Area**: MCP
- **Type**: design-gap
- **Source**: `scripts/mcp_servers/git/git_service.py`
- **Owner**: Unassigned
- **First Found**: 2026-08-22
- **Target**: `docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md`
- **Related**: ADR-012
- **Summary**: ADR-012 requires that Git MCP tools verify postconditions after write operations complete. Neither `git_checkout` nor `git_pull` verifies that the expected state was achieved.
- **Current Description**: After executing a write operation, neither tool verifies that the working tree, branch, or remote state matches the expected outcome.
- **Observed Implementation**: `git_checkout` returns success after calling `git checkout` without verifying the branch actually changed; `git_pull` returns success after `git pull` without verifying the remote refs updated.
- **Impact**: Silent failures where the operation appears successful but did not achieve the expected state — operators would not know the operation failed.
- **Recommended Action**: Add postcondition checks after each write operation (e.g., verify current branch after checkout, verify remote ref update after pull) and fail the operation if the expected state is not reached.
- **Resolution Notes**: Open — design gap confirmed.

---

## Related Documents

- `04_mcp_00_document-guide.md`
