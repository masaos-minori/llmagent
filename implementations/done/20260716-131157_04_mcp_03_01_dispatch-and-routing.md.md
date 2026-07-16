# Implementation: docs/04_mcp_03_01_dispatch-and-routing.md (update `MDQ_TOOLS` list)

Source plan: `plans/20260716-123031_plan.md`

## Goal

Update the `MDQ_TOOLS` row in the tool-routing table (line 79) to drop
`fts_consistency_check`, `fts_rebuild` from the parenthetical tool-name
list, matching the trimmed `MDQ_TOOLS` frozenset (companion
`tool_constants.py` doc).

## Scope

**In:**
- The table row (current line 79):
  ```
  | `MDQ_TOOLS` (search_docs, get_chunk, outline, index_paths, refresh_index, stats, grep_docs, fts_consistency_check, fts_rebuild) | `mdq` |
  ```

**Out:**
- Any other row in the table (`READ_TOOLS`, `WRITE_TOOLS`, `DELETE_TOOLS`,
  `GITHUB_TOOLS`, `RAG_TOOLS`, `CICD_TOOLS`, `GIT_TOOLS`).
- The surrounding explanatory text ("重要:" note, code example below the
  table).

## Assumptions

1. This table documents `ToolRouteResolver`'s routing source-of-truth
   (`scripts/shared/tool_constants.py`'s frozensets) — it must be updated in
   the same change set as the companion `tool_constants.py` doc to avoid
   the doc drifting from code immediately after that change lands.

## Implementation

### Target file

`docs/04_mcp_03_01_dispatch-and-routing.md`

### Procedure

1. Open `docs/04_mcp_03_01_dispatch-and-routing.md`.
2. Locate the table row (current line 79):
   ```
   | `MDQ_TOOLS` (search_docs, get_chunk, outline, index_paths, refresh_index, stats, grep_docs, fts_consistency_check, fts_rebuild) | `mdq` |
   ```
3. Replace with:
   ```
   | `MDQ_TOOLS` (search_docs, get_chunk, outline, index_paths, refresh_index, stats, grep_docs) | `mdq` |
   ```

### Method

Single table-cell text edit — remove two names from a parenthetical list;
no change to table structure or the `mdq` routing-key column.

### Details

- Preserve the exact Markdown table pipe (`|`) alignment style used
  elsewhere in the table (this table does not appear to pad columns to a
  fixed width, based on the surrounding rows — match whatever the adjacent
  rows do).

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Names removed | `grep -n "fts_consistency_check\|fts_rebuild" docs/04_mcp_03_01_dispatch-and-routing.md` | 0 matches |
| Doc consistency | `uv run check-mcp-docs` | passes |
