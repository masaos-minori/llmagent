# Implementation procedure: `docs/04_mcp_90_inconsistencies_and_known_issues.md` (browser_fetch merge references)

Source plan: `plans/20260720-135137_plan.md`, Implementation step 11; Affected areas doc-files row
(UNK-04: documentation-fix-required).

No prior implementation doc targets this filename for the browser-merge concern. New document.

## Goal

Update this doc's "Impact scope"/"Current behavior" bullet referencing
`scripts/mcp_servers/browser/` and `browser-mcp browser_fetch` so they reflect the merged location
and server name.

## Scope

**In scope**: lines 41-42 (confirmed via direct grep/read).
**Out of scope**: the rest of the known-issues entry this bullet belongs to (the
`config_dependent`/`enabled`/`disabled_reason` gap discussion) — the underlying issue description
(not yet all servers adopting `config_dependent`) is unaffected by the merge and stays as-is.

## Assumptions

1. Line 41: `` - **Impact scope:** `scripts/mcp_servers/browser/`（`config_dependent`採用済み）、
   `scripts/agent/**`（RuntimeToolRegistry配線済み） `` — the path
   `scripts/mcp_servers/browser/` no longer exists after this merge (per the browser-directory-
   deletion doc); the tool now lives at `scripts/mcp_servers/web_search/`.
2. Line 42: "**Current behavior:** browser-mcp `browser_fetch` が `config_dependent: True` を採用
   した。..." — same "browser-mcp" framing as the other docs in this set.
3. This is a "documentation fix required" case per `rules/coding.md`'s classification table (stale
   path/server-name reference, not a code bug) — confirmed, matching UNK-04's blanket resolution for
   all 8 files.

## Implementation

### Target file

`docs/04_mcp_90_inconsistencies_and_known_issues.md`

### Procedure

1. Line 41: change `` `scripts/mcp_servers/browser/`（`config_dependent`採用済み） `` to
   `` `scripts/mcp_servers/web_search/`（`browser_fetch` の `config_dependent` 採用済み、
   web_search-mcp に統合） ``.
2. Line 42: change "browser-mcp `browser_fetch` が" to "web_search-mcp の `browser_fetch` が" (same
   substitution pattern as the companion `04_mcp_08` doc).

### Method

Two in-place substitutions — path update (line 41) and server-name framing update (line 42) — no
change to the surrounding known-issue's substantive claim (that `enabled`/`disabled_reason` are
still missing from `/v1/tools` responses and other servers haven't adopted `config_dependent` yet;
both remain true post-merge).

### Details

- Do not remove this known-issue entry entirely — the underlying gap (other MCP servers not yet
  adopting `config_dependent`) is unrelated to the browser merge and still applies.

## Validation plan

| Check | Command | Target |
|---|---|---|
| MCP docs consistency | `uv run check-mcp-docs` | passes |
| Scoped grep | `grep -n "mcp_servers/browser\|browser-mcp" docs/04_mcp_90_inconsistencies_and_known_issues.md` | 0 matches after edit |
