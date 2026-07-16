# Implementation: config/agent.toml (remove `fts_consistency_check`/`fts_rebuild` safety tiers and `tool_names` entries)

Source plan: `plans/20260716-123031_plan.md`

## Goal

Remove the two safety-tier lines and the two `tool_names` entries for
`fts_consistency_check`/`fts_rebuild` from `config/agent.toml`, resolving the
stale `# Needs confirmation — see UNK-01` comment on the `fts_consistency_check`
line by deleting it outright rather than investigating further (per the
source plan's Unknowns section: no matching UNK-01 entry describing this
line exists in `plans/done/`).

## Scope

**In:**
- Delete line 240: `fts_consistency_check    = "READ_ONLY"   # Needs confirmation — see UNK-01`
- Delete line 243: `fts_rebuild              = "WRITE_DANGEROUS"`
- In the `[mcp_servers.mdq]` block's `tool_names` list (lines 385-388),
  remove `"fts_consistency_check", "fts_rebuild"` from the list.

**Out:**
- Any other safety-tier line in this file (e.g. `search_docs`, `get_chunk`,
  `outline`, `stats`, `grep_docs`, `index_paths`, `refresh_index` — all
  remain unchanged).
- Any other `[mcp_servers.*]` block.
- `config/mdq_mcp_server.toml` — not touched by this plan (see the sibling
  plan `plans/20260716-121714_plan.md`/`plans/done/20260716-121714_plan.md`
  for `audit_log_path`-related config changes, which are unrelated).

## Assumptions

1. `config/agent.toml` is read at MDQ/agent startup to build the live tool
   set and safety-tier mapping (`ToolRegistry`/CLI startup, per the source
   plan's Affected areas table) — an incorrect edit could break startup if
   `tool_names` and the server's actual dispatch table diverge. This is
   mitigated by the source plan's Implementation step 7 (dev restart +
   `/v1/tools` check).
2. This change must land together with the `tools.py` change (companion
   doc) that removes the same two tools from `TOOL_LIST` — otherwise
   `tool_names` in this config could list a tool no longer present in the
   schema (or vice versa if done out of order).
3. Removing the `# Needs confirmation — see UNK-01` comment is safe because
   the plan's Unknowns section confirms no corresponding UNK-01 entry
   exists anywhere in `plans/done/` — the comment is stale and unresolvable,
   and deleting the line it annotates resolves the ambiguity by removing the
   subject entirely.

## Implementation

### Target file

`config/agent.toml`

### Procedure

1. Open `config/agent.toml`.
2. In the safety-tier section (around lines 235-249), delete line 240 in
   full:
   ```
   fts_consistency_check    = "READ_ONLY"   # Needs confirmation — see UNK-01
   ```
3. Delete line 243 in full:
   ```
   fts_rebuild              = "WRITE_DANGEROUS"
   ```
4. Confirm the surrounding lines (`stats`, `grep_docs`, `index_paths`,
   `refresh_index`, `rag_run_pipeline`, etc.) remain in their original order
   and alignment — do not re-align column spacing for unrelated lines.
5. In the `[mcp_servers.mdq]` block, locate `tool_names` (lines 385-388):
   ```toml
   tool_names       = [
     "search_docs", "get_chunk", "outline", "index_paths", "refresh_index",
     "stats", "grep_docs", "fts_consistency_check", "fts_rebuild",
   ]
   ```
   Change to:
   ```toml
   tool_names       = [
     "search_docs", "get_chunk", "outline", "index_paths", "refresh_index",
     "stats", "grep_docs",
   ]
   ```

### Method

Direct deletion of two safety-tier lines and two list entries — no
renaming, no tier reassignment for remaining tools.

### Details

- This is a production TOML config file — validate with a TOML parser
  after editing (e.g. `python -c "import tomllib; tomllib.load(open('config/agent.toml','rb'))"`)
  to catch any syntax error introduced by the edit (trailing comma issues,
  etc.) before running the full validation suite.
- Do not touch the column alignment (`=` positions) of unrelated lines in
  either the safety-tier block or elsewhere in the file.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| TOML syntax valid | `python -c "import tomllib; tomllib.load(open('config/agent.toml','rb'))"` | no exception |
| Safety-tier lines removed | `grep -n "fts_consistency_check\|fts_rebuild" config/agent.toml` | 0 matches |
| `tool_names` updated | `grep -n -A3 "tool_names" config/agent.toml \| grep -A3 "8013\|mdq"` (or inspect `[mcp_servers.mdq]` block directly) | list contains exactly 7 names, no `fts_*` |
| Doc consistency | `uv run check-mcp-docs` | passes, tool count matches |
| Dev restart check (manual) | restart `mdq-mcp` in dev, `curl` `/v1/tools` | returns exactly 7 tools, matches `_DISPATCH_TABLE` |
