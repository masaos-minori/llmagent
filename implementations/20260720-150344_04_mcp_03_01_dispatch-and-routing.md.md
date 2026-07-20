# Implementation procedure: `docs/04_mcp_03_01_dispatch-and-routing.md` (browser_fetch merge references)

Source plan: `plans/20260720-135137_plan.md`, Implementation step 11; Affected areas doc-files row
(UNK-04: documentation-fix-required, no code-behavior discrepancy).

A prior doc for this exact filename already exists at
`implementations/20260720-142522_04_mcp_03_01_dispatch-and-routing.md.md` (pending, not in
`implementations/done/`) — read in full. It targets a different, unrelated plan
(`plans/done/20260720-134821_plan.md`, rewriting "two-tier routing-authority" language to
"sole authority" language) and explicitly scopes itself to the "ToolRouteResolver" section, the
ownership-layers diagram, and "ルーティングの信頼できる情報源" section — it does not touch the
tool-set/server-key mapping table this doc targets (a different table, lines 74-86, listing
frozenset-name → server_key rows). No overlap. New document.

## Goal

Update the tool-set → server-key mapping table (current lines 74-86, direct read confirmed) so it
reflects that `browser_fetch` now routes to `server_key="web_search"` via the merged
`WEB_SEARCH_TOOLS` frozenset, closing a pre-existing gap where this table lists `search_web` but
has never listed `browser_fetch`/`BROWSER_TOOLS` at all (confirmed via direct read: no
`browser`/`BROWSER_TOOLS` row exists in the table today, even pre-merge — a stale omission this
merge is a natural opportunity to fix).

## Scope

**In scope**: the table at lines 74-86 (row `| `search_web` | `web_search` |` at line 80) and its
immediately surrounding prose (lines 88, 90-93), all in
`docs/04_mcp_03_01_dispatch-and-routing.md`.
**Out of scope**: the "ToolRouteResolver" priority-list section (lines ~58-72), ownership-layers
diagram (~line 129), and "ルーティングの信頼できる情報源" section (~163-192) — these are the other
pending doc's exclusive scope (routing-authority two-tier→single-tier language), confirmed
unrelated to this table.

## Assumptions

1. Confirmed via direct read: this table's rows are keyed by *frozenset name* for multi-tool
   frozensets (`READ_TOOLS (9 tools: ...)`, `GITHUB_TOOLS (...)`, `MDQ_TOOLS (...)`) but by *bare
   tool name* for single-tool frozensets (`shell_run`, `search_web`) — i.e. the table's convention
   drops the frozenset name when it has exactly one member. Since `WEB_SEARCH_TOOLS` now has two
   members (`search_web`, `browser_fetch`) after the merge, the row should switch to the
   multi-tool convention: `WEB_SEARCH_TOOLS (search_web, browser_fetch)` | `web_search`.
2. No other row in this table needs a change — `BROWSER_TOOLS` never had its own row to remove
   (the gap predates this merge), so this is purely an addition/rename of the existing `search_web`
   row, not a deletion.

## Implementation

### Target file

`docs/04_mcp_03_01_dispatch-and-routing.md`

### Procedure

1. Change line 80 from `| `search_web` | `web_search` |` to
   `| `WEB_SEARCH_TOOLS` (search_web, browser_fetch) | `web_search` |`, matching the multi-tool
   row convention used by `READ_TOOLS`/`GITHUB_TOOLS`/`MDQ_TOOLS` etc.
2. Re-check lines 88-93 (the "新しいツールは常に `ToolRegistry` を経由して登録" note and the
   `resolver.resolve("read_text_file")` code sample) for any incidental `browser`/8016 mention —
   confirmed via direct read: none present; no edit needed there.
3. Re-run `uv run check-mcp-docs` after the edit (validates tool-count/routing-doc consistency
   project-wide — this file is one of its inputs).

### Method

Single table-row edit (rename + add one tool name), matching the file's existing Markdown table
formatting and Japanese-prose conventions exactly. No structural change to the table.

### Details

- Do not touch the `BROWSER_TOOLS` naming anywhere else in this file — grep confirms this table is
  the only place `search_web`'s frozenset membership is enumerated in this doc.

## Validation plan

| Check | Command | Target |
|---|---|---|
| MCP docs consistency | `uv run check-mcp-docs` | passes |
| Scoped grep | `grep -n "WEB_SEARCH_TOOLS\|browser_fetch" docs/04_mcp_03_01_dispatch-and-routing.md` | shows the updated row |
| Manual read | full re-read of the table | `web_search` row now lists both tools; no other row altered |
