# Implementation procedure: `docs/04_mcp_08_tool_capability_naming_convention.md` (browser_fetch merge references)

Source plan: `plans/20260720-135137_plan.md`, Implementation step 11; Affected areas doc-files row
(UNK-04: documentation-fix-required).

No prior implementation doc targets this filename for the browser-merge concern. New document.

## Goal

Update this doc's reference to `browser_fetch (browser-mcp)` so it reflects `browser_fetch` now
being served by `web_search-mcp`.

## Scope

**In scope**: lines 87 and 91 (confirmed via direct grep/read).
**Out of scope**: the rest of the capability-naming-convention discussion (unrelated to which
server hosts `browser_fetch`).

## Assumptions

1. Line 87: `` - `browser_fetch` (`browser-mcp`) — `("web_fetch",)` `` — a list entry mapping the
   tool to its hosting server and declared capability tuple. The server name in parentheses needs
   updating.
2. Line 91 (Japanese prose): "...browser-mcp `browser_fetch` が `web_fetch` ケイパビリティを宣言した
   ことで初めて実装に採用された。" — same "browser-mcp" framing needs updating.
3. No other line in this file mentions `browser`/8016 (confirmed via full grep — only these two
   hits).

## Implementation

### Target file

`docs/04_mcp_08_tool_capability_naming_convention.md`

### Procedure

1. Line 87: change `` `browser_fetch` (`browser-mcp`) — `("web_fetch",)` `` to
   `` `browser_fetch` (`web_search-mcp`) — `("web_fetch",)` ``.
2. Line 91: change "browser-mcp `browser_fetch` が" to "web_search-mcp の `browser_fetch` が"
   (Japanese phrasing adjustment; keep the rest of the sentence — "`web_fetch` ケイパビリティを宣言
   したことで初めて実装に採用された" — unchanged, since the capability-declaration fact itself is
   unaffected by which server hosts the tool).

### Method

Two small in-place substitutions (`browser-mcp` → `web_search-mcp`), preserving the surrounding
Markdown list/prose formatting exactly.

### Details

- This file's convention is illustrative (one example tool per capability), not an exhaustive
  registry — no other list entries need touching.

## Validation plan

| Check | Command | Target |
|---|---|---|
| MCP docs consistency | `uv run check-mcp-docs` | passes |
| Scoped grep | `grep -n "browser-mcp" docs/04_mcp_08_tool_capability_naming_convention.md` | 0 matches after edit |
