# Implementation: scripts/mcp_servers/mdq/service.py (remove embedding config fields and duplicate `max_search_results`)

Source plan: `plans/20260716-131500_plan.md`

Note: this is a distinct change from the two other `service.py`-targeting
docs already created (`implementations/20260716-130659_service.py.md` for
`audit_log_path`, source plan `plans/done/20260716-121714_plan.md`; and
`implementations/20260716-131148_mdq_service.py.md` for
`fts_consistency_check`/`fts_rebuild` methods, source plan
`plans/done/20260716-123031_plan.md`). All three touch non-overlapping
line ranges in the same file — apply all three.

## Goal

Remove `self.use_embedding`, `self.vector_table`, `self.embedding_model`,
`self.embedding_dims` and their now-unneeded pass-through into
`create_production_tables()`, plus the unused `self.max_search_results`
duplicate — closing the config surface for the permanently-stubbed hybrid
search and the dead result-limit alias.

## Scope

**In:**
- Delete `self.max_search_results: int = mdq_cfg.get("max_search_results", 100)`
  (`scripts/mcp_servers/mdq/service.py:60`).
- Delete the "Embedding/hybrid search mode" block (`service.py:88-92`):
  `self.use_embedding`, `self.vector_table`, `self.embedding_model`,
  `self.embedding_dims`, and its preceding comment.
- Update `_init_db()`'s call to `create_production_tables()`
  (`service.py:118-125`) to drop the three now-removed arguments
  (`self.use_embedding`, `self.vector_table`, `self.embedding_dims`),
  matching the companion `db_schema.py` doc's simplified signature.

**Out:**
- `self.max_results_limit` (`service.py`, in the "Result size limits"
  block) — this is the canonical, still-enforced result-count key; do not
  touch it.
- `self.summary_cache_enabled`/`self.summary_threshold`/`self.summary_model`
  — owned by a separate requirement (`requires/20260716_05_require.md`),
  out of scope here.
- `self.sqlite_busy_timeout` — passed to `create_production_tables()` and
  still needed; keep it in the call.
- Any method other than `_init_db()` (`_get_db_connection`, `search_docs`,
  `get_chunk`, etc.).

## Assumptions

1. `self.max_search_results` has no reader anywhere in the codebase besides
   its own assignment — verified via `rg -n "max_search_results" scripts/
   tests/`; the value actually enforced by `search.py::search_docs` is
   `service.max_results_limit` (a separate, already-correct field).
2. `self.use_embedding`, `self.vector_table`, `self.embedding_model`,
   `self.embedding_dims` are read only in: (a) this file's own `_init_db()`
   pass-through to `create_production_tables()`, and (b) `search.py`'s now
   -removed `if mode == "hybrid" and service.use_embedding:` branch
   (companion `search.py` doc) — after both changes land, no code anywhere
   reads these four attributes. `self.embedding_model` specifically has no
   reader at all today outside its own assignment (verified via
   `rg -n "embedding_model" scripts/`); confirm this remains true after the
   `search.py` edit (it does, since `search.py` never read
   `service.embedding_model` directly).
3. This change must land in the same commit as the companion `db_schema.py`
   doc (removes the corresponding parameters from
   `create_production_tables()`) and the companion `search.py` doc (removes
   the `service.use_embedding` read) — otherwise this file's `_init_db()`
   call passes fewer/different arguments than `create_production_tables()`
   expects, breaking at call time.

## Implementation

### Target file

`scripts/mcp_servers/mdq/service.py`

### Procedure

1. Open `scripts/mcp_servers/mdq/service.py`.
2. Delete line 60:
   ```python
   self.max_search_results: int = mdq_cfg.get("max_search_results", 100)
   ```
3. Delete the block at lines 87-92:
   ```python
   # Embedding/hybrid search mode
   self.use_embedding: bool = mdq_cfg.get("use_embedding", False)
   self.vector_table: str = mdq_cfg.get("vector_table", "chunks_vec")
   self.embedding_model: str = mdq_cfg.get("embedding_model", "default")
   self.embedding_dims: int = mdq_cfg.get("embedding_dims", 384)
   ```
4. In `_init_db()` (current lines 112-127), locate the
   `create_production_tables(...)` call (lines 118-125):
   ```python
   create_production_tables(
       conn,
       self.db_path,
       self.use_embedding,
       self.vector_table,
       self.embedding_dims,
       self.sqlite_busy_timeout,
   )
   ```
   Replace with (matching the companion `db_schema.py` doc's simplified
   signature — `conn`, `db_path`, `sqlite_busy_timeout` only):
   ```python
   create_production_tables(
       conn,
       self.db_path,
       self.sqlite_busy_timeout,
   )
   ```

### Method

Direct deletion of two field blocks and a call-site argument-list
simplification — no renaming, no new fields introduced.

### Details

- Do not delete `self.max_results_limit`, `self.max_chars_per_chunk`, or
  `self.max_total_result_chars` (the "Result size limits" block) — these
  are unrelated canonical fields that remain in active use.
- Confirm no blank-line/comment residue remains where the deleted blocks
  used to be (e.g. no orphaned "# Embedding/hybrid search mode" comment
  left above a now-empty spot).

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Fields removed | `grep -n "max_search_results\|use_embedding\|vector_table\|embedding_model\|embedding_dims" scripts/mcp_servers/mdq/service.py` | 0 matches |
| `_init_db()` call updated | `grep -n -A5 "create_production_tables(" scripts/mcp_servers/mdq/service.py` | 3-arg call (`conn`, `self.db_path`, `self.sqlite_busy_timeout`) |
| Lint | `uv run ruff check scripts/mcp_servers/mdq/service.py` | 0 errors |
| Type check | `uv run mypy scripts/mcp_servers/mdq/service.py` | no new errors |
| Targeted tests | `uv run pytest tests/test_mdq_service.py -v` | all pass |
| Full MDQ suite | `uv run pytest tests/test_mdq_*.py -v` | all pass, `test_mdq_hybrid_search.py` no longer collected (companion deletion doc) |
