# Implementation Procedure: Fix GitHub write policy enforcement and consolidate GitOps approval behavior

## Goal

Eliminate duplicated GitHub write tool constants, wire up dead GitOps config fields, add audit decisions for GitOps denials, and ensure fail-closed behavior across all GitHub write paths.

## Scope

### Files to modify
- `shared/tool_constants.py` — verify `GITHUB_WRITE_TOOLS` is canonical
- `agent/tool_policy.py` — use shared constant, add force push/protected branch logic
- `agent/tool_approval.py` — use shared constant, wire force push/protected branch, add audit

### Out of scope
- `agent/config_dataclasses.py`
- `agent/config_builders.py`
- `agent/services/config_reload.py`
- `agent/commands/*`
- `agent/memory/*`
- Documentation files
- Test files (except policy/approval tests if required)

## Current State Analysis

Three separate definitions of GitHub write tools exist:

1. `tool_policy.py:_API_WRITE_TOOLS` (9 tools) — includes `github_create_issue`, `github_add_issue_comment`; also includes `github_delete_file`, `github_merge_pull_request`
2. `tool_approval.py:_GITHUB_WRITE_TOOLS` (7 tools) — excludes issue/comment creation, excludes delete/merge PR
3. `tool_constants.py:GITHUB_WRITE_TOOLS` (7 tools) — excludes delete/merge PR, includes issue/comment creation

The canonical constant should be `tool_constants.py:GITHUB_WRITE_TOOLS` since it's in the shared layer. The question is whether `github_delete_file` and `github_merge_pull_request` should be GitHub write tools. Per the existing `GITHUB_DANGEROUS_TOOLS` constant, they're classified as dangerous rather than write tools.

## Design Decisions

### Decision 1: Use shared `GITHUB_WRITE_TOOLS` everywhere
Both `tool_policy.py` and `tool_approval.py` must import `GITHUB_WRITE_TOOLS` from `shared/tool_constants.py` instead of defining their own sets. This eliminates duplication and ensures consistency.

### Decision 2: Issue/comment creation are GitHub write tools
Per `tool_constants.py:GITHUB_WRITE_TOOLS`, `github_create_issue` and `github_add_issue_comment` ARE GitHub write tools. Remove them from `_API_WRITE_TOOLS` in `tool_policy.py`.

### Decision 3: Wire `gitops_force_push_blocked`
When `force=True` is passed to a tool that supports force push (currently `github_push_files`), deny if `gitops_force_push_blocked` is True. Add audit decision `denied_gitops_force_push_blocked`.

### Decision 4: Wire `gitops_protected_branches`
When a tool targets a protected branch, deny if `gitops_protected_branches` contains that branch name. Add audit decision `denied_gitops_protected_branch`. Need to determine which tools support branch targeting.

### Decision 5: `skip_in_workflow_mode` remains as-is
Workflow-level approval intentionally bypasses per-tool approval. This is not a security concern because workflow-level approval is itself a higher-level gate. Keep this behavior but add a debug log entry noting the bypass.

## Implementation Steps

### Step 1: Consolidate GitHub write tool constant

#### In `tool_policy.py`:
1. Import `GITHUB_WRITE_TOOLS` from `shared.tool_constants`
2. Remove `_API_WRITE_TOOLS` definition (lines 23-35)
3. Replace all references to `_API_WRITE_TOOLS` with `GITHUB_WRITE_TOOLS`

#### In `tool_approval.py`:
1. Import `GITHUB_WRITE_TOOLS` from `shared.tool_constants`
2. Remove `_GITHUB_WRITE_TOOLS` definition (lines 38-48)
3. Replace all references to `_GITHUB_WRITE_TOOLS` with `GITHUB_WRITE_TOOLS`

### Step 2: Improve repository allowlist check

#### In `tool_policy.py`:
1. Update `check_allowed_repo()` to normalize `owner` and `repo` (strip whitespace, lowercase)
2. Add explicit validation: reject if `owner` or `repo` is empty after stripping
3. Ensure `allowed` is treated as a set-like container (already done via `in`)
4. Document the normalization behavior in docstring

### Step 3: Wire `gitops_force_push_blocked`

#### In `tool_approval.py`:
1. After `gitops_push_blocked` check (around line 123), add force push check:
   - If `ctx.cfg.approval.gitops_force_push_blocked` is True AND `args.get("force")` is True AND `tool_name` is a tool that supports force push
2. Determine which tools support force push — likely just `github_push_files` based on the tool signature
3. Emit denial message: `"[DENIED] {tool_name}: gitops_force_push_blocked is set; force push operations are disabled"`
4. Audit decision: `denied_gitops_force_push_blocked`

### Step 4: Wire `gitops_protected_branches`

#### In `tool_approval.py`:
1. After `gitops_push_blocked` check, add protected branch check:
   - If `ctx.cfg.approval.gitops_protected_branches` is non-empty AND the tool targets a branch AND that branch is in the protected list
2. Determine which tools support branch targeting — need to check tool signatures for `branch` parameter
3. Emit denial message: `"[DENIED] {tool_name}: gitops_protected_branches blocks writes to '{branch}'"`
4. Audit decision: `denied_gitops_protected_branch`

### Step 5: Add audit decisions for GitOps denials

#### In `tool_approval.py`:
1. Verify `audit_approval()` is called with proper RiskLevel for each GitOps denial path
2. For `gitops_push_blocked`: already uses `RiskLevel.HIGH` ✓
3. For `gitops_force_push_blocked`: use `RiskLevel.HIGH`
4. For `gitops_protected_branch`: use `RiskLevel.HIGH`
5. Ensure `emit_denied()` is called for all GitOps denial paths

### Step 6: Add workflow-mode bypass logging

#### In `tool_approval.py`:
1. Add a debug log entry when `skip_in_workflow_mode` is True:
   ```python
   logger.debug("run_approval_checks: skipping per-tool approval — workflow-level approval is active")
   ```
2. This makes the bypass visible in logs for auditing purposes

## Acceptance Criteria Verification

1. **Allowlist enforcement**: `check_allowed_repo()` normalizes owner/repo, rejects missing values, denies when allowlist is empty
2. **Tool set consolidation**: Both `tool_policy.py` and `tool_approval.py` import `GITHUB_WRITE_TOOLS` from `shared/tool_constants.py`
3. **No dead GitOps fields**: `gitops_force_push_blocked` and `gitops_protected_branches` both have runtime behavior
4. **No bypass**: `skip_in_workflow_mode` still works but is logged for auditability
5. **Audit trail**: All GitOps denials emit audit decisions
