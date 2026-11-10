## Goal

- Caller-side test: a `save_http` result of `None` neither increments the persisted budget nor triggers link enqueueing in `_process_crawl_url_async` (`REQ-005`: `None` is not counted).

## Scope
**Release unit**: N/A: not part of a release unit

- One new async test in `TestMaxPagesBoundaryCondition` in `tests/rag/ingestion/test_crawler_integration.py`.

## Assumptions

- Overlap note: the ragrev011/ragrev013 edits to this file are already landed (overlap check reports no findings this cycle); the new test patches `save_http` only and touches no shared helper (Plan Assumptions).
- The counted-page variant is already covered by `test_stops_at_max_pages` (L175), so only the uncounted variant is added (Plan Tests).

## Design decisions

- Reuse the `TestMaxPagesBoundaryCondition._page` helper and the `mock_config` / `tmp_path` / `respx` fixture pattern from `test_stops_at_max_pages` (L175-201) rather than a new fixture.

## Alternatives considered
N/A: test-only row.

## Implementation
### Target file
- `tests/rag/ingestion/test_crawler_integration.py`

### Procedure
- Add `test_none_save_result_not_counted` (new) to `TestMaxPagesBoundaryCondition`.

### Method
- `mock_config["max_pages"] = 1`, `mock_config["max_depth"] = 3`, `rag_src_dir` = `tmp_path` (same shape as `test_stops_at_max_pages`).
- Mock `http://example.com/start` to `self._page` with text "Alpha" and one link to the subpage URL mocked next (same href shape as `test_stops_at_max_pages`), and mock `http://example.com/b` to a persistable page; construct `WebCrawler(config=mock_config)`.
- `with patch.object(crawler.crawl_persister, "save_http", return_value=None):` run `await crawler.crawl_site("http://example.com/start", "en")` under `respx.mock` with `caplog.at_level(logging.WARNING, logger="rag.ingestion.orchestrator")`.
- Assert: no JSON file in `tmp_path` (persisted count stayed 0, so the `persisted budget reached` stop at `orchestrator.py` L137-140 never fires), `"persisted budget reached" not in caplog.text`, and only the start URL was requested (`len(respx.calls) == 1`) — the skip returned before `enqueue_links` (L278), so the linked page URL was never fetched.

### Details
- `patch.object` on the instance attribute `crawler.crawl_persister` (constructed at `crawler.py` L92) is the patch target `tools/check_mock_patch_targets.py` accepts.
- No other test in the class is modified.

## Compatibility considerations

- `TestMaxPagesBoundaryCondition`'s existing tests stay green unmodified (they use the unpatched `save_http`).

## Security considerations
N/A: test-only.

## Rollback considerations
N/A: revert the commit.

## Validation plan

- `uv run pytest tests/rag/ingestion/test_crawler_integration.py -v` — the new test is red on HEAD (the result is ignored and `budget.persisted += 1` runs unconditionally: with `max_pages = 1` the budget stop fires and the linked page is enqueued), green after the seq-02 document lands (red-first per Plan Phase 2).
- `uv run python tools/check_mock_patch_targets.py` — passes.

## Completion criteria

- AC-5: a crawl whose `save_http` returns `None` never reaches the persisted-budget warning and never fetches the page's links; existing budget tests stay green.

## Out of Scope

- The `save_http` contract (seq-01), the orchestrator change (seq-02), unit-level skip tests (seq-03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the test per Implementation > Procedure/Method/Details | Completed | 20261110 | 20261110 | seq-02 (orchestrator `if saved is None: return`, L326-327) was already landed in seq-02, so the test lands green on HEAD rather than red. Red-first is moot once the fix exists. |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261110 | 20261110 | ruff format/check clean; `check_mock_patch_targets.py` No findings; mypy clean on `scripts/ tests/eventbus tools` (558 files) and explicitly on this test file (tests/rag/ is outside the default mypy `files`); `TestMaxPagesBoundaryCondition` 6/6 green. |

**Adversarial verification notes:**
- `max_pages=1` makes the `len(respx.calls) == 1` and `len(glob("*-*.json")) == 0` assertions co-satisfiable by the persisted-budget stop alone (without the fix, `/b` is enqueued but the budget stop at `orchestrator.py` L142 breaks before draining it, so it is never fetched). The assertion that actually forces red without the fix is `"persisted budget reached" not in caplog.text`: without the fix `budget.persisted` reaches 1 after the start page, the stop fires, and the warning is logged. With the fix `budget.persisted` stays 0 and the warning never fires. The test is therefore a valid regression test for AC-5.
- The `save_http` result is ignored by the caller without the fix; patching it to `None` still exercises the real fetch/extract/lang-resolve path up to the save call, so the budget accounting is genuinely exercised, not stubbed.

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-005` (caller-side test that `None` is not counted)
- **Source issue**: issues/20261108-195932_ragrev018_save_http-returns-a-path-to-a-file-it-never-wrote-when-it-skips.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261109-102846_ragrev018_save_http-returns-a-path-to-a-file-it-never-wrote-when-it-skips.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-235704
- **Related target files**: `tests/rag/ingestion/test_crawler_integration.py`
