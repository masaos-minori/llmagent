---
title: "MCP Inconsistencies and Known Issues"
category: mcp
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
- **Status**: open
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
- **Resolution Notes**: Open — not deferred by design; the gap is wiring, not missing capability.

---

### MCP-002: `rag_pipeline`, `cicd`, `mdq`, and `shell` do not implement `enabled`/`disabled_reason`

- **ID**: MCP-002
- **Title**: Tool runtime availability metadata (`config_dependent`/`enabled`/`disabled_reason`) is implemented for most servers; `web_search` is now included, correcting a stale prior version of this issue
- **Status**: open
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
- **Resolution Notes**: Corrected scope; not yet resolved.

---

### MCP-003: Git MCP has no protected-branch or Force Push guard, and `branch`/`remote` accept option-injection values

- **ID**: MCP-003
- **Title**: `git_checkout`/`git_pull`/`git_push` lack command-specific guards; unvalidated `branch`/`remote` values allow forced checkout/push
- **Status**: open
- **Severity**: High
- **Area**: MCP
- **Type**: design-gap
- **Source**: `scripts/mcp_servers/git/git_service.py`, `format_output.py`, `tool_validators.py`
- **Owner**: Unassigned
- **First Found**: Unconfirmed
- **Target**: `04_mcp_04_05_git.md`, `00_security_02_high-risk-tool-common-policy.md`
- **Related**: SHARED-style gap in Git MCP write path; see `04_mcp_04_05_git.md` §Write protection policy
- **Summary**: Git MCP enforces only repository-path allowlisting and `read_only`; no guard checks Dirty Worktree, Detached HEAD, protected branches, or Force Push. `branch`/`remote` are forwarded to GitPython unvalidated.
- **Current Description**: `git_checkout`/`git_pull`/`git_push` all pass through the same common guard as `git_add`/`git_commit`, with no additional command-specific validation.
- **Observed Implementation**: Reproduced in a sandboxed test environment — passing `branch="--force"` to `git_checkout` discards uncommitted worktree changes without warning, and to `git_push` performs a forced update overwriting a diverged remote branch, because the value is interpreted as a `git` CLI option rather than a ref name.
- **Impact**: A caller (or a compromised/careless LLM turn) that can invoke `git_checkout`/`git_push` can silently discard local changes or force-overwrite a remote branch, bypassing the protection the tool's schema appears to provide by omitting a `force` field.
- **Recommended Action**: Validate `branch`/`remote` against a safe-ref pattern (reject values starting with `-`), add explicit Dirty-Worktree/Detached-HEAD/protected-branch/Force-Push checks per `04_mcp_04_05_git.md` §git_checkout/git_pull/git_push policy target design.
- **Resolution Notes**: Open; confirmed exploitable, not merely a documentation gap.

---

### MCP-004: `git_checkout`/`git_pull`/`git_push` are approved at `MEDIUM` risk despite being documented as `WRITE_DANGEROUS`

- **ID**: MCP-004
- **Title**: Git write tools fall back to `y/N` approval instead of the full-word `yes` prompt their risk tier implies
- **Status**: open
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
- **Resolution Notes**: Documentation corrected to describe current behavior; underlying policy decision still open.

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
- **Target**: `04_mcp_04_05_git.md` §Audit
- **Related**: MCP-003
- **Summary**: The audit call site passes `req.args.get("repo", "")` as the audit `target`, but Git MCP's input schema uses the key `repo_path`, not `repo`.
- **Current Description**: Read from code, this means the audit `target` field for every git-mcp call is likely always the empty-string default.
- **Observed Implementation**: Not yet confirmed by capturing a live audit log line — flagged as **Needs confirmation** rather than a fully verified bug.
- **Impact**: If confirmed, Git MCP audit entries carry no repository identity, weakening the audit trail for a High-Severity write surface (see MCP-003).
- **Recommended Action**: Confirm by inspecting an actual audit log line for a git-mcp call; if `target` is empty, fix the key to `repo_path`.
- **Resolution Notes**: Open, pending confirmation.

---

## Related Documents

- `04_mcp_00_document-guide.md`
