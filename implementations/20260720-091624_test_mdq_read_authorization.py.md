# Implementation: tests/test_mdq_read_authorization.py (new — read-time authorization
regression tests)

Source plan: `plans/20260719-205532_plan.md`, Implementation steps Phase 3, item 4.

## Goal

Create a new dedicated test file proving that narrowing `allowed_dirs` after indexing
immediately hides previously-indexed content from `search_docs`, `get_chunk`, and `grep_docs`
(the companion `search.py`/`mdq_service.py`/`db_grep.py` implementation docs), and that
`grep_docs(paths=[...])` rejects explicitly-requested unauthorized paths.

## Scope

**In scope:**
- New file `tests/test_mdq_read_authorization.py`.
- Index-then-narrow-`allowed_dirs` test pattern applied to each of `search_docs`, `get_chunk`,
  `grep_docs` (no-`paths` case).
- `grep_docs(paths=[...])` explicit-path rejection test (raises `MdqAuthorizationError`).
- The deny-all short-circuit case flagged in the companion `db_grep.py` doc (empty
  `authorized_paths` must return "No matches found.", not an unfiltered scan).

**Out of scope:**
- `MdqConfig` validation tests — covered by `tests/test_mdq_config.py` (companion doc).
- Health `/health` field tests — covered by `tests/test_mdq_health.py` (companion doc).
- Re-testing `outline`/`index_paths`/`refresh_index` authorization — already covered by
  existing tests per the plan's Scope ("Any change to `outline`/`index_paths`/`refresh_index`
  authorization" is explicitly out of scope, "already enforced pre-change, no gap there").

## Assumptions

1. `tests/test_mdq_service.py`'s existing `service` fixture (confirmed by direct read,
   `tests/test_mdq_service.py:38-48`) is the established pattern for this package:
   ```python
   @pytest.fixture
   def service(tmp_path: Path) -> MdqService:
       fd, db = mkstemp(suffix=".db", dir=str(tmp_path))
       svc = MdqService(db_path=db)
       svc._allowed_dirs = [str(tmp_path)]
       return svc
   ```
   This new file follows the same construction pattern: build a service with `allowed_dirs`
   initially covering a temp directory, index a file there, then **narrow**
   `svc._allowed_dirs` to a different (non-overlapping) directory to simulate the
   config-narrowed-after-indexing scenario the plan targets.
2. Indexing a file requires calling `index_paths()`/`IndexPathsRequest` (imported from
   `mcp_servers.mdq.indexer`/`mcp_servers.mdq.mdq_models` per the existing test file's import
   block) against a path that is authorized *at index time*, then later reassigning
   `svc._allowed_dirs` to something that excludes it, before calling the read-time methods
   under test.
3. `MdqAuthorizationError` is importable from `mcp_servers.mdq.mdq_models` (already used
   elsewhere, e.g. `mdq_service.py:33`).
