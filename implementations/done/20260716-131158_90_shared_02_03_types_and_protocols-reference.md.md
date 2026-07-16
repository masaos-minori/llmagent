# Implementation: docs/90_shared_02_03_types_and_protocols-reference.md (update `MDQ_TOOLS` list)

Source plan: `plans/20260716-123031_plan.md`

## Goal

Update the `MDQ_TOOLS` row in the constants-reference table (line 53) to
drop `fts_consistency_check`, `fts_rebuild` and correct the trailing
`(9 tools)` count to `(7 tools)`.

## Scope

**In:**
- The table row (current line 53):
  ```
  | `MDQ_TOOLS` | `search_docs`, `get_chunk`, `outline`, `index_paths`, `refresh_index`, `stats`, `grep_docs`, `fts_consistency_check`, `fts_rebuild` (9 tools) |
  ```

**Out:**
- Any other row in the table (`READ_TOOLS`, `WRITE_TOOLS`, `DELETE_TOOLS`,
  `RAG_TOOLS`, `CICD_TOOLS`, `GIT_TOOLS`, `SHELL_TOOLS`, `WEB_SEARCH_TOOLS`).
- The trailing note ("`shared/tool_executor.py` および `agent/tool_runner.py`
  からも参照される。").

## Assumptions

1. This table mirrors `scripts/shared/tool_constants.py`'s frozensets
   (companion doc) — the `(9 tools)` suffix must become `(7 tools)` to stay
   accurate, matching the style already used for `READ_TOOLS` (`(9 tools)`)
   and `WRITE_TOOLS` (`(4 tools)`) elsewhere in the same table.

## Implementation

### Target file

`docs/90_shared_02_03_types_and_protocols-reference.md`

### Procedure

1. Open `docs/90_shared_02_03_types_and_protocols-reference.md`.
2. Locate the table row (current line 53):
   ```
   | `MDQ_TOOLS` | `search_docs`, `get_chunk`, `outline`, `index_paths`, `refresh_index`, `stats`, `grep_docs`, `fts_consistency_check`, `fts_rebuild` (9 tools) |
   ```
3. Replace with:
   ```
   | `MDQ_TOOLS` | `search_docs`, `get_chunk`, `outline`, `index_paths`, `refresh_index`, `stats`, `grep_docs` (7 tools) |
   ```

### Method

Single table-cell text edit — remove two backtick-quoted names and update
the trailing count annotation.

### Details

- Match the existing convention in this table of appending `(N tools)` only
  to rows that already have it (`READ_TOOLS`, `WRITE_TOOLS`,
  `DELETE_TOOLS`, `MDQ_TOOLS`) — `RAG_TOOLS`/`CICD_TOOLS`/etc. do not have
  a count suffix in the current table and should not gain one as a side
  effect of this edit.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Names/count updated | `grep -n "MDQ_TOOLS" docs/90_shared_02_03_types_and_protocols-reference.md` | shows 7 names, `(7 tools)` |
| Stale names removed | `grep -n "fts_consistency_check\|fts_rebuild" docs/90_shared_02_03_types_and_protocols-reference.md` | 0 matches |
| Doc consistency | `uv run check-mcp-docs` | passes |
