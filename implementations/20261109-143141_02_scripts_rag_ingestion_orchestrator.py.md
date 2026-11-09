## Goal

Make `_process_crawl_url_async` branch on the typed fetch result: a not-modified page above the depth limit is fetched once more without validator headers and its links are enqueued (nothing is extracted or persisted), and a failed fetch is reported distinctly and enqueues nothing (`REQ-002`: unconditional discovery fetch below the depth limit; `REQ-003`: no extraction, persistence, or budget count for a 304 page; `REQ-004`: failed reported distinctly; `REQ-005`: a changed child of a 304 parent is reached).

## Scope
**Release unit**: ragrev011-core

- In scope: `scripts/rag/ingestion/orchestrator.py` (the result handling in `_process_crawl_url_async` and one new private helper).
- Out of scope: `crawl_site` and `_drain_queue_to_tasks`, the early returns for empty content and unsupported language (Plan UNK-02), link filtering and robots policy in `LinkDiscovery`, redirect handling, and the persistence path.
- Plan: `plans/20261108-165922_ragrev011_recrawl-304-drops-subtree.md` (Plan step 3); apply after document `01`.

## Assumptions

- Re-verified at generation time (by symbol): `_process_crawl_url_async` acquires the semaphore, sleeps `crawl_delay`, reads conditional headers, calls `fetch_html`, returns on `None`, then extracts, resolves the language, calls `save_http`, increments `budget.persisted`, and calls `enqueue_links` last; `enqueue_links(html, url, start_url, depth, queue)` returns without enqueueing when `depth >= max_depth`, and `_drain_queue_to_tasks` drops URLs with `depth > self._max_depth`.
- The discovery fetch runs inside the same `async with sem` block (the semaphore is already held), after one more `crawl_delay` sleep, and counts toward the scheduled-URL bound only through the links it enqueues.
- Names created by document `01` (`Fetched`, `NotModified`, `FetchFailed`, `FetchResult`) are declared by that earlier-`seq` sibling.
- `tests/rag/ingestion/test_crawler_integration.py::TestMaxPagesBoundaryCondition::test_max_pages_warning_logged` serves 304 children at `depth == max_depth`; with the depth guard no second request is made, so its `len(respx.calls) <= 2 * max_pages` assertion stays valid unmodified.
- Overlap (Plan step 2 judgments, recorded in the Plan Assumptions): ragrev012 (depends on this Plan, redirect handling in the same function), ragrev013 (`crawl_site` only), ragrev014 (robots check before the request), and ragrev018 (`save_http` result after the write) are compatible with this edit, which is confined to the result handling before extraction plus one helper. Locate code by symbol name, not line number.

## Design decisions

- Handle the two non-fetched outcomes in `_process_crawl_url_async` with early `return` after logging, keeping the fetched path's body unchanged below an `isinstance` check; the discovery fetch lives in a small private helper `_discover_links_of_unchanged_page` (new) so `_process_crawl_url_async` stays at complexity A or B.
- Use `self._max_depth` as the guard so a not-modified page at the limit makes no extra request (`REQ-002`); `enqueue_links` stays the single place that filters origin, nofollow, and robots (`REQ-003`).

## Alternatives considered

- Persist a link list or the HTML for later discovery: rejected here (storage change; Plan UNK-01).
- Fetch every page unconditionally and compare validators locally: rejected; it gives up the bandwidth benefit for leaf pages.

## Implementation
### Target file
`scripts/rag/ingestion/orchestrator.py`

### Procedure
1. Import `FetchFailed`, `Fetched`, and `NotModified` from `rag.ingestion.http_fetcher` next to the existing `HttpFetcher` import (same `# noqa: E402` style as its neighbors).
2. Replace `if result is None: return` and the tuple unpacking in `_process_crawl_url_async` with: when the result is `NotModified`, log `"not modified: %s"` at info and `await self._discover_links_of_unchanged_page(...)`, then return; when it is `FetchFailed`, log `"fetch failed, subtree not discovered: %s"` at warning and return; otherwise read `html`, `etag`, and `last_modified` from the `Fetched` result and continue unchanged.
3. Add `_discover_links_of_unchanged_page` (new) taking `url`, `depth`, `start_url`, `queue`, and `client`: return at once when `depth >= self._max_depth`; otherwise `await asyncio.sleep(self._crawl_delay)`, call `self._http_fetcher.fetch_html(url, client)` with no extra headers, and on a `Fetched` result call `self._link_discovery.enqueue_links(result.html, url, start_url, depth, queue)`; on any other result log `"discovery fetch did not return a body: %s"` at warning and return.
4. Update the `_process_crawl_url_async` docstring to say a not-modified page is re-fetched for link discovery only and is neither extracted, persisted, nor counted.

### Method
- Edit by symbol; leave the extraction, language, `save_http`, `budget.persisted += 1`, and trailing `enqueue_links` lines untouched.
- Keep the new helper's own logic to the depth guard, one fetch, and one branch; no recursion and no queue writes other than through `enqueue_links`.

### Details
- Log wording is part of the contract tested by document `03`: the not-modified message is info level and the failed message is warning level, so a caplog test can tell them apart.
- Run `uv run python tools/check_module_size.py` (the module is far below the gate) and `uv run python tools/check_mock_patch_targets.py`.

## Compatibility considerations

- Behavior change by design: an unchanged index page above the depth limit now costs one extra unconditional GET per re-crawl; nothing extra is persisted, embedded, or counted against `max_pages`.
- `crawl_site`, the scheduling bound, and the persisted budget semantics are unchanged; the not-modified page is still counted as scheduled (it was added to `visited` by `_drain_queue_to_tasks`).

## Security considerations

N/A: the discovery fetch requests a URL that already passed the same origin and robots filters at enqueue time, using the same client and headers; redirect policy is ragrev012.

## Rollback considerations

- Revert the release unit's commits together (documents `01` to `03`); no persisted state is involved.

## Validation plan

- After document `01`, this document, and document `03`: `uv run pytest tests/rag/ingestion/test_crawler_integration.py tests/rag/ingestion/test_robots.py -q`, then `uv run pytest tests/rag/ingestion -q`.
- `uv run ruff format` and `uv run ruff check`; `uv run mypy`; `PYTHONPATH=scripts uv run lint-imports`; `uv run python tools/check_module_size.py`.
- Coverage on changed lines at 90 percent (`diff-cover`).

## Completion criteria

- A 304 start page at `depth < max_depth` triggers exactly one unconditional GET of the same URL and enqueues its links; at `depth >= max_depth` no second request is made.
- A 304 page is not extracted, `save_http` is not called for it, and `budget.persisted` does not change.
- A failed fetch logs the failed message at warning level, a 304 logs the not-modified message at info level, and neither path enqueues links unless the discovery fetch returns a body.
- No `result is None` check on `fetch_html` remains.

## Out of Scope

- Empty-content and unsupported-language early returns (Plan UNK-02), a stored link list, `crawl_site` changes, redirect and robots policy, and the test and documentation edits (documents `03` and `04`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Import the result types and branch on the outcome in `_process_crawl_url_async` | Pending | — | — | |
| 2 | Add `_discover_links_of_unchanged_page` (new) and update the docstring | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) together with documents `01` and `03` | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (discovery fetch for 304 pages below the depth limit), `REQ-003` (304 page not persisted or counted), `REQ-004` (failed reported distinctly), `REQ-005` (changed child reached)
- **Source issue**: issues/20261108-131125_ragrev011_recrawl-304-drops-subtree.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-165922_ragrev011_recrawl-304-drops-subtree.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-143141
- **Related target files**: `scripts/rag/ingestion/orchestrator.py`
