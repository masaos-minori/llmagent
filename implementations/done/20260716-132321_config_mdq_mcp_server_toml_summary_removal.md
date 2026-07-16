# Implementation: config/mdq_mcp_server.toml (remove `summary_cache_enabled`/`summary_threshold`/`summary_model`)

Source plan: `plans/20260716-131559_plan.md`

Note: distinct from `implementations/20260716-131850_config_mdq_mcp_server_toml.md`
(plan 04, removes `use_embedding`/`embedding_dims`/`vector_table`/
`embedding_model`/`max_search_results`). Both touch this same config file at
different, adjacent blocks — apply both.

## Goal

Remove `summary_cache_enabled`, `summary_threshold`, `summary_model` from
`config/mdq_mcp_server.toml`, and add a removal note matching the existing
`audit_log_path`/`concurrency_limit` note style.

## Scope

**In:**
- Delete the "Summary cache for large chunks" block
  (`config/mdq_mcp_server.toml:68-71`): the comment and all three keys
  (`summary_cache_enabled`, `summary_threshold`, `summary_model`).
- Add a new `# NOTE:` block documenting this removal, matching the style of
  the existing `audit_log_path`/`concurrency_limit` notes.

**Out:**
- `use_embedding`/`embedding_dims`/`vector_table`/`embedding_model`/
  `max_search_results` — already handled by the companion plan-04 doc for
  this same file; do not duplicate.
- Every other key in the file (`max_results_limit`, `enable_refresh`,
  `enable_grep`, etc.).

## Assumptions

1. `summary_cache_enabled`, `summary_threshold`, `summary_model` become
   fully dead config once the companion `service.py` and `indexer.py` docs
   land — no code reads any of these three keys after both changes are
   applied together.
2. This file's established convention for documenting removed keys (the
   `audit_log_path`/`concurrency_limit` NOTE block) should be followed for
   this removal too — state what was removed, the date, why (feature never
   produced real summaries), and where to look for more detail.

## Implementation

### Target file

`config/mdq_mcp_server.toml`

### Procedure

1. Open `config/mdq_mcp_server.toml`.
2. Delete lines 68-71:
   ```toml
   # Summary cache for large chunks (reduces token usage by returning summaries)
   summary_cache_enabled = false
   summary_threshold = 5000
   summary_model = "default"
   ```
3. Add a new NOTE block (placed adjacently with the other removal notes in
   this file — either immediately after the existing
   `audit_log_path`/`concurrency_limit` notes, or after the companion
   plan-04 doc's embedding/hybrid notes if that change has already landed;
   adjust the date to the actual implementation date):
   ```toml
   # NOTE: summary_cache_enabled, summary_threshold, and summary_model were
   # removed ([implementation date]). The summary-cache feature never generated
   # a real summary -- _generate_and_cache_summary() always returned None for
   # the only supported summary_model value ("default"), and the indexer wrote
   # a truncated verbatim copy of the raw chunk content into chunk_summaries,
   # not an actual summary. get_chunk() now always returns raw (optionally
   # truncated) content. See docs/04_mcp_04_04_mdq.md. Re-add only alongside a
   # real LLM-based summarization implementation.
   ```

### Method

Direct deletion of three keys (plus their comment) and addition of one new
NOTE comment block — no other key's value or ordering changes.

### Details

- Do not renumber or reorder any remaining key.
- Validate TOML syntax after editing via a TOML parser, matching the
  approach used in the companion plan-04 `config/mdq_mcp_server.toml` doc.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| TOML syntax valid | `python -c "import tomllib; tomllib.load(open('config/mdq_mcp_server.toml','rb'))"` | no exception |
| Keys removed | `grep -n "summary_cache_enabled\|summary_threshold\|summary_model" config/mdq_mcp_server.toml` | 0 matches outside the new NOTE comment |
| Doc consistency | `uv run check-mcp-docs` | passes |
| Targeted tests | `uv run pytest tests/test_mdq_service.py -v` | all pass (companion `service.py` change must also land) |