4. Getting a valid `chunk_id` for the `get_chunk` test requires either querying the DB
   directly after indexing, or capturing it from a preceding `search_docs`/`outline` call —
   check `tests/test_mdq_service.py`'s existing tests for the established way to obtain a
   `chunk_id` in this test suite (likely via a direct `sqlite3` query against
   `svc._get_db_connection()` or via `outline()`'s returned chunk IDs) and reuse that
   pattern rather than inventing a new one.

## Implementation

### Target file

`tests/test_mdq_read_authorization.py`

### Procedure

1. Create the file with a module docstring: "Read-time authorization regression tests for
   `search_docs`, `get_chunk`, `grep_docs` — verifies narrowing `allowed_dirs` after indexing
   immediately hides previously-indexed content, per
   `plans/20260719-205532_plan.md`."
2. Reuse (or locally redefine, matching exactly) the `service`/`md_file` fixture pattern from
   `tests/test_mdq_service.py`.
3. Add test cases (pseudocode):
   ```
   class TestSearchDocsReadTimeAuthorization:
       async def test_narrowed_allowed_dirs_hides_indexed_content(self, tmp_path): ...
           # 1. svc._allowed_dirs = [str(tmp_path)]; index a .md file under tmp_path
           # 2. confirm search_docs(query matching file content) finds it
           # 3. svc._allowed_dirs = [str(tmp_path / "other-unrelated-dir")]
           # 4. search_docs(same query) -> "No results found for: ..." (row silently dropped)

   class TestGetChunkReadTimeAuthorization:
       async def test_narrowed_allowed_dirs_denies_get_chunk(self, tmp_path): ...
           # 1. index file, capture chunk_id while still authorized
           # 2. narrow svc._allowed_dirs to exclude the indexed file's directory
           # 3. get_chunk(GetChunkRequest(chunk_id=...)) raises MdqAuthorizationError
           # 4. assert the exception message does NOT contain the source file path
           #    (no leak per mdq_service.py doc's Assumption 3)

   class TestGrepDocsReadTimeAuthorization:
       async def test_narrowed_allowed_dirs_hides_content_no_filter(self, tmp_path): ...
           # 1. index file with content matching a grep pattern, while authorized
           # 2. narrow allowed_dirs to exclude it
           # 3. grep_docs(GrepDocsRequest(pattern=..., paths=None)) -> "No matches found."

       async def test_explicit_unauthorized_path_rejected(self, tmp_path): ...
           # 1. index file under tmp_path, then narrow allowed_dirs to a different dir
           # 2. grep_docs(GrepDocsRequest(pattern=..., paths=[str(indexed_file)]))
           #    raises MdqAuthorizationError (fails the whole call, does not silently drop)

       async def test_deny_all_returns_no_matches_not_unfiltered_scan(self, tmp_path): ...
           # 1. index file while allowed_dirs=[str(tmp_path)]
           # 2. svc._allowed_dirs = [] (deny-all)
           # 3. grep_docs(GrepDocsRequest(pattern=..., paths=None)) -> "No matches found."
           #    (regression test for the db_grep.py doc's flagged empty-authorized-set edge case —
           #    must NOT fall through to an unfiltered scan that leaks all indexed content)
   ```
4. Where an async event loop is needed to call `MdqService`'s `async def` methods
   (`search_docs`, `get_chunk`, `grep_docs` are all `async def` per
   `mdq_service.py:129,138,326`), use whatever async test runner convention
   `tests/test_mdq_service.py` already uses (check its `pytest.ini`/`pyproject.toml`
   `asyncio_mode` setting or explicit `@pytest.mark.asyncio` decorators, and match exactly).

### Method

New pytest file built entirely on the existing `service`/`md_file` fixture conventions already
established in `tests/test_mdq_service.py`, with one new structural test idiom introduced:
index-while-authorized, then mutate `svc._allowed_dirs` directly (bypassing config reload) to
simulate "config changed after indexing" without needing to actually rewrite a TOML file
mid-test.

### Details

- Mutating `svc._allowed_dirs` directly (rather than re-instantiating `MdqService` with a
  different config) is the deliberate, minimal way to simulate "the operator narrowed
  `allowed_dirs` and the running service picked up the new config" — matches the existing
  `service` fixture's own pattern of setting `svc._allowed_dirs = [str(tmp_path)]` directly
  after construction (`tests/test_mdq_service.py:44`).
- Do not assert on internal SQL query text — assert only on the public method's return
  value/raised exception, keeping tests resilient to the internal filtering implementation
  detail (list comprehension vs. SQL `IN` clause).
- `test_deny_all_returns_no_matches_not_unfiltered_scan` is the most important regression
  case flagged during this plan's grounding (see companion `db_grep.py` doc, Assumption 3) —
  do not skip it; it is the one edge case where naive reuse of `db_grep.py`'s existing
  `if req_paths:` falsy-check could silently leak all content instead of enforcing deny-all.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| File collected | `uv run pytest tests/test_mdq_read_authorization.py --collect-only` | test classes/functions listed, no collection errors |
| All pass | `uv run pytest tests/test_mdq_read_authorization.py -v` | all pass |
| No regression | `uv run pytest tests/test_mdq_service.py tests/test_mdq_search_modes.py tests/test_mdq_get_chunk_behavior.py -v` | all pass |
| Full MDQ suite | `uv run pytest tests/test_mdq_*.py -v` | no new failures |
| Lint | `uv run ruff check tests/test_mdq_read_authorization.py` | 0 errors |
| Type check | `uv run mypy tests/` | no new errors |
| MDQ/RAG boundary | `uv run pytest tests/test_mdq_rag_boundary.py -v` | pass (no new cross-DB access introduced) |
