# Implementation procedure: `docs/04_mcp_03_06_tool-runtime-availability-metadata.md` (browser_fetch merge references)

Source plan: `plans/20260720-135137_plan.md`, Implementation step 11; Affected areas doc-files row
(UNK-04: documentation-fix-required).

No prior implementation doc targets this filename for the browser-merge concern (no prior hits
under `implementations/`/`implementations/done/`). New document.

## Goal

Update this doc's two references to `browser-mcp` as a standalone server so they instead describe
`browser_fetch` as a tool served by `web_search-mcp`, reflecting the merge.

## Scope

**In scope**: lines 22 and 26 (confirmed via direct grep/read), both inside the file's
"Implementation status" callout and adjoining prose paragraph.
**Out of scope**: the rest of the file's discussion of `config_dependent`/`enabled`/
`disabled_reason` semantics — unrelated to the server-consolidation change, untouched.

## Assumptions

1. Line 22: `> **Implementation status:** As of 2026-07-20 `config_dependent` is adopted for
   browser-mcp `browser_fetch` tool. ...` — the phrase "for browser-mcp `browser_fetch` tool"
   describes `browser_fetch` as belonging to a standalone `browser-mcp` server, which is no longer
   accurate post-merge.
2. Line 26: "...browser-mcp `browser_fetch` tool is the first to adopt `config_dependent: True`." —
   same pattern.
3. No other line in this file mentions `browser`/8016 (confirmed via full grep — only these two
   hits exist).

## Implementation

### Target file

`docs/04_mcp_03_06_tool-runtime-availability-metadata.md`

### Procedure

1. Line 22: change "`config_dependent` is adopted for browser-mcp `browser_fetch` tool" to
   "`config_dependent` is adopted for `web_search-mcp`'s `browser_fetch` tool (merged from the
   former standalone browser-mcp server)".
2. Line 26: change "browser-mcp `browser_fetch` tool is the first to adopt" to
   "`web_search-mcp`'s `browser_fetch` tool is the first to adopt" (drop the "browser-mcp" framing
   consistently with line 22's rewrite).

### Method

Two-sentence prose edits, English (file's existing language for this section, unlike some other
docs in this set which are Japanese) — no structural/heading change.

### Details

- Keep the parenthetical "(merged from the former standalone browser-mcp server)" only on the
  first occurrence (line 22) to avoid repetitive phrasing; line 26 can read simply
  "`web_search-mcp`'s `browser_fetch` tool" without repeating the merge history.
- Re-run `uv run check-mcp-docs` after editing — it checks for stale "browser-mcp" server
  references project-wide per its documented checks.

## Validation plan

| Check | Command | Target |
|---|---|---|
| MCP docs consistency | `uv run check-mcp-docs` | passes |
| Scoped grep | `grep -n -i "browser-mcp" docs/04_mcp_03_06_tool-runtime-availability-metadata.md` | 0 matches after edit |
| Manual read | lines 20-28 | reads naturally, consistent with `web_search-mcp` framing used elsewhere in the merged docs |
