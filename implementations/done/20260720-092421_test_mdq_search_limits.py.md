# Implementation: tests/test_mdq_search_limits.py (new — effective SQL limit coverage)

Source plan: `plans/20260719-210826_plan.md` ("Fix MDQ freshness detection and search result
correctness"), Implementation step 2, requirement's target test file list. No existing
implementation document references this filename — new file.

## Goal

Cover the companion `search.py` document's (`implementations/20260720-092134_search.py.md`)
`effective_limit = min(request limit, service.max_results_limit)` change: default limit
honored, an explicit request `limit` below the config cap is honored, and a request `limit`
above the config cap is bounded at the SQL layer itself (not merely truncated after an unbounded
fetch).

## Scope

**In scope:**
- `test_default_limit_from_config`: no explicit `limit` in the request — default `limit=10`
  (from `SearchDocsRequest.limit`'s own default) applies, bounded by
  `service.max_results_limit` if the config cap is lower.
- `test_explicit_limit_below_cap_is_honored`: request `limit` smaller than
  `service.max_results_limit` — the smaller value is what actually reaches the SQL `LIMIT`.
- `test_explicit_limit_above_cap_is_bounded_at_sql_layer`: request `limit` far above
  `service.max_results_limit` (e.g. `limit=10000` against `service.max_results_limit=2`, with
  more than 2 matching documents indexed) — assert the number of rows fetched from the database
  itself never exceeds `service.max_results_limit`, not just that the final rendered text is
  truncated. This is the specific regression the plan calls out: today, `_search_docs_structured
  ()` uses the *unbounded* `limit` directly in SQL, so a large `req.limit` bypasses the config
  cap at the SQL layer entirely, even though `search_docs()`'s post-fetch truncation eventually
  hides the extra rows from the rendered text.

**Out of scope:**
- Matched-vs-shown count wording — covered by `tests/test_mdq_search_counts.py` (separate file).
- `max_results_limit` request-field behavior as a secondary post-fetch display cap — already
  covered by existing `tests/test_mdq_search_modes.py::TestResultLimitBehavior` (which this
  plan's companion document updates for new wording, not new limit-precedence behavior); this
  file focuses specifically on the SQL-layer `effective_limit` computation, which is new.
- Search mode restriction (`bm25`-only) — already covered by
  `tests/test_mdq_search_modes.py::TestSearchModeRestriction`, unaffected by this plan.

## Assumptions

1. Reuses the `service` fixture pattern from `tests/test_mdq_search_modes.py`:
   ```python
   @pytest.fixture
   def service(tmp_path: Path) -> MdqService:
       fd, db = mkstemp(suffix=".db", dir=str(tmp_path))
       try:
           svc = MdqService(db_path=db)
           svc._allowed_dirs = [str(tmp_path)]
           return svc
       finally:
           os.close(fd)
   ```
2. To observe the SQL-layer fetch count directly (not just the rendered text), the test calls
   `_search_docs_structured(service, req)` directly (the module-level function in `search.py`,
   already imported/tested at that granularity by `tests/test_mdq_service.py::TestSearchDocs` —
   confirm the existing test file's import shape via `grep -n "_search_docs_structured"
   tests/test_mdq_service.py` before writing, to match whatever access pattern is already
   established) rather than only asserting against `search_docs()`'s formatted string output —
   the structured result's `shown_count`/`results` length is the most direct signal that the SQL
   fetch itself was bounded, independent of any later Python-side truncation.
3. `service.max_results_limit` is a plain mutable `int` attribute (already used this way by
   `tests/test_mdq_search_modes.py::test_request_override_above_cap_is_bounded`, which does
   `service.max_results_limit = 2` directly) — tests here follow the same direct-assignment
   pattern to set up a low config cap.

## Implementation

### Target file

`tests/test_mdq_search_limits.py`

### Procedure

1. **Default limit test:**
   ```
   def test_default_limit_from_config(service, tmp_path):
       # index 3 docs, no explicit `limit` in SearchDocsRequest
       # assert shown_count/len(results) == 3 (all fit under default limit=10 and config cap)
   ```
2. **Explicit limit below cap:**
   ```
   def test_explicit_limit_below_cap_is_honored(service, tmp_path):
       # index 5 docs, SearchDocsRequest(query=..., limit=3)
       # assert exactly 3 rows returned by _search_docs_structured (SQL-layer bounded)
   ```
3. **Explicit limit above cap is bounded at SQL layer:**
   ```
   def test_explicit_limit_above_cap_is_bounded_at_sql_layer(service, tmp_path):
       # index 5 docs
       service.max_results_limit = 2
       # SearchDocsRequest(query=..., limit=10000)
       # call _search_docs_structured directly
       # assert len(result["results"]) == 2  (NOT 5 — proves the SQL LIMIT itself used
       #   effective_limit = min(10000, 2) == 2, not the unbounded req.limit)
   ```
   This is the key regression assertion: under the pre-fix code, `_search_docs_structured()`
   would fetch all 5 matching rows from SQLite (since `limit = getattr(req, "limit", 10) or 10`
   was used unbounded), and only `search_docs()`'s later Python-side slicing would hide the
   extra 3 — meaning `_search_docs_structured()` alone, called directly, would return 5 rows
   pre-fix and must return 2 rows post-fix.

### Method

New pytest module mirroring `tests/test_mdq_search_modes.py`'s existing fixture and indexing
pattern (`index_paths`/`IndexPathsRequest`, `asyncio.run(...)`), but asserting against the
structured result (`_search_docs_structured`'s return value) directly rather than only the
formatted string, since the SQL-layer bounding claim requires inspecting the actual row count
before any Python-side truncation.

### Details

- Import shape: `from mcp_servers.mdq.search import _search_docs_structured, search_docs`;
  `from mcp_servers.mdq.mdq_models import IndexPathsRequest, SearchDocsRequest`; `from
  mcp_servers.mdq.mdq_service import MdqService`; `from mcp_servers.mdq.indexer import
  index_paths`.
- `_search_docs_structured` is a synchronous function called via `asyncio.to_thread(...)`
  inside `search_docs()` in production, but it can be called directly and synchronously in a
  test (no `asyncio.run` needed for that specific call) — confirm this by reading its signature
  in `search.py` (`def _search_docs_structured(service: MdqService, req: SearchDocsRequest) ->
  SearchResultResult:` — a plain sync function, not `async def`).
- Use distinct query keywords per test (e.g. `"Keyword"` per test's own doc set, following
  `tests/test_mdq_search_modes.py`'s existing convention) to avoid FTS5 index cross-talk between
  test cases sharing the same `tmp_path`/db.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| File created | `ls tests/test_mdq_search_limits.py` | exists |
| Lint | `uv run ruff check tests/test_mdq_search_limits.py` | 0 errors |
| Type check | `uv run mypy tests/test_mdq_search_limits.py` | no new errors |
| Targeted run | `uv run pytest tests/test_mdq_search_limits.py -v` | all pass (after companion `search.py` code change lands) |
| Regression coverage | `test_explicit_limit_above_cap_is_bounded_at_sql_layer` | fails against pre-fix `search.py` (would see 5 rows, not 2), passes after the fix |
| No cross-test interference | `uv run pytest tests/test_mdq_search_limits.py tests/test_mdq_search_modes.py -v` | all pass together |
