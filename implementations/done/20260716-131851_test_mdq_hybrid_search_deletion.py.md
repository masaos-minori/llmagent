# Implementation: tests/test_mdq_hybrid_search.py (delete file)

Source plan: `plans/20260716-131500_plan.md`

## Goal

Delete `tests/test_mdq_hybrid_search.py` in full — every test in it
(`TestHybridSearchConfig`, `TestHybridSearchVectorTable`,
`TestHybridSearchMerge`) exercises config/schema/merge behavior removed by
the companion `models.py`/`search.py`/`service.py`/`db_schema.py`/
`config/mdq_mcp_server.toml` docs for this same plan.

## Scope

**In:**
- Delete `tests/test_mdq_hybrid_search.py` (219 lines, 3 test classes,
  10 test functions total: `test_use_embedding_disabled_by_default`,
  `test_vector_table_default_value`, `test_embedding_model_default_value`,
  `test_vector_table_not_created_when_disabled`,
  `test_vector_table_created_when_enabled`, `test_empty_results`,
  `test_only_fts_results`, `test_rrf_merge_scores`,
  `test_rrf_cross_list_ranking`, plus any class-level fixtures).

**Out:**
- `tests/test_mdq_search_modes.py` (new — companion doc) — this is an
  addition, not part of this deletion.
- Any other `tests/test_mdq_*.py` file.

## Assumptions

1. `test_mdq_hybrid_search.py` imports `_RRF_K`, `_merge_hybrid` from
   `mcp_servers.mdq.search` and constructs `MdqService` directly to assert
   on `use_embedding`/`vector_table`/`embedding_model` — all of which are
   removed by the companion `search.py` and `service.py` docs. Once those
   land, this file would fail to even import (`ImportError` on `_RRF_K`,
   `_merge_hybrid`), confirming there is nothing salvageable in it after
   the removal — full deletion (not partial editing) is correct.
2. This deletion must land in the same commit as (or after) the companion
   `search.py` doc — deleting this file before `_RRF_K`/`_merge_hybrid`
   are removed leaves a redundant-but-still-passing test temporarily; the
   reverse order (deleting first) is also safe since pytest simply stops
   collecting the file. Either sequencing works; recommend doing this
   deletion in the same commit as the `search.py`/`service.py`/
   `db_schema.py` changes for atomicity.

## Implementation

### Target file

`tests/test_mdq_hybrid_search.py`

### Procedure

1. Confirm the file's test classes still match the ones enumerated above
   (`rg -n "^class|def test_" tests/test_mdq_hybrid_search.py`) — a
   sanity check that no unrelated test was added to this file since the
   source plan was written.
2. Delete the file: `git rm tests/test_mdq_hybrid_search.py` (or
   equivalent), not a truncation to empty.

### Method

Whole-file deletion — no test logic is preserved or migrated; the
companion `tests/test_mdq_search_modes.py` doc covers the *replacement*
coverage (mode validation, result-limit behavior) independently, not a
port of this file's assertions.

### Details

- Do not leave an empty stub file — full removal is the intent, matching
  how `db_fts.py` was fully deleted in the companion plan-02 doc.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| File gone | `test -f tests/test_mdq_hybrid_search.py && echo EXISTS || echo REMOVED` | `REMOVED` |
| Not collected | `uv run pytest --collect-only -q tests/ 2>&1 \| grep -i hybrid` | 0 matches |
| Full MDQ suite | `uv run pytest tests/test_mdq_*.py -v` | all pass, no `ImportError` from the deleted file |
