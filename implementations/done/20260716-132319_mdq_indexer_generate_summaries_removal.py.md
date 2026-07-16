# Implementation: scripts/mcp_servers/mdq/indexer.py (remove `_generate_summaries()` and its call site)

Source plan: `plans/20260716-131559_plan.md`

## Goal

Remove the `if service.summary_cache_enabled: _generate_summaries(...)`
call in `_index_single_file()` and the `_generate_summaries()` function
itself — it never generated a real summary, only inserted a truncated
verbatim copy of the raw chunk content into `chunk_summaries.summary`.

## Scope

**In:**
- Delete the call-site block (`scripts/mcp_servers/mdq/indexer.py:126-128`):
  ```python
  # Generate summaries for large chunks if enabled
  if service.summary_cache_enabled:
      _generate_summaries(service, conn, doc_id, sections, path)
  ```
- Delete `_generate_summaries()` in full (current lines 315-341).

**Out:**
- The surrounding chunk-insertion logic in `_index_single_file()`
  (the `INSERT INTO chunks (...)` statement immediately above the deleted
  block, and `conn.execute("COMMIT")` immediately below it) — unchanged.
- Any other function in `indexer.py` (`index_paths`, `refresh_paths`,
  `_index_directory`, `generate_chunk_id`, etc.).

## Assumptions

1. `_generate_summaries()`'s only caller is the `if
   service.summary_cache_enabled:` block being removed in the same file —
   confirmed via `rg -n "_generate_summaries" scripts/` showing only the
   definition (line 315) and the one call site (line 128).
2. `_generate_summaries()` inserts
   `section["content"][:service.summary_threshold]` (a truncated verbatim
   copy of the raw chunk, not an actual summary) into
   `chunk_summaries.summary` — confirmed by direct read of
   `indexer.py:315-341`. This is exactly the requirement's "Problem"
   statement: the feature never produced real summarized text, so removing
   it loses no working functionality.
3. This change must land in the same commit as the companion `service.py`
   doc (removes `self.summary_cache_enabled`/`self.summary_threshold`) —
   otherwise this file's deleted block would have referenced attributes
   that no longer exist, or (if this file is edited first) the deleted
   call site simply stops calling into a still-existing but now-orphaned
   function until `service.py`'s companion change also lands.

## Implementation

### Target file

`scripts/mcp_servers/mdq/indexer.py`

### Procedure

1. Open `scripts/mcp_servers/mdq/indexer.py`.
2. In `_index_single_file()`, locate lines 126-128:
   ```python
   # Generate summaries for large chunks if enabled
   if service.summary_cache_enabled:
       _generate_summaries(service, conn, doc_id, sections, path)
   ```
   Delete these three lines in full, leaving `conn.execute("COMMIT")`
   (currently line 130) as the next statement after the chunk-insertion
   loop.
3. Delete `_generate_summaries()` in full (current lines 315-341):
   ```python
   def _generate_summaries(
       service: MdqService,
       conn: sqlite3.Connection,
       doc_id: str,
       sections: list[ParsedSection],
       path: Path,
   ) -> None:
       """Generate summaries for large chunks if enabled."""
       normalized_path = path.resolve().as_posix()
       for section in sections:
           content_hash = hashlib.sha256(section["content"].encode()).hexdigest()
           if len(section["content"]) > service.summary_threshold:
               chunk_id = generate_chunk_id(
                   normalized_path,
                   section.get("heading_path", ""),
                   section.get("ordinal", 0),
                   content_hash,
               )
               conn.execute(
                   "INSERT OR REPLACE INTO chunk_summaries (chunk_id, summary, summary_model, content_hash, created_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
                   (
                       chunk_id,
                       section["content"][: service.summary_threshold],
                       service.summary_model,
                       content_hash,
                   ),
               )
   ```

### Method

Delete a 3-line call-site block and a 27-line function — no replacement
logic.

### Details

- Check whether `MdqService` (imported under `TYPE_CHECKING` per this
  file's existing import block) or `hashlib` have any other use in this
  file after the deletion (`grep -n "hashlib\." scripts/mcp_servers/mdq/indexer.py`)
  — `hashlib` is also used elsewhere in `_index_single_file()`
  (`content_hash = hashlib.sha256(...)` for the chunk itself, a separate
  computation from the one inside the deleted `_generate_summaries()`), so
  the `import hashlib` line must remain.
- Do not remove `generate_chunk_id` — it is a public function used
  elsewhere in this module (e.g. by `_index_single_file()` itself for
  chunk ID generation), not exclusive to the deleted
  `_generate_summaries()`.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Call site removed | `grep -n "summary_cache_enabled" scripts/mcp_servers/mdq/indexer.py` | 0 matches |
| Function removed | `grep -n "_generate_summaries" scripts/mcp_servers/mdq/indexer.py` | 0 matches |
| `hashlib` import still needed | `grep -n "hashlib" scripts/mcp_servers/mdq/indexer.py` | at least 1 remaining use (chunk content hash) plus the import line |
| Lint | `uv run ruff check scripts/mcp_servers/mdq/indexer.py` | 0 errors |
| Type check | `uv run mypy scripts/mcp_servers/mdq/indexer.py` | no new errors |
| Dead code | `uv run vulture scripts/mcp_servers/mdq/indexer.py --min-confidence 80` | no new dead code |
| Targeted tests | `uv run pytest tests/test_mdq_service.py -k index -v` | all pass |
| Full MDQ suite | `uv run pytest tests/test_mdq_*.py -v` | all pass, `test_mdq_summary_cache.py` no longer collected (companion deletion doc) |
