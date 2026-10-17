# Enable approval dry-run previews for GitHub tools

## Priority
Medium

## Summary
Approval dry-run enrichment is disabled for GitHub tools because they are absent
from the default `approval_dry_run_tools` allowlist. When a high-risk GitHub tool
requires approval, the preview shows only static text without executing a dry run.
Add GitHub tools to the dry-run allowlist (or otherwise enable dry-run previews
for them) so approvers see real dry-run output.

## Background
`_build_preview_with_dry_run()` in `scripts/agent/tool_approval.py` enriches the
approval preview with actual dry-run output, but only when the tool is in
`cfg.approval.approval_dry_run_tools`:

```python
if (
    tool_name not in ctx.cfg.approval.approval_dry_run_tools
    or ctx.services_required.tools is None
):
    return preview   # static preview only; dry-run path dormant
```

`_DEFAULT_DRY_RUN_TOOLS` in `scripts/agent/constants.py` is:
`[write_file, edit_file, create_directory, delete_file, delete_directory, move_file]`
— no GitHub tools. `docs/23_agent/agent_06_02_...approval.md` and
`agent_06_03_...concurrency-safety.md` both note the GitHub dry-run path is
currently dormant.

## Problem
GitHub tool calls that require approval present a static preview without a dry
run, so approvers cannot see what the operation would actually do before
approving. This reduces the effectiveness of the approval gate for a high-risk
category. It is related to Known Issue MCP-006 (uneven protection-layer coverage
for high-risk tool categories): enabling dry-run is one concrete step toward
parity with the file tools, which already get dry-run previews.

## Reason for Change
Approval is the last human-controlled barrier before a dangerous GitHub operation
(e.g. push, create issue, edit repo). A dry-run preview materially improves
decision quality. The mechanism already exists; it is simply not enabled for
GitHub tools.

## Implementation Intent
Add the relevant GitHub tool names to `_DEFAULT_DRY_RUN_TOOLS` (or configure the
allowlist to include them), provided the GitHub server supports a `dry_run`
argument (checked by `_is_dry_run_capable()`). If GitHub tools do not support
dry_run, `_build_preview_with_dry_run` already falls back to a static preview with
a warning, so adding them to the list is safe but only beneficial if dry_run is
supported. Confirm dry_run support before enabling.

## Target Files or Areas
- `scripts/agent/constants.py` (`_DEFAULT_DRY_RUN_TOOLS`)
- `scripts/agent/tool_approval.py` (`_build_preview_with_dry_run`, `_is_dry_run_capable`)
- The GitHub MCP server definition (confirm which tool names and whether they accept `dry_run`)

## Required Changes
- Add GitHub tool names to `_DEFAULT_DRY_RUN_TOOLS` if the server supports dry_run.
- If dry_run is not supported by GitHub tools, document that explicitly rather
  than silently enabling a no-op, and consider it under MCP-006.
- Ensure the change is configurable (does not hard-code around the config field).

## Constraints
- Do not enable dry-run for tools that lack dry_run support (they fall back to
  static preview anyway, but avoid misleading previews).
- Preserve the existing allowlist mechanism and validation
  (`_validate_dry_run_tools`).
- Do not weaken the approval gate; dry-run enrichment is additive.

## Acceptance Criteria
- GitHub tools that support dry_run produce a dry-run-enriched approval preview.
- GitHub tools that do not support dry_run fall back to the static preview with
  the existing warning (no regression).
- The allowlist remains configurable via `approval.dry_run_tools`.

## Testing Expectations
- Unit test that a dry_run-capable GitHub tool name is in the effective
  allowlist and yields a dry-run-enriched preview.
- Regression test for the non-capable fallback path.
- Confirm `_is_dry_run_capable` correctly classifies GitHub tools.

## Documentation Impact
Update the "dormant" notes in
`docs/23_agent/agent_06_02_...approval.md` / `agent_06_03_...concurrency-safety.md`
to reflect whether dry-run is now enabled for GitHub tools.

## Out of Scope
- Adding new GitHub tools to the MCP server.
- Changing the approval gate logic itself.
- Other high-risk tool categories (scope per MCP-006 re-audit).

## Dependencies
- Known Issue MCP-006 (`issues/20261017-115004_mcp006_...md`) — this issue is one
  concrete resolution avenue for the GitHub category; re-verify against current
  source, since MCP-006 is a historical snapshot and github may already ship
  guards.

## Unresolved Questions
- Which exact GitHub tool names exist and whether they accept a `dry_run`
  argument.
- Whether enabling dry-run changes approval timing/UX in a way that needs
  operator config.

## AI Implementation Instruction
Confirm the GitHub server tools accept `dry_run` before changing anything. If
they do, add their names to `_DEFAULT_DRY_RUN_TOOLS` in
`scripts/agent/constants.py`. If they do not, do NOT add them; instead record the
finding as part of MCP-006. Do not modify `_is_dry_run_capable` or the approval
gate. Add a unit test for the enabled path.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261017-123420
- **Related target files**: `scripts/agent/constants.py`, `scripts/agent/tool_approval.py`
