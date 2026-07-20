# Implementation: tests/test_mdq_search_counts.py (new — matched vs. shown count wording
coverage)

Source plan: `plans/20260719-210826_plan.md` ("Fix MDQ freshness detection and search result
correctness"), Implementation step 3, requirement's target test file list. No existing
implementation document references this filename — new file.

## Goal

Cover the companion `search.py`/`mdq_models.py` documents' new `matched_count`/`shown_count`
split (replacing the old `total: int` field that mislabeled the post-`LIMIT` row count as an
exact total): assert the structured result reports an exact matched count independent of any
limit, assert the shown count reflects what was actually returned, and assert
`search_docs()`'s rendered header text never claims an exact "found" total when rows were
actually dropped by a limit.

## Scope

**In scope:**
- `test_matched_count_is_exact_regardless_of_limit`: index N documents matching a query, request
  a `limit` smaller than N, assert `_search_docs_structured()`'s `matched_count == N` (the exact
  count, unaffected by the `LIMIT` clause) while `shown_count == limit` (the bounded count).
- `test_header_wording_when_nothing_truncated`: index N documents, request a `limit` ≥ N (or
  rely on the config default), assert the rendered `search_docs()` text uses the simple
  "N found"-style phrasing (matched_count == shown_count, nothing hidden).
- `test_header_wording_when_results_truncated`: index N documents, request/configure a lower
  effective limit, assert the rendered text distinguishes "matched" from "shown" (does not
  render a single number that could be misread as an exact total) and does not silently repeat
  the old `"{original_total} found"` framing when `matched_count != shown_count`.
- `test_truncation_message_consistency`: assert the truncation trailer text (the
  `[Truncated — ...]` block) uses the same `matched_count`/`shown_count` numbers as the header,
  i.e. no cross-referencing inconsistency between the header's claimed counts and the trailer's.

**Out of scope:**
- SQL-layer limit bounding itself — covered by `tests/test_mdq_search_limits.py` (separate file);
  this file assumes the limit mechanism works and focuses purely on count/wording correctness.
- `tests/test_mdq_search_modes.py`'s three existing `TestResultLimitBehavior` tests — updated in
  place by the companion `tests/test_mdq_search_modes.py` document (their existing
  `"3 found"`/`"5 found"` assertions get new wording), not duplicated here.

## Assumptions

1. `SearchResultResult` (per companion `mdq_models.py` document) exposes `matched_count: int`
   and `shown_count: int` instead of `total: int` — tests here access these fields directly by
   calling `_search_docs_structured(service, req)` and indexing into the returned `TypedDict`
   (`result["matched_count"]`, `result["shown_count"]`), matching the existing access pattern
   implied by `search.py`'s own internal use of `result["total"]` pre-change.
2. Per the companion `search.py` document's Implementation step 4, the exact rendered wording is
   an implementation-time detail; these tests assert on the *distinguishing property*
   (matched-count and shown-count both appear, and are not conflated into a single misleading
   number) rather than pinning an exact string like `"{matched_count} matched, {shown_count}
   shown"` — using a looser assertion (e.g. `str(matched_count) in result and str(shown_count) in
   result` when they differ, or a regex) so the test does not become over-fitted to one specific
   phrasing choice made at implementation time.
3. Reuses the `service`/`tmp_path` fixture and indexing pattern already established by
   `tests/test_mdq_search_modes.py` and `tests/test_mdq_search_limits.py` (companion document).

## Implementation

### Target file

`tests/test_mdq_search_counts.py`

### Procedure

1. **Exact matched count independent of limit:**
   ```
   def test_matched_count_is_exact_regardless_of_limit(service, tmp_path):
       # index 5 docs matching "Keyword"
       result = _search_docs_structured(service, SearchDocsRequest(query="Keyword", limit=2))
       assert result["matched_count"] == 5
       assert result["shown_count"] == 2
   ```
2. **Header wording — nothing hidden:**
   ```
   def test_header_wording_when_nothing_truncated(service, tmp_path):
       # index 3 docs, no limiting configured/requested (all 3 fit)
       text = asyncio.run(search_docs(service, SearchDocsRequest(query="Keyword")))
       assert "3" in text  # matched_count == shown_count == 3, simple phrasing acceptable
       assert "Truncated" not in text
   ```
3. **Header wording — results truncated:**
   ```
   def test_header_wording_when_results_truncated(service, tmp_path):
       # index 5 docs, request limit=2 (or set service.max_results_limit=2)
       text = asyncio.run(search_docs(service, SearchDocsRequest(query="Keyword", limit=2)))
       # both the matched count (5) and shown count (2) must be discoverable in the text —
       # the header must not present a single ambiguous "N found" where N is actually the
       # limited/shown count, not the true match count
       assert "5" in text
       assert "2" in text
   ```
4. **Truncation message consistency:**
   ```
   def test_truncation_message_consistency(service, tmp_path):
       # index 5 docs, force truncation via a low limit
       text = asyncio.run(search_docs(service, SearchDocsRequest(query="Keyword", limit=2)))
       # whatever numbers appear in the header must match whatever numbers appear in the
       # [Truncated — ...] trailer — extract both and assert equality rather than pinning
       # one hardcoded string
   ```

### Method

New pytest module, one test class (or flat functions matching this suite's mixed style — both
patterns exist across `tests/test_mdq_*.py`), asserting on both the structured result
(`_search_docs_structured`) for exactness and the rendered string (`search_docs`) for honest
user-facing wording. Assertions favor substring/regex checks over exact string equality where the
plan leaves wording as an implementation-time choice (per Assumption 2), to avoid brittleness.

### Details

- Import shape: `from mcp_servers.mdq.search import _search_docs_structured, search_docs`;
  `from mcp_servers.mdq.mdq_models import IndexPathsRequest, SearchDocsRequest`; `from
  mcp_servers.mdq.mdq_service import MdqService`; `from mcp_servers.mdq.indexer import
  index_paths`; `import asyncio`.
- If the implementer adopts the Option B fallback described in the companion `search.py`
  document (dropping the exact `matched_count` query in favor of `shown_count` +
  `possibly_more: bool`), this test file's `matched_count`-specific assertions
  (`test_matched_count_is_exact_regardless_of_limit`) would need equivalent adjustment to check
  `possibly_more` instead — flag this dependency in a comment at the top of the test file so a
  future implementer switching options knows this file must be revisited together with
  `search.py`.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| File created | `ls tests/test_mdq_search_counts.py` | exists |
| Lint | `uv run ruff check tests/test_mdq_search_counts.py` | 0 errors |
| Type check | `uv run mypy tests/test_mdq_search_counts.py` | no new errors |
| Targeted run | `uv run pytest tests/test_mdq_search_counts.py -v` | all pass (after companion `search.py`/`mdq_models.py` code changes land) |
| Regression coverage | `test_matched_count_is_exact_regardless_of_limit` | fails against pre-fix code (no `matched_count` field exists; `total` would equal the limited count, not 5), passes after the fix |
| Full search-related suite | `uv run pytest tests/test_mdq_search_modes.py tests/test_mdq_search_limits.py tests/test_mdq_search_counts.py -v` | all pass |
