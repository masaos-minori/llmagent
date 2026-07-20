# Implementation procedure: `docs/04_mcp_07_tool_schema_export_policy.md` (cross-reference to tracked duplicate-file issue)

Source plan: `plans/20260719-202346_plan.md`, Implementation step Phase 1 / Design §6.

One prior doc exists for this exact filename: `implementations/done/20260701-172000_04_mcp_07_tool_schema_export_policy.md`.
Opened and checked by content — that doc's goal was rewriting the file from "migration plan"
framing to "current policy" framing (removing "servers that need to migrate" future-tense
language, confirming all servers now export `TOOL_LIST`). It predates and is unrelated to the
`ca6b7bfe`/`abcf0820` duplicate-file situation this plan's task addresses (that issue did not
exist when the July 1 doc was written). Flagged as checked, not a genuine overlap — this is a
new document.

## Goal

Add a short cross-reference line near `docs/04_mcp_07_tool_schema_export_policy.md`'s per-server
canonical-filename table (the "移行履歴" / migration-history numbered list, verified at lines
31-39) pointing to the already-tracked `issues/20260719-193357_risks.md`, so a future reader does
not treat the table's bare `tools.py`/`server.py` filenames as unambiguously canonical without
knowing about the tracked duplicate-file discrepancy for `web_search` (and 7 other servers).

## Scope

**In scope**
- One added line/note near the migration-history list (lines 31-39 in the current file — item 6,
  `web_search — scripts/mcp_servers/web_search/tools.py, scripts/mcp_servers/web_search/server.py`,
  is the specific line relevant to this plan's `web_search` scope, but the cross-reference should
  cover the list as a whole since 7 other servers are affected too, per the plan's framing).
- Per `rules/coding.md`'s "Current behavior" classification table, this is the **"Issue already
  tracked"** category: cross-reference the existing entry, do not duplicate the explanation of the
  duplicate-file problem in this doc.

**Out of scope**
- Rewriting the migration-history section itself (already correct as a historical record of the
  `_MCP_TOOLS` → `TOOL_LIST` migration; the *new* problem is unrelated — old-named bare files were
  left on disk alongside the new `<server>_tools.py`/`<server>_server.py` names after a later
  rename, per `issues/20260719-193357_risks.md`).
- Re-describing or re-diagnosing the duplicate-file issue in prose — that is
  `issues/20260719-193357_risks.md`'s job; this doc only points to it.

## Assumptions

1. Verified directly: `docs/04_mcp_07_tool_schema_export_policy.md` lines 31-39 are the
   "### 移行履歴" (migration history) numbered list, item 6 reading
   `**web_search** — \`scripts/mcp_servers/web_search/tools.py\`, \`scripts/mcp_servers/web_search/server.py\``
   — i.e., it still names the bare (now-superseded-by-rename, and per the plan's Revised note,
   now further affected by commit `abcf0820`'s deletion of the orphaned bare files) filenames
   without qualification.
2. `issues/20260719-193357_risks.md` exists (verified via `ls issues/`) and is the correct,
   already-tracked entry to cross-reference — this doc must not create a second tracking file for
   the same discrepancy (would violate the "Issue already tracked" rule in `rules/coding.md`).
3. The doc's `related:` YAML frontmatter (lines 8-10) already lists `04_mcp_03_02_tool-registry.md`
   as a related doc; the new cross-reference to `issues/20260719-193357_risks.md` is added as
   inline prose near the migration-history list, not as a frontmatter `related:` entry (issues/
   files are not part of the docs cross-reference frontmatter convention used elsewhere in this
   file — verified no other doc lists an `issues/*.md` path in `related:`).

## Implementation

### Target file

`docs/04_mcp_07_tool_schema_export_policy.md`, near lines 31-39 (the "### 移行履歴" list).

### Procedure

1. Re-read the current "### 移行履歴" section end-to-end (lines 26-39) to confirm exact insertion
   point (immediately after the numbered list, before the next `###` heading, i.e. "### 検証").
2. Insert one short paragraph (Japanese, matching the doc's existing language) noting: some
   servers' bare `tools.py`/`server.py` filenames listed above coexisted with later `<server>_*`
   renamed files; the current on-disk state and its follow-up are tracked in
   `issues/20260719-193357_risks.md` (do not restate the issue's content here).
3. Do not alter the numbered list items themselves — the historical migration record stays as-is.

### Method

Pseudocode (prose sketch, not a code block since this is a Markdown doc, not source):

```
### 移行履歴
...(existing numbered list, unchanged)...

注: 一部のサーバーではベア名 (tools.py/server.py) のファイルと、後の命名変更による
<server>_tools.py/<server>_server.py が併存していた期間があった。現状と対応は
issues/20260719-193357_risks.md で追跡している。

### 検証
...(existing, unchanged)...
```

### Details

- Keep the added note to 1-2 sentences; the goal is discoverability (a reader following the
  per-server table sees the flag and follows the link), not a full re-explanation.
- No frontmatter change needed — `related:` already covers the adjacent registry doc; this is a
  body-text addition only.
- This is a documentation-only edit; no source file, config, or test is touched by this item.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Doc consistency | `uv run check-mcp-docs` | passes — no wording this check flags (fail-open language, routing-authority phrasing, active-issue cross-references) is affected |
| Manual read | re-read full file after edit | note reads clearly, does not duplicate `issues/20260719-193357_risks.md`'s content, link path is correct relative to repo root |
| Link target exists | `ls issues/20260719-193357_risks.md` | file present |
