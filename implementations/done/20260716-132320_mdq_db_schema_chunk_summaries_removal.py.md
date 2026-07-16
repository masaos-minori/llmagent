# Implementation: scripts/mcp_servers/mdq/db_schema.py (remove `chunk_summaries` table creation)

Source plan: `plans/20260716-131559_plan.md`

Note: distinct from `implementations/20260716-131849_mdq_db_schema.py.md`
(plan 04, removes `use_embedding`/`vector_table`/`embedding_dims` params and
the `vec0` block). Both touch `create_production_tables()` in the same
file, at different, non-adjacent blocks — apply both; after both land, the
function's signature is `(conn, db_path, sqlite_busy_timeout)` and it
creates `documents`, `chunks`, `chunks_fts` (+ triggers), `index_state`
only (no `chunk_summaries`, no vector table).

## Goal

Remove the `chunk_summaries` table creation statement from
`create_production_tables()` — per the source plan's Design decision to
**drop** this table going forward (not merely leave it unread), since it
was never documented as intentional future scaffolding (unlike the vector
table) and only ever stored misleading truncated-content data mislabeled as
"summary".

## Scope

**In:**
- Delete the `CREATE TABLE IF NOT EXISTS chunk_summaries (...)` block
  (`scripts/mcp_servers/mdq/db_schema.py:125-133`).

**Out:**
- Every other table/trigger creation statement in this function
  (`documents`, `chunks`, `chunks_fts`, `chunks_ai`/`chunks_ad`/`chunks_au`
  triggers, `index_state`).
- The vector-table (`vec0`) block — already removed by the companion
  plan-04 doc for this same file; do not re-edit or reference it here as
  if it still exists.
- The old-schema migration/rebuild logic at the top of the function.
- No `DROP TABLE` statement is added for pre-existing `chunk_summaries`
  tables on live databases — per the source plan's Unknowns resolution,
  this is a non-destructive, forward-only removal (matches the `chunks_vec`
  precedent from plan 04: idempotent creation removed, no active drop).

## Assumptions

1. No code reads or writes `chunk_summaries` after the companion
   `service.py` and `indexer.py` docs for this same plan land — confirmed
   by this plan's own Assumption 3 (`ChunkSummary`/
   `GetChunkSummaryResponse` have zero importers) and the removal of the
   only read site (`service.py`'s `get_chunk()` cache-check block) and the
   only write site (`indexer.py`'s `_generate_summaries()`).
2. `CREATE TABLE IF NOT EXISTS` is idempotent — removing this statement
   does not drop any pre-existing `chunk_summaries` table on a live
   `mdq.sqlite` database; it only stops creating one on fresh/rebuilt
   databases going forward, per the source plan's Design section and
   matching the same reasoning already applied to the `chunks_vec` table
   in the companion plan-04 doc.
3. This change must land in the same commit as the companion `service.py`
   and `indexer.py` docs — otherwise those files would still reference a
   table this doc stops creating (though on an existing database the table
   would still physically exist from a prior run, so this specific
   ordering risk is low; still, land together for a clean, atomic diff).

## Implementation

### Target file

`scripts/mcp_servers/mdq/db_schema.py`

### Procedure

1. Open `scripts/mcp_servers/mdq/db_schema.py`.
2. Locate the block at current lines 125-133:
   ```python
   conn.execute("""
       CREATE TABLE IF NOT EXISTS chunk_summaries (
           chunk_id TEXT PRIMARY KEY,
           summary TEXT NOT NULL,
           summary_model TEXT NOT NULL,
           content_hash TEXT NOT NULL,
           created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
       )
   """)
   ```
3. Delete this block in full.
4. Confirm the statement immediately before it (`index_state` table
   creation) and whatever follows (per the companion plan-04 doc, this may
   now be `conn.commit()` directly, since the vector-table block is also
   removed) remain contiguous with no orphaned blank lines.

### Method

Single block deletion — no signature change in this file (the source
plan's Scope for this file is limited to the table-creation statement; the
signature change to `create_production_tables()` is fully covered by the
companion plan-04 `db_schema.py` doc, which this doc does not duplicate).

### Details

- Do not add a `DROP TABLE chunk_summaries` statement anywhere — explicitly
  out of scope per the source plan's Unknowns resolution (non-destructive
  removal only).
- If implementing this doc's change before the companion plan-04
  `db_schema.py` doc, the resulting file still has the `use_embedding`/
  `vector_table`/`embedding_dims` parameters and vec0 block at the time of
  this edit — that is fine; both docs target the same file independently
  and the end state is correct once both land, regardless of order.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Table creation removed | `grep -n "chunk_summaries" scripts/mcp_servers/mdq/db_schema.py` | 0 matches |
| Lint | `uv run ruff check scripts/mcp_servers/mdq/db_schema.py` | 0 errors |
| Type check | `uv run mypy scripts/mcp_servers/mdq/db_schema.py` | no new errors |
| Targeted tests | `uv run pytest tests/test_mdq_service.py -v` | all pass (exercises `_init_db()`/`create_production_tables()` indirectly) |
| Pre-existing DB check (manual, per source plan step 8) | restart `mdq-mcp` in dev, confirm indexing a large file no longer touches `chunk_summaries` | no new rows written; existing rows (if any) are left untouched and unreferenced |
