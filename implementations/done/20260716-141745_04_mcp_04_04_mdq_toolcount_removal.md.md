# Implementation: docs/04_mcp_04_04_mdq.md (drop `（7個）` from the tool heading)

Source plan: `plans/20260716-135355_plan.md`

Note: this is a distinct change from the three other `04_mcp_04_04_mdq.md`
docs already created for the earlier MDQ compatibility-cleanup batch
(`implementations/done/` — `audit_log_path` note, tool-count 9→7,
embedding/hybrid removal, summary-field removal). This doc removes the
`（7個）` parenthetical from the tool heading entirely — a further,
independent edit on the same line those earlier docs already updated to
say "7個". Apply this after those, not instead of them.

## Goal

Remove the `（7個）` parenthetical from the `**ツール（7個）:**` heading,
leaving `**ツール:**` followed by the same 7 tool names.

## Scope

**In:**
- Line 24: `**ツール（7個）:** \`search_docs\`, \`get_chunk\`, \`outline\`, \`index_paths\`, \`refresh_index\`, \`stats\`, \`grep_docs\``

**Out:**
- Any other line in this doc (config field list, tool status line, hybrid
  -search section, etc. — already handled by the earlier MDQ-cleanup-batch
  docs for this same file).

## Assumptions

1. By the time this edit lands, the tool count on this line already
   correctly reads "7個" (per the companion plan-02 doc from the earlier
   MDQ batch, `implementations/20260716-131156_04_mcp_04_04_mdq.md.md`,
   which updated it from "9個") — this edit removes the parenthetical
   entirely rather than correcting a stale number, since the number is
   already accurate at this point; the goal here is purely to eliminate
   the maintenance-burden literal, not to fix drift.

## Implementation

### Target file

`docs/04_mcp_04_04_mdq.md`

### Procedure

1. Open `docs/04_mcp_04_04_mdq.md`.
2. Locate the line (content-match, since exact line number may have
   shifted slightly from prior edits in the same file by other plans in
   this batch):
   ```
   **ツール（7個）:** `search_docs`, `get_chunk`, `outline`, `index_paths`, `refresh_index`, `stats`, `grep_docs`
   ```
3. Replace with:
   ```
   **ツール:** `search_docs`, `get_chunk`, `outline`, `index_paths`, `refresh_index`, `stats`, `grep_docs`
   ```

### Method

Single mechanical parenthetical removal.

### Details

- Do not alter any tool name in the listing.
- Do not touch the separate "ツールステータス" (tool status) line
  elsewhere in this doc — that line is out of scope for this specific
  edit (it was already handled by the earlier MDQ-batch companion doc).

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Parenthetical removed | `grep -n "ツール（[0-9]*個）" docs/04_mcp_04_04_mdq.md` | 0 matches |
| Tool listing intact | `grep -n "search_docs.*get_chunk.*outline" docs/04_mcp_04_04_mdq.md` | present, unchanged |
| Doc consistency | `uv run check-mcp-docs` | passes (once companion `check_mcp_docs_consistency.py` Check-5 removal also lands) |
