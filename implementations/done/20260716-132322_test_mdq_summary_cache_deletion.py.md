# Implementation: tests/test_mdq_summary_cache.py (delete file)

Source plan: `plans/20260716-131559_plan.md`

## Goal

Delete `tests/test_mdq_summary_cache.py` in full — every test in it
(`TestSummaryCacheDisabledByDefault`, `TestSummaryCacheEnabled`,
`TestSummaryCacheWithLargeChunk`, `TestGenerateAndCacheSummary`) exercises
config/schema/cache behavior removed by the companion `service.py`,
`models.py`, `indexer.py`, `db_schema.py`, and
`config/mdq_mcp_server.toml` docs for this same plan.

## Scope

**In:**
- Delete `tests/test_mdq_summary_cache.py` in full (10 test functions
  across 4 classes: `test_summary_cache_disabled_by_default`,
  `test_summary_threshold_default`, `test_summary_model_default`,
  `test_summary_cache_table_created_when_enabled`,
  `test_summary_cache_not_used_when_disabled`,
  `test_cached_summary_returned_when_available`,
  `test_raw_content_returned_when_no_cached_summary`,
  `test_content_hash_invalidation_invalidates_summary`,
  `test_returns_none_for_default_model`,
  `test_returns_none_on_exception`).

**Out:**
- `tests/test_mdq_get_chunk_behavior.py` (new — companion doc) — this is an
  addition, not part of this deletion.
- Any other `tests/test_mdq_*.py` file.

## Assumptions

1. Every test in this file either constructs `MdqService` and asserts on
   `summary_cache_enabled`/`summary_threshold`/`summary_model` attributes,
   queries the `chunk_summaries` table directly, or calls
   `_generate_and_cache_summary()` — all removed by the companion docs for
   this plan. Once those land, this file would fail to even run
   (`AttributeError` on `MdqService` construction/attribute access) —
   confirming full deletion (not partial editing) is correct.
2. This deletion should land in the same commit as the companion
   `service.py`/`indexer.py`/`db_schema.py` changes for atomicity, though
   either ordering is safe (pytest simply stops collecting a deleted file).

## Implementation

### Target file

`tests/test_mdq_summary_cache.py`

### Procedure

1. Confirm the file's test classes still match the ones enumerated above
   (`rg -n "^class|def test_" tests/test_mdq_summary_cache.py`) — a sanity
   check that no unrelated test was added since the source plan was
   written.
2. Delete the file: `git rm tests/test_mdq_summary_cache.py` (or
   equivalent), not a truncation to empty.

### Method

Whole-file deletion — no test logic is preserved or migrated; the
companion `tests/test_mdq_get_chunk_behavior.py` doc covers the
*replacement* coverage (normal `get_chunk` behavior, removed-field
handling) independently, not a port of this file's assertions.

### Details

- Do not leave an empty stub file — full removal is the intent.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| File gone | `test -f tests/test_mdq_summary_cache.py && echo EXISTS || echo REMOVED` | `REMOVED` |
| Not collected | `uv run pytest --collect-only -q tests/ 2>&1 \| grep -i summary_cache` | 0 matches |
| Full MDQ suite | `uv run pytest tests/test_mdq_*.py -v` | all pass, no `AttributeError`/`ImportError` from the deleted file |
