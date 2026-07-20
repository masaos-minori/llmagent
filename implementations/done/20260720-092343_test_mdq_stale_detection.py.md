# Implementation: tests/test_mdq_stale_detection.py (new — unit + behavior coverage for shared
stale-detection helper)

Source plan: `plans/20260719-210826_plan.md` ("Fix MDQ freshness detection and search result
correctness"), Implementation step 1, requirement's target test file list. No existing
implementation document references this filename — new file.

## Goal

Cover the new `is_stale()`/`STALE_SQL_CONDITION` shared definitions (companion `mdq_models.py`
document, `implementations/20260720-091958_mdq_models.py.md`) at the unit level (boundary
values), and cover `MdqService.outline()`'s fixed behavior (companion `mdq_service.py` document,
`implementations/20260720-092036_mdq_service.py.md`) at the integration level — specifically that
a freshly indexed file no longer produces a spurious stale warning, and that a genuinely modified
file still does.

## Scope

**In scope:**
- Unit tests for `is_stale(mtime_ns: int, indexed_at: float) -> bool` directly.
- A test asserting `is_stale()`'s Python formula and `STALE_SQL_CONDITION`'s SQL formula agree at
  the exact boundary (`mtime_ns == int(indexed_at * 1e9)` → not stale;
  `mtime_ns == int(indexed_at * 1e9) + 1` → stale) — per plan UNK-01's resolution, this pairing
  is the whole point of having both a Python predicate and a SQL fragment: they must never
  diverge.
- Integration test(s) via `MdqService.outline()`: index a file, call `outline()` immediately,
  assert the "modified since last indexing" warning text is absent (regression test for the bug
  this plan fixes — before the fix, this case would incorrectly show the warning).
- A companion case with an artificially stale document row (mtime_ns set later than
  indexed_at in nanosecond terms) asserting the warning IS present — proves the fix does not
  simply always suppress the warning.

