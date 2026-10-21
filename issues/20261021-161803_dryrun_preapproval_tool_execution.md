# Dry-run approval preview executes the target tool before the user approves

## Priority
Medium

## Summary
The interactive approval preview runs the target MCP tool with `dry_run=True` before the user has approved the call. For MEDIUM/HIGH-risk tools this means the tool executes during preview; if a whitelisted tool does not fully suppress side effects under `dry_run`, an unapproved mutation can occur. Verify that `dry_run=True` is a hard no-op for every whitelisted tool and document the pre-approval execution boundary.

## Background
`tool_approval.check_approval` builds a preview for MEDIUM/HIGH-risk calls via `_build_preview_with_dry_run`, then prompts the user interactively via `_prompt_user_approval`. `_build_preview_with_dry_run` calls `ctx.services_required.tools.execute(tool_name, {**args, "dry_run": True})` to enrich the preview with a simulated result. This is gated by `cfg.approval.approval_dry_run_tools` and limited to `_KNOWN_DRY_RUN_CAPABLE_TOOLS`.

## Problem
The preview is shown before the approval decision, yet the tool actually executes. The security boundary ("execute only after approval") is relaxed for preview enrichment. If any whitelisted tool treats `dry_run` as advisory (performs the write/delete/network action anyway), the preview becomes an unapproved execution.

## Reason for Change
Dry-run preview enrichment is enabled by config, so the pre-approval execution is now part of the runtime path. The contract that `dry_run=True` performs zero side effects is assumed but not enforced or documented per tool.

## Implementation Intent
- Enumerate every tool in `_KNOWN_DRY_RUN_CAPABLE_TOOLS` and confirm each server honors `dry_run=True` as a hard no-op (no write/delete/network/database side effect).
- Where a tool cannot guarantee a no-op dry_run, remove it from the whitelist or downgrade its preview to text-only (no execution).
- Document the pre-approval dry-run execution behavior and the no-op contract in the approval subsystem docs / Known Issues.

## Target Files or Areas
- `scripts/agent/tool_approval.py` (`_KNOWN_DRY_RUN_CAPABLE_TOOLS`, `_build_preview_with_dry_run`, `check_approval`)
- `scripts/shared/mcp_config.py` (tool registration / dry_run capability)
- Approval subsystem docs / Known Issues

## Required Changes
- Audit each whitelisted tool's `dry_run` semantics; record whether it is a guaranteed no-op.
- Remove any non-no-op tool from `_KNOWN_DRY_RUN_CAPABLE_TOOLS` (or drop it from the default `approval_dry_run_tools`).
- Add a guard/comment asserting the dry_run no-op contract at the whitelist definition.
- Document the pre-approval execution boundary and the no-op requirement.

## Constraints
- Must not change the interactive approval UX for approved calls.
- Dry-run preview failures must still degrade to text-only preview (existing behavior) rather than blocking approvals.
- Do not alter the whitelist for tools that already guarantee a no-op dry_run.

## Acceptance Criteria
- Every tool in `_KNOWN_DRY_RUN_CAPABLE_TOOLS` is confirmed to perform zero side effects under `dry_run=True`.
- No whitelisted tool can perform a write/delete/network action during the preview phase.
- The pre-approval dry-run execution behavior is documented.

## Testing Expectations
- Unit test confirming `dry_run=True` produces no side effect for each whitelisted tool (using a spy/fake executor that asserts `execute` was called with `dry_run=True` and no downstream mutation).
- Type check + lint pass.

## Documentation Impact
Document the dry-run pre-approval execution boundary and the per-tool no-op contract in the approval subsystem docs / Known Issues.

## Out of Scope
- Changing which tools require approval or their risk classification.
- Masking of preview args (separate concern; the interactive preview intentionally shows args for informed consent).

## Dependencies
N/A: none

## Unresolved Questions
- Are there whitelisted tools whose server-side `dry_run` is advisory rather than a hard no-op? (Needs confirmation against each MCP server.)
- Is `dry_run` passed through to nested/sub-tools, or only the top-level call?

## AI Implementation Instruction
Do not weaken the approval gate. The fix is verification + documentation + (if needed) whitelist narrowing, not changing the prompt flow. Confirm `dry_run` no-op per tool before removing anything from the whitelist.

## Traceability
- Workflow phase: python-code-review -> issue-creator
- Source issue: N/A: this document is the issue
- Source requirement: N/A: no standalone requirement document is generated
- Source plan: N/A: not filed from a Plan
- Source implementation procedure: N/A: not filed from an implementation procedure
- Generated at: 20261021-161803
- Related target files: scripts/agent/tool_approval.py, scripts/shared/mcp_config.py
```
