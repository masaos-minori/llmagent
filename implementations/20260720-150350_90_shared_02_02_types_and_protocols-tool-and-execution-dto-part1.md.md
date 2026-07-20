# Implementation procedure: `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto-part1.md` (browser_fetch merge references)

Source plan: `plans/20260720-135137_plan.md`, Implementation step 11; Affected areas doc-files row
(UNK-04: documentation-fix-required).

No prior implementation doc targets this filename for the browser-merge concern. New document.

## Goal

Update this doc's reference to `browser-mcp browser_fetch` (as the tool that first exercised
`RuntimeTool`/`build_runtime_tool()` with real data) so it reflects the merged server name.

## Scope

**In scope**: line 184 (confirmed via direct grep/read).
**Out of scope**: the rest of the `RuntimeTool`/DTO discussion — unaffected by which server hosts
`browser_fetch`.

## Assumptions

1. Line 184: "**[Explicit in code]** browser-mcp `browser_fetch` ツールが `config_dependent: True`
   を採用したことで、`RuntimeTool` / `build_runtime_tool()` が初めて実データで使用されている。..." —
   the substantive claim (this tool was the first real-data user of `RuntimeTool`) remains true
   post-merge; only the server-name framing ("browser-mcp") is stale.

## Implementation

### Target file

`docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto-part1.md`

### Procedure

1. Line 184: change "browser-mcp `browser_fetch` ツールが" to "web_search-mcp の `browser_fetch`
   ツールが" (same substitution pattern as the companion `04_mcp_08`/`04_mcp_90` docs). Leave the
   rest of the sentence ("`config_dependent: True` を採用したことで、`RuntimeTool` /
   `build_runtime_tool()` が初めて実データで使用されている。MCPツールディスカバリによる実データの
   投入も完了済み") unchanged — the historical/factual claim is unaffected by the merge.

### Method

Single in-place substitution, same pattern as the other doc-set entries in this plan.

### Details

- No other `browser`/8016 reference exists in this file (confirmed via full grep — one hit only).

## Validation plan

| Check | Command | Target |
|---|---|---|
| MCP docs consistency | `uv run check-mcp-docs` | passes |
| Scoped grep | `grep -n "browser-mcp" docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto-part1.md` | 0 matches after edit |
