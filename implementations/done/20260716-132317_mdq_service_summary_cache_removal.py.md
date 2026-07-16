# Implementation: scripts/mcp_servers/mdq/service.py (remove summary-cache fields, `_generate_and_cache_summary()`, simplify `get_chunk()`)

Source plan: `plans/20260716-131559_plan.md`

Note: a fourth distinct change targeting `service.py`, alongside
`implementations/20260716-130659_service.py.md` (`audit_log_path`, plan
01), `implementations/20260716-131148_mdq_service.py.md`
(`fts_consistency_check`/`fts_rebuild`, plan 02), and
`implementations/20260716-131848_mdq_service_embedding_and_search_limit_removal.py.md`
(embedding/`max_search_results`, plan 04). All four touch non-overlapping
line ranges — apply all four.

## Goal

Remove `self.summary_cache_enabled`, `self.summary_threshold`,
`self.summary_model`, delete `_generate_and_cache_summary()` entirely, and
simplify `get_chunk()` to always return raw (optionally truncated) chunk
content with no summary-cache branch — since `_generate_and_cache_summary()`
has always returned `None` for the only supported `summary_model` value
(`"default"`).

## Scope

**In:**
- Delete the three field assignments (`scripts/mcp_servers/mdq/service.py:84-86`):
  `self.summary_cache_enabled`, `self.summary_threshold`,
  `self.summary_model`.
- Delete `_generate_and_cache_summary()` in full (current lines 152-173).
- Simplify `get_chunk()` (current lines 175-230) to remove the summary-cache
  -check block (lines 192-218: the `if req.use_summary and
  self.summary_cache_enabled and ...` branch, including the cache-hit
  return and the cache-miss background-task trigger via
  `_asyncio.create_task(...)`), per the exact target shape given in the
  source plan's Design section.

**Out:**
- `self.max_chars_per_chunk` and the truncation logic in `get_chunk()`
  (lines 177-181, 220-229) — unchanged, this is the only limit-enforcement
  logic that remains.
- Any other method (`search_docs`, `outline`, `index_paths`,
  `refresh_index`, `stats`, `grep_docs`).

## Assumptions

1. `_generate_and_cache_summary()` returns `None` whenever
   `self.summary_model == "default"` (the only value ever set in
   production — no caller changes it), and its only non-stub branch is
   dead commented-out code (`# Future: replace with actual LLM call`) —
   confirmed by direct read of `service.py:152-173`. Removing it loses no
   working functionality.
2. This change must land in the same commit as the companion `models.py`
   doc (removes `GetChunkRequest.use_summary`) — `get_chunk()`'s simplified
   body no longer references `req.use_summary` at all, so removing the
   field from the model in the same change avoids a temporarily-unused
   field.
3. This change must land in the same commit as the companion `db_schema.py`
   doc (removes `chunk_summaries` table creation) and `indexer.py` doc
   (removes `_generate_summaries()`) — after all four land together, no
   code anywhere reads or writes `chunk_summaries`.

## Implementation

### Target file

`scripts/mcp_servers/mdq/service.py`

### Procedure

1. Open `scripts/mcp_servers/mdq/service.py`.
2. Delete lines 84-86:
   ```python
   self.summary_cache_enabled: bool = mdq_cfg.get("summary_cache_enabled", False)
   self.summary_threshold: int = mdq_cfg.get("summary_threshold", 5000)
   self.summary_model: str = mdq_cfg.get("summary_model", "default")
   ```
   (and the preceding `# Summary cache for large chunks` comment, if
   present immediately above these lines).
3. Delete `_generate_and_cache_summary()` in full (current lines 152-173):
   ```python
   async def _generate_and_cache_summary(
       self, chunk_id: str, content: str, content_hash: str
   ) -> str | None:
       """Generate a summary for chunk_id and cache it in chunk_summaries.

       Returns the generated summary on success, or None on failure/stub.
       When summary_model == "default", no LLM integration is available — returns None.
       """
       try:
           if self.summary_model == "default":
               return None
           # Future: replace with actual LLM call
           # summary = await self._call_llm_for_summary(content)
           # conn = self._get_db_connection()
           # try:
           #     conn.execute("INSERT OR REPLACE INTO chunk_summaries ...", ...)
           #     conn.commit()
           # finally:
           #     conn.close()
           return None
       except Exception:
           return None
   ```
4. Replace `get_chunk()` (current lines 175-230) with the exact target
   shape from the source plan's Design section:
   ```python
   async def get_chunk(self, req: GetChunkRequest) -> str:
       """Retrieve a Markdown chunk by its ID."""
       request_limit = req.max_chars_per_chunk
       config_cap = self.max_chars_per_chunk
       max_chars = (
           min(request_limit, config_cap) if request_limit is not None else config_cap
       )
       conn = self._get_db_connection()
       try:
           row = conn.execute(
               "SELECT heading, content, content_hash FROM chunks WHERE chunk_id = ?",
               (req.chunk_id,),
           ).fetchone()
           if row is None:
               raise MdqNotFoundError(f"Chunk {req.chunk_id} not found")
           content = row["content"]
           truncated = False
           if len(content) > max_chars:
               content = content[:max_chars]
               truncated = True
           result = f"## {row['heading']}\n\n{content}"
           if truncated:
               result += (
                   f"\n\n[Truncated — {len(row['content'])}/{max_chars} chars. "
                   f"Use a narrower chunk_id or reduce max_chars_per_chunk.]"
               )
           return result
       finally:
           conn.close()
   ```

### Method

Delete two field-assignment lines, delete one full method, and replace
another method's body with an already-specified simplified version (copied
verbatim from the source plan's Design section) — no new logic invented
here.

### Details

- `content_hash` is still selected in the SQL query (`SELECT heading,
  content, content_hash FROM chunks ...`) even though it is no longer used
  after this simplification — keep it in the `SELECT` exactly as the source
  plan's Design snippet specifies (do not further "optimize" the query;
  match the given target shape exactly for a minimal, reviewable diff).
- Remove the now-unused `import asyncio as _asyncio` local import if it
  was only used inside the deleted cache-miss branch — check
  `grep -n "_asyncio" scripts/mcp_servers/mdq/service.py` after the edit;
  the module-level `import asyncio` (used elsewhere, e.g.
  `self._index_lock: asyncio.Lock | None`) must remain.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Fields removed | `grep -n "summary_cache_enabled\|summary_threshold\|summary_model" scripts/mcp_servers/mdq/service.py` | 0 matches |
| Method removed | `grep -n "_generate_and_cache_summary" scripts/mcp_servers/mdq/service.py` | 0 matches |
| `get_chunk()` simplified | `grep -n -A30 "async def get_chunk" scripts/mcp_servers/mdq/service.py` | matches the Design snippet, no `use_summary`/cache references |
| Lint | `uv run ruff check scripts/mcp_servers/mdq/service.py` | 0 errors |
| Type check | `uv run mypy scripts/mcp_servers/mdq/service.py` | no new errors |
| Targeted tests | `uv run pytest tests/test_mdq_get_chunk_behavior.py -v` (once companion new-test doc lands) | all pass |
| Full MDQ suite | `uv run pytest tests/test_mdq_*.py -v` | all pass, `test_mdq_summary_cache.py` no longer collected (companion deletion doc) |
