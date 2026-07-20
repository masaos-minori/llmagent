# Implementation procedure: `docs/05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md` (browser_fetch merge references — verification, no edit)

Source plan: `plans/20260720-135137_plan.md`, Implementation step 11; Affected areas doc-files row
(UNK-04).

No prior implementation doc targets this filename for the browser-merge concern. New document.

## Goal

Verify whether this doc contains any `browser-mcp`/`browser_fetch`/port-8016 reference needing
removal, and record the finding.

## Scope

**In scope**: full-file grep and read of
`docs/05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md` (118 lines).
**Out of scope**: no other file.

## Assumptions

1. Same rationale as the companion `04_mcp_03_02_tool-registry.md` verification doc: the plan's
   Affected-areas table listed this file on the strength of the source requirement's (unverified)
   file list; this design cycle performs the per-file check the plan's UNK-04 deferred.

## Implementation

### Target file

`docs/05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md`

### Procedure

1. `grep -n -i "browser\|8016\|mcp server"` against the file: **zero matches** for `browser`/`8016`
   (confirmed during this design cycle's research); the file's `/session export` command-table row
   is the only "mcp server"-adjacent-looking hit and is unrelated (a CLI command description, no
   server-name content).
2. Conclusion: no browser-mcp-specific content exists in this file today. No text edit is required
   for the browser-merge concern.

### Method

Verification only — no content change.

### Details

- This file documents CLI slash-commands and session/MCP interaction at the agent-CLI layer, not
  individual MCP server registrations — consistent with it having no server-specific content to
  update.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Scoped grep | `grep -n -i "browser\|8016" docs/05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md` | 0 matches (re-verify unchanged at implementation time) |
| MCP docs consistency | `uv run check-mcp-docs` | passes (this file requires no change to keep passing) |
