## Goal

Split the single `max_pages` counter into two bounds (`REQ-001`–`REQ-004`): a
persisted-page budget that gates the BFS loop on pages actually written, and a
per-call scheduling cap on `len(visited)` so non-persisted fetches (304, empty
content, language rejection, task failures) cannot silently consume the operator's
page budget nor make the loop unbounded. Log scheduled-vs-persisted at loop stop
(`REQ-004`).

## Scope
**Release unit**: crawl-persisted-budget (Plan Phases 1–3)

## Assumptions
- `save_http` returning normally means the page is persisted: `crawl_persister.py`
  has no post-save failure path (re-confirm at implementation start; `save_http`
  returns a `Path` at `crawl_persister.py:145`; its skip branches return a path
  without writing, but those conditions — unsupported lang, empty content — are
  already filtered in `_process_crawl_url_async` before `save_http` is reached).
- Budget state is per `crawl_site` call: `WebCrawler.crawl` calls `crawl_site` per
  target URL (`crawler.py:106,116`), each getting a fresh budget — matching today's
  per-call `visited` scope.
- `_drain_queue_to_tasks` / `_process_crawl_url_async` have no external callers
  except the vacuous `test_max_pages_warning_logged` (being replaced); the public
  entry is `crawl_site` only. Verified by `rg` across `tests/`.

## Design decisions
- **`_CrawlBudget` dataclass, passed by reference.** A small internal
  `@dataclass _CrawlBudget(persisted: int, max_persist: int, max_scheduled: int)`
  created in `crawl_site` and threaded through `_drain_queue_to_tasks` and
  `_process_crawl_url_async`. Chosen over (a) instance attributes
  (`self._persisted` — cross-`crawl_site`-call state that must be reset per call;
  lifecycle hazard) and (b) a plain local counter (cannot reach the private helpers).
  Private to the orchestrator; no public-API change.
- **Fixed multiplier constant.** `SCHEDULED_BUDGET_MULTIPLIER = 2` at module level;
  `max_scheduled = self._max_pages * SCHEDULED_BUDGET_MULTIPLIER`. Matches the
  issue's chosen resolution (fixed multiplier over a config key).
- **Two top-of-loop guards, persisted first.** (a) `budget.persisted >= budget.max_persist`
  → WARNING `"persisted budget reached"` + break; (b) `len(visited) >= budget.max_scheduled`
  → WARNING `"scheduling budget reached"` + break. The old
  `len(visited) >= self._max_pages` guard is removed.
- **Per-URL drain cap fixes the overshoot.** Inside the `while not queue.empty()`
  loop of `_drain_queue_to_tasks`, add `if len(visited) >= budget.max_scheduled: break`
  before `visited.add`. URLs left queued at cap-hit are dropped exactly as today's
  break drops them.
- **Persisted increment after `save_http`.** `_process_crawl_url_async` does
  `budget.persisted += 1` immediately after `self._persister.save_http(...)` returns,
  before `enqueue_links`. Single event loop; the loop reads `budget.persisted` only
  at `asyncio.wait` FIRST_COMPLETED boundaries, so no lock is needed.
- **Stop-summary log once, after the loop.** `logger.info("BFS stop: scheduled=%d persisted=%d max_pages=%d", len(visited), budget.persisted, budget.max_persist)` placed after the `while` loop so it fires on every exit path (either guard, the `if not pending` break, or normal exhaustion).

## Alternatives considered
- Instance attributes (`self._persisted`): rejected (per-call reset lifecycle hazard).
- Config key for the multiplier: rejected (operator tuning knob without measured
  justification; issue fixed the multiplier).
- Counting `len(visited)` as the persisted budget: rejected — `visited` grows on
  non-persisted fetches too, which is exactly the bug.

## Implementation
### Target file
- `scripts/rag/ingestion/orchestrator.py`

### Procedure
1. Add `from dataclasses import dataclass`; add module constant
   `SCHEDULED_BUDGET_MULTIPLIER = 2` and the `_CrawlBudget` dataclass before
   `class CrawlOrchestrator`.
2. In `crawl_site`, create `budget = _CrawlBudget(max_persist=self._max_pages,
   max_scheduled=self._max_pages * SCHEDULED_BUDGET_MULTIPLIER)` and replace the two
   guards with the persisted/scheduled pair; thread `budget` into `_drain_queue_to_tasks`.
3. In `_drain_queue_to_tasks`, add the `budget` parameter and the per-URL
   `len(visited) >= budget.max_scheduled` break before `visited.add`.
4. In `_process_crawl_url_async`, add the `budget` parameter and
   `budget.persisted += 1` right after `save_http` returns, before `enqueue_links`.
5. Add the `BFS stop:` summary log after the `while` loop in `crawl_site`.

### Method
- Dataclass placement (after imports, before the class):
  ```python
  SCHEDULED_BUDGET_MULTIPLIER = 2


  @dataclass
  class _CrawlBudget:
      """Per-crawl_site page-budget state: persisted count and scheduling bound."""

      persisted: int = 0
      max_persist: int = 0
      max_scheduled: int = 0
  ```