**Out of scope:**
- `MdqService.stats()`'s stale count — already covered by
  `tests/test_mdq_service.py::TestMdqService::test_stats_includes_stale_count` (existing,
  unchanged assertion `"Stale: 0,"` since `stats()`'s SQL text does not change, only its origin).
- `health_check._check_stale_documents()` — already covered by
  `tests/test_mdq_health_stale.py` (existing; unchanged since its SQL text does not change
  either).
- Any search-limit or count-wording behavior — covered by `tests/test_mdq_search_limits.py` and
  `tests/test_mdq_search_counts.py` (separate new files, separate documents).

## Assumptions

1. `is_stale`/`STALE_SQL_CONDITION` are importable from `mcp_servers.mdq.mdq_models` after the
   companion `mdq_models.py` document's changes land (`from mcp_servers.mdq.mdq_models import
   is_stale, STALE_SQL_CONDITION`).
2. Following the existing fixture convention in `tests/test_mdq_search_modes.py`
   (`service` fixture: `MdqService(db_path=db)` with `svc._allowed_dirs = [str(tmp_path)]`) and
   `tests/test_mdq_service.py` (uses `index_paths`/`IndexPathsRequest` plus `asyncio.run(...)` to
   drive async `MdqService` methods), integration tests reuse the same pattern: a temp SQLite DB
   via `mkstemp`, a temp dir added to `allowed_dirs`, real `.md` files written and indexed via
   `index_paths()`, then `asyncio.run(service.outline(OutlineRequest(path=...)))`.
3. To construct a "genuinely stale" row for the second integration case, the test needs to
   directly manipulate the `documents` table's `mtime_ns`/`indexed_at` values after indexing
   (e.g. `UPDATE documents SET mtime_ns = ? WHERE source_path = ?` via a raw connection) rather
   than relying on real filesystem `mtime` changes (flaky/timing-dependent) — this mirrors how
   `tests/test_mdq_health_stale.py` already builds its own test DB with hand-crafted `mtime_ns`
   values rather than depending on real file timestamps.

## Implementation

### Target file

`tests/test_mdq_stale_detection.py`

### Procedure

1. **Unit tests for `is_stale()`** (no DB, no service, pure function):
   - `test_not_stale_at_exact_boundary`: `is_stale(mtime_ns=int(1000.0 * 1e9), indexed_at=1000.0)
     is False` (equal → not stale, matches `>` not `>=` semantics).
   - `test_stale_one_nanosecond_past_boundary`: `is_stale(mtime_ns=int(1000.0 * 1e9) + 1,
     indexed_at=1000.0) is True`.
   - `test_not_stale_when_mtime_much_older`: `is_stale(mtime_ns=int(500.0 * 1e9),
     indexed_at=1000.0) is False` — the case that demonstrates the bug this plan fixes: under
     the old buggy direct comparison (`mtime_ns > indexed_at`, i.e. `500_000_000_000 > 1000.0`),
     this would have incorrectly evaluated `True`; `is_stale()` correctly evaluates `False`.
   - `test_sql_condition_agrees_with_python_predicate`: build an in-memory SQLite table with one
     row at each of the three boundary value-pairs above, run
     `f"SELECT mtime_ns, indexed_at, ({STALE_SQL_CONDITION}) as is_stale_sql FROM t"`, and assert
     `bool(row["is_stale_sql"]) == is_stale(row["mtime_ns"], row["indexed_at"])` for every row —
     this is the test the plan's UNK-01 explicitly calls for.
2. **Integration tests via `MdqService.outline()`** (following the `service`/`tmp_path` fixture
   pattern from `tests/test_mdq_search_modes.py` and `tests/test_mdq_service.py`):
   - `test_outline_no_stale_warning_immediately_after_indexing`: write one `.md` file, index it,
     call `outline()`, assert `"modified since last indexing"` is NOT in the result — this is the
     direct regression test for the reported bug (previously, every freshly indexed file would
     spuriously show this warning).
   - `test_outline_shows_stale_warning_when_mtime_is_newer`: index a file, then directly `UPDATE
     documents SET mtime_ns = ? WHERE source_path = ?` to a value greater than
     `int(indexed_at * 1e9)`, call `outline()` again, assert `"modified since last indexing"` IS
     in the result — proves the fix still detects genuine staleness, not just "always false."

### Method

New pytest module, two `class Test...` groupings (pure-function unit tests; `MdqService`
integration tests), following this test suite's existing style (plain `assert` statements,
`asyncio.run(...)` for async service methods, `pytest.fixture` for shared setup). No mocking of
`is_stale()`/`STALE_SQL_CONDITION` themselves — both are simple enough to test directly against
real SQLite where relevant.

### Details

- Import shape: `from mcp_servers.mdq.mdq_models import is_stale, STALE_SQL_CONDITION,
  IndexPathsRequest, OutlineRequest`; `from mcp_servers.mdq.indexer import index_paths`; `from
  mcp_servers.mdq.mdq_service import MdqService`.
- For the raw `UPDATE documents SET mtime_ns = ...` step, use
  `service._get_db_connection()` (the same private accessor `MdqService`'s own methods use
  internally, confirmed present in `mdq_service.py`'s `outline()`/`grep_docs()`) rather than
  opening a fresh, separate `sqlite3.connect(...)` — keeps the test consistent with the
  production code path's connection handling and avoids WAL-mode visibility surprises between
  two independently opened connections to the same file.
- Keep the SQL-agreement test (`test_sql_condition_agrees_with_python_predicate`) using a
  minimal, throwaway in-memory table (`sqlite3.connect(":memory:")`, `CREATE TABLE t (mtime_ns
  INTEGER, indexed_at REAL)`), not the full `documents`/`chunks`/`chunks_fts` schema — no need
  for the full production schema to test a pure boolean-expression equivalence.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| File created | `ls tests/test_mdq_stale_detection.py` | exists |
| Lint | `uv run ruff check tests/test_mdq_stale_detection.py` | 0 errors |
| Type check | `uv run mypy tests/test_mdq_stale_detection.py` | no new errors |
| Targeted run | `uv run pytest tests/test_mdq_stale_detection.py -v` | all pass (after companion `mdq_models.py`/`mdq_service.py` code changes land) |
| Regression coverage | `test_outline_no_stale_warning_immediately_after_indexing` specifically | fails against the pre-fix `outline()` code, passes after the fix — confirms this test would have caught the original bug |
| Full MDQ suite | `uv run pytest tests/test_mdq_service.py tests/test_mdq_health_stale.py tests/test_mdq_stale_detection.py -v` | all pass, no regressions |
