# Implementation: config/mdq_mcp_server.toml (remove embedding/hybrid keys and duplicate `max_search_results`)

Source plan: `plans/20260716-131500_plan.md`

## Goal

Remove `use_embedding`, `embedding_dims`, `vector_table`, `embedding_model`,
and `max_search_results` from `config/mdq_mcp_server.toml`, keeping
`max_results_limit` as the sole canonical result-count key, and add a
removal note matching the existing `audit_log_path`/`concurrency_limit`
note style.

## Scope

**In:**
- Delete `max_search_results = 100` (line 18) and its preceding comment
  (`# Maximum number of results to return from search`, line 17).
- Delete the "Embedding/hybrid search mode" block (lines 73-77):
  the comment and all four keys (`use_embedding`, `embedding_dims`,
  `vector_table`, `embedding_model`).
- Add a new `# NOTE:` block (matching the style of the existing
  `audit_log_path`/`concurrency_limit` notes at lines 56-66) documenting
  this removal, its date, and the rationale.

**Out:**
- `max_results_limit = 100` (line 33) and its surrounding "Result size
  limits" comment block (lines 29-39) — this is the canonical key that
  remains; do not touch it.
- `summary_cache_enabled`/`summary_threshold`/`summary_model` (lines 68-71)
  — owned by a separate requirement (`requires/20260716_05_require.md`),
  out of scope.
- `enable_refresh`/`enable_grep` (lines 50-54) — owned by a separate
  requirement (`requires/20260716_06_require.md`), out of scope.
- The existing `audit_log_path`/`concurrency_limit` NOTE block
  (lines 56-66) — already correct, do not edit its text (only append a new
  note after it, or in a stylistically consistent adjacent position).

## Assumptions

1. `max_search_results` has zero readers in code (confirmed in the
   companion `service.py` doc's Assumption 1) — removing it from config is
   safe once the corresponding `self.max_search_results` field is also
   removed from `service.py` in the same change set.
2. `use_embedding`/`embedding_dims`/`vector_table`/`embedding_model` become
   fully dead config once the companion `service.py`, `db_schema.py`, and
   `search.py` docs land — no code reads any of these four keys after all
   companion changes are applied together.
3. This file already has an established convention for documenting removed
   keys (the `audit_log_path`/`concurrency_limit` NOTE block at lines
   56-66) — the new note should follow the same format: state what was
   removed, the date, why (no code reader), and where to look for more
   detail (a docs file).

## Implementation

### Target file

`config/mdq_mcp_server.toml`

### Procedure

1. Open `config/mdq_mcp_server.toml`.
2. Delete lines 17-18:
   ```toml
   # Maximum number of results to return from search
   max_search_results = 100
   ```
3. Delete lines 73-77:
   ```toml
   # Embedding/hybrid search mode (disabled by default — FTS5-only is production baseline)
   use_embedding = false
   embedding_dims = 384
   vector_table = "chunks_vec"
   embedding_model = "default"
   ```
4. Immediately after the existing `concurrency_limit` NOTE block (current
   lines 62-66), add a new NOTE block (adjust the date to the actual
   implementation date):
   ```toml
   # NOTE: max_search_results was removed ([implementation date]). It was parsed
   # but never read anywhere in scripts/mcp_servers/mdq/ -- max_results_limit is
   # the sole enforced result-count key (see docs/04_mcp_04_04_mdq.md). Re-add
   # only alongside an implementation that actually reads this key.

   # NOTE: use_embedding, embedding_dims, vector_table, and embedding_model were
   # removed ([implementation date]). Hybrid/semantic search was never
   # functionally implemented -- _search_vector() in search.py always returned
   # an empty list. FTS5 (BM25) is the only supported search mode; use the RAG
   # pipeline (rag-pipeline-mcp) for semantic search. See
   # docs/04_mcp_04_04_mdq.md and docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md.
   # Re-add only alongside a real embedding-search implementation.
   ```

### Method

Direct deletion of five keys (plus their comments) and addition of two new
NOTE comment blocks — no other key's value or ordering changes.

### Details

- Do not renumber or reorder any remaining key — only the specified lines
  are removed/added.
- Validate TOML syntax after editing (a config file, not source code) via
  a TOML parser, same as the companion `config/agent.toml` doc's approach
  for the sibling plan.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| TOML syntax valid | `python -c "import tomllib; tomllib.load(open('config/mdq_mcp_server.toml','rb'))"` | no exception |
| Keys removed | `grep -n "max_search_results\|use_embedding\|embedding_dims\|vector_table\|embedding_model" config/mdq_mcp_server.toml` | 0 matches outside the new NOTE comments |
| `max_results_limit` intact | `grep -n "max_results_limit = 100" config/mdq_mcp_server.toml` | 1 match, unchanged |
| Doc consistency | `uv run check-mcp-docs` | passes |
| Targeted tests | `uv run pytest tests/test_mdq_service.py -v` | all pass (companion `service.py` change must also land) |
