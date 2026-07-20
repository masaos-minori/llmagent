# Implementation procedure: close out `issues/20260720-070458_mcp_server_agent_toml_cmd_points_to_deleted_files.md`

Source plan: `plans/20260720-073534_plan.md`, Implementation step Phase 3, item 2.

No prior implementation doc targets this filename (verified via `ls implementations/done/ | grep`). New
document.

## Goal

Update the critical issue's status to resolved once the `config/agent.toml` fix and the new regression
test (`tests/test_mcp_server_cmd_paths.py`) both land and pass, so the issue tracker accurately reflects
that the 8-server startup-breaking bug is fixed in the repo (while still flagging that a `deploy` run is
needed to propagate the fix to any already-running production processes).

## Scope

**In scope**
- `issues/20260720-070458_mcp_server_agent_toml_cmd_points_to_deleted_files.md`'s `## Status` section —
  update from "Plan written, not yet implemented" to resolved, cross-referencing the landed commit and
  the new test.

**Out of scope**
- Any other section of the issue file (Context/Evidence/Impact/Recommended action/Affected in-flight
  plans) — those remain accurate historical record of the bug and do not need editing.
- Actually running `deploy` — this doc only updates the issue's status to reflect the repo-level fix;
  production redeployment is a separate, explicit-approval step per the plan's own Scope section.

## Assumptions

1. This step is ordered last in the plan's Implementation steps (Phase 3), after both the config fix and
   the regression test are implemented and verified — the status update must not land before the actual
   fix, or the issue would falsely claim resolution.
2. The existing `## Status` section (verified by direct read) currently reads: "Plan written, not yet
   implemented (2026-07-20). See `plans/20260720-073534_plan.md` for the concrete fix... implementation
   requires explicit approval, and redeploying the fix to `/opt/llm` requires a separate `deploy` step
   after that." This entire paragraph is what gets replaced.

## Implementation

### Target file

`issues/20260720-070458_mcp_server_agent_toml_cmd_points_to_deleted_files.md`

### Procedure

1. Replace the `## Status` section's content with a resolved statement: fix landed in
   `config/agent.toml` (8 `cmd` entries corrected), regression test
   `tests/test_mcp_server_cmd_paths.py` added and passing, cross-reference the plan and the commit SHA
   once known at implementation time.
2. Explicitly retain the note that production redeployment (`deploy` skill) is a separate follow-up step
   not covered by this fix alone, so a reader doesn't assume the running production servers are already
   fixed the moment this file is edited.

### Method

Direct Markdown section replacement (prose, not a code block) — illustrative text:

```
## Status

Resolved (implemented at commit <fill in at landing time>). `config/agent.toml`'s 8 `cmd` entries now
point at each server's actual `<name>_server.py`; `tests/test_mcp_server_cmd_paths.py` locks this
invariant for all subprocess-mode MCP servers. Redeploying this fix to `/opt/llm` (so any currently
running/crashed production processes actually pick it up) is a separate step — run the `deploy` skill
after this fix is reviewed and merged.
```

### Details

- Do not remove or rewrite the rest of the issue file — it remains useful historical context (how the
  bug was found, why it's severe, which in-flight plans referenced it).
- If the implementer is working from a local branch/worktree without a final commit SHA yet, use a
  placeholder like "this commit" and let the PR/merge process fill in the SHA, rather than blocking the
  status update on knowing the SHA in advance.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Status updated | `grep -n "^## Status" -A5 issues/20260720-070458_mcp_server_agent_toml_cmd_points_to_deleted_files.md` | reads resolved, not "Plan written, not yet implemented" |
| No unrelated change | `git diff issues/20260720-070458_mcp_server_agent_toml_cmd_points_to_deleted_files.md` | only the `## Status` section modified |
| Docs consistency | `uv run check-mcp-docs` | passes |
