# Implementation: scripts/mcp_servers/mdq/tools.py (update `search_docs.mode` description to drop hybrid wording)

Source plan: `plans/20260716-131500_plan.md`

Note: distinct from the earlier `implementations/20260716-131146_mdq_tools.py.md`
(source plan `plans/done/20260716-123031_plan.md`), which removed the
`fts_consistency_check`/`fts_rebuild` `TOOL_LIST` entries. This doc edits the
`search_docs` entry's `mode` property description only — apply both changes,
they touch disjoint parts of `TOOL_LIST`.

## Goal

`search_docs`'s `mode` input-schema description states the single supported
value (`bm25`) and drops "grep" and "hybrid is not yet supported" wording,
matching the model-level restriction to `Literal["bm25"]` (companion
`models.py` doc).

## Scope

**In:**
- The `mode` property description inside the `search_docs` `TOOL_LIST`
  entry (`scripts/mcp_servers/mdq/tools.py:33-36`):
  ```python
  "mode": {
      "type": "string",
      "description": "Search mode: bm25/grep (hybrid is not yet supported)",
  },
  ```

**Out:**
- Any other property in `search_docs`'s `inputSchema`
  (`query`, `limit`, `path_prefix`, `tag_filter`, `heading_prefix`,
  `max_results_limit`, `max_total_result_chars`).
- The `search_docs` entry's top-level `description` field
  (`"Search indexed Markdown documents using BM25/FTS5. Markdown-only,
  structure-aware retrieval."`) — already accurate, no hybrid/grep mention,
  no change needed.
- Any other `TOOL_LIST` entry (`get_chunk`, `outline`, etc.).

## Assumptions

1. This description text is purely informational (JSON schema metadata
   surfaced to the LLM caller) — narrowing it to state only `bm25` does not
   change runtime validation; that enforcement comes from the companion
   `models.py` change (`Literal["bm25"]`).
2. This edit should land in the same commit as the `models.py` change
   (companion doc) so the advertised description and the actual accepted
   values stay consistent from the same commit onward.

## Implementation

### Target file

`scripts/mcp_servers/mdq/tools.py`

### Procedure

1. Open `scripts/mcp_servers/mdq/tools.py`.
2. Locate the `mode` property inside the `search_docs` entry (current
   lines 33-36):
   ```python
   "mode": {
       "type": "string",
       "description": "Search mode: bm25/grep (hybrid is not yet supported)",
   },
   ```
3. Replace the `description` string:
   ```python
   "mode": {
       "type": "string",
       "description": "Search mode: bm25 (only supported value)",
   },
   ```

### Method

Single string-literal edit inside a dict — no schema structure change
(`"type": "string"` stays; the property remains optional since `required`
for `search_docs` only lists `["query"]`).

### Details

- Do not add an `"enum": ["bm25"]` constraint to the JSON schema unless
  explicitly requested — the source plan's Scope only calls for updating
  the description text; the actual enforcement lives in the pydantic model
  (companion `models.py` doc), keeping the JSON schema as advisory metadata
  consistent with this file's existing style (no other property in this
  file uses `"enum"`).

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Hybrid/grep wording removed | `grep -n "grep\|hybrid" scripts/mcp_servers/mdq/tools.py` | 0 matches referencing `search_docs`'s `mode` description (confirm no other unrelated `grep_docs` tool-name false positive is miscounted) |
| Lint | `uv run ruff check scripts/mcp_servers/mdq/tools.py` | 0 errors |
| Type check | `uv run mypy scripts/mcp_servers/mdq/tools.py` | no new errors |
| Doc consistency | `uv run check-mcp-docs` | passes |