- `crawl_site` guard block becomes:
  ```python
  budget = _CrawlBudget(
      max_persist=self._max_pages,
      max_scheduled=self._max_pages * SCHEDULED_BUDGET_MULTIPLIER,
  )
  ...
  while not queue.empty() or pending:
      if budget.persisted >= budget.max_persist:
          logger.warning(
              "persisted budget reached: persisted=%d max_pages=%d for %s",
              budget.persisted,
              budget.max_persist,
              start_url,
          )
          break
      if len(visited) >= budget.max_scheduled:
          logger.warning(
              "scheduling budget reached: scheduled=%d max_pages=%d for %s",
              len(visited),
              budget.max_persist,
              start_url,
          )
          break
      pending |= self._drain_queue_to_tasks(
          queue, visited, start_url, hint_lang, client, sem, budget,
      )
      if not pending:
          break
      ...
  logger.info(
      "BFS stop: scheduled=%d persisted=%d max_pages=%d",
      len(visited),
      budget.persisted,
      budget.max_persist,
  )
  ```
- `_drain_queue_to_tasks`:
  ```python
  def _drain_queue_to_tasks(
      self, queue, visited, start_url, hint_lang, client, sem, budget,
  ) -> set[asyncio.Task]:
      tasks: set[asyncio.Task] = set()
      while not queue.empty():
          url, depth = queue.get_nowait()
          if url in visited or depth > self._max_depth:
              continue
          if len(visited) >= budget.max_scheduled:
              break
          visited.add(url)
          tasks.add(
              asyncio.create_task(
                  self._process_crawl_url_async(
                      url, depth, start_url, hint_lang, queue, client, sem, budget,
                  ),
              ),
          )
      return tasks
  ```
- `_process_crawl_url_async`: add `budget` to the signature and insert
  `budget.persisted += 1` between the `save_http(...)` call and
  `self._link_discovery.enqueue_links(...)`.

### Details
- `budget.persisted` starts at 0 (dataclass default); `max_persist`/`max_scheduled`
  are set at creation. `scheduled` in the summary log is `len(visited)` (dedup count).
- Do not touch `crawl_site`'s semaphore/queue setup, `_max_depth` handling,
  `enqueue_links`, or the fetch/extract/lang pipeline — only the budget wiring.
- No schema, public-API, or payload-shape change; `crawl_site`'s signature is
  unchanged. `scan_change_consumers.py` is not required.

## Compatibility considerations
Behavior changes intentionally (operator-visible stop log, persisted-count semantics).
`test_max_pages_boundary` (all-persisted path) is unaffected — new and old semantics
agree there. Dedup (`visited`), `max_depth`, and single-fetch-per-URL are preserved.

## Security considerations
N/A: no input-handling, network, or credential change. The stop-summary log emits
URL counts and the start URL only; no secret flows through it.

## Rollback considerations
Revert the commit to `orchestrator.py`. The change is confined to `crawl_site`, two
private helpers, and two module-level additions.

## Validation plan
- Integration (304-heavy): stub via respx routes (or `fetch_html`) so 3 URLs return 304 and 2 return
  content at `max_pages=2` → 2 chunk files persisted under `rag-src/`, scheduled ≤ 4
  (fails today; companion test document).
- Integration (failure-only): every fetch raises → loop terminates, scheduled ≤
  `2 * max_pages`, persisted = 0, summary log emitted.
- Characterization: `test_max_pages_boundary` passes unchanged before and after.
- Regression: `uv run pytest tests/rag/ingestion` passes, incl. `test_max_pages_fallback_default`
  (`_max_pages == 200`) and the max_depth/external-link tests unchanged.
- Static gates: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages
  scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`,
  `uv run bandit -r scripts/ -c pyproject.toml -ll` — clean.
- Coverage: ≥ 90% diff-cover on changed lines (`rules/toolchain.md`).

## Completion criteria
- `_CrawlBudget` + `SCHEDULED_BUDGET_MULTIPLIER = 2` exist; `crawl_site` has the two
  guards, `_drain_queue_to_tasks` has the per-URL cap, `_process_crawl_url_async`
  increments after `save_http`, and the stop-summary log fires.
- 304-heavy run persists all M ≤ max_pages pages; failure-only run bounded at
  `2 * max_pages` scheduled.
- `test_max_pages_boundary` green unchanged; full ingestion suite green.
- Static gates clean; diff-cover ≥ 90%.

## Out of Scope
- Crawl scheduling and target-list generation.
- `CrawlOrchestrator.crawl` removal (open `crawl002` issue, disjoint region `:76-88`).
- The `max_pages` default drift (`crawler.py:66` 200 vs `orchestrator.py:74` 500) —
  recorded as UNK-02, a separate issue candidate.
- Conditional-GET behavior itself.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `_CrawlBudget` + `SCHEDULED_BUDGET_MULTIPLIER`; swap guards; drain cap; persisted increment; stop-summary log | Pending | — | — | REQ-001..REQ-004 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A at plan creation | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|-------|----------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`
- **Source issue**: `issues/20261106-073538_raging009_crawl-max-pages-pending-tasks.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261106-104423_raging009_crawl-max-pages-pending-tasks.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-154603
- **Related target files**: `scripts/rag/ingestion/orchestrator.py`
