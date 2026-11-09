## Goal
- Guarantee that `CrawlOrchestrator.crawl_site` leaves no running task behind: on every exit from the BFS loop (budget stop, error, cancellation) cancel the remaining tasks and await them, logging their errors once, before the HTTP client and the session database connection are closed.

## Priority
Medium

## Scope
- **In-Scope**:
  - A cancel-and-gather step in the `finally` path of `crawl_site` (`scripts/rag/ingestion/orchestrator.py`), implemented as a small private helper.
  - A budget-limited crawl test with slow responses asserting that no task created by the crawl is alive after return, no "never retrieved" warning appears, and no file is written after return.
- **Out-of-Scope**:
  - Concurrency settings, budget semantics, the typed fetch result and redirect work of the sibling plans, atomic file writes for crash safety (see Assumptions).
- **Dependencies**: N/A: none. Same-file note: `scripts/rag/ingestion/orchestrator.py` is also edited by the ragrev011 and ragrev012 plans, which change `_process_crawl_url_async`; this plan changes `crawl_site` only (compatible, any order).

## Background
Review finding F-013. In `crawl_site` (`scripts/rag/ingestion/orchestrator.py:100-181`, revalidated 20261109 after ragrev011/ragrev012 landed; line numbers shifted, behavior unchanged) the two budget checks execute `break` inside `while not queue.empty() or pending` while `pending` may hold running tasks; the `finally` closes only `session_db`, and the surrounding `async with httpx.AsyncClient` exits right after, so tasks still in `pending` can use a closed client or connection. Impact is real in production: `WebCrawler.crawl` calls `orchestrator.crawl_site` for each target in sequence inside one event loop (`scripts/rag/ingestion/crawler.py:121`), so orphaned tasks of one site keep running while the next site's crawl starts. Two facts found while verifying (checked in Step 3): (1) the Issue's open question about cancellation mid-`save_http` is resolved by code reading: after `fetch_html` returns, `_process_crawl_url_async` runs `extract_content`, `resolve_lang`, `save_http` (a synchronous `path.write_bytes`, `crawl_persister.py`), and `enqueue_links` with no `await`, so a task can only be cancelled at the sleep or fetch awaits, never in the middle of a write; (2) the in-loop `t.exception()` raises `CancelledError` for a cancelled task, so the cleanup must collect results with `gather(..., return_exceptions=True)` and must not reuse that call. Existing budget tests (`tests/rag/ingestion/test_crawler_integration.py:161-244`, `TestMaxPagesBoundaryCondition`) use `respx` and run the crawl to its budget stop.

## Problem
Orphaned tasks can fail with a closed client or connection, log "Task exception was never retrieved", or write one more document after the crawl was declared finished (and, with several target sites, interfere with the next site).

## Reason for Change
Reaching `max_pages` is the normal way a bounded crawl ends, so the race is hit routinely.

## Implementation Intent
`pending` is already declared before the `try` (revalidated 20261109: `orchestrator.py:105`, so no move is needed); in `finally` call a helper that cancels every not-yet-done task, awaits them with `asyncio.gather(*tasks, return_exceptions=True)`, and logs a non-cancellation exception once; only then close `session_db`. The `async with` client then exits with nothing in flight.

## Requirements
- `REQ-001`: After `crawl_site` returns or raises, no task created by it is still running.
- `REQ-002`: Cleanup does not raise: task exceptions other than cancellation are logged once, and a cancelled task is not reported as an error.
- `REQ-003`: Budget semantics, concurrency, log messages for the budget stop, and persisted documents written before the stop are unchanged and intact.
- `REQ-004`: A budget-limited crawl with in-flight slow tasks produces no "Task exception was never retrieved" message and writes no file after `crawl_site` returns.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/ingestion/orchestrator.py` | Modify | Cancel and gather pending tasks in the `finally` path of `crawl_site` via a private helper | `REQ-001`..`REQ-003` / AC-1..AC-3 | `break` at the budget checks (L144, L152) and the empty-pending exit (L163-164), `finally` closes only `session_db` (L178-180), `pending` assigned at L105 before the `try` (revalidated 20261109) | `tests/rag/ingestion/test_crawler_integration.py` | Verified |
| `tests/rag/ingestion/test_crawler_integration.py` | Modify | Add the in-flight budget-stop test next to `TestMaxPagesBoundaryCondition` | `REQ-001`..`REQ-004` / AC-1..AC-4 | `TestMaxPagesBoundaryCondition` at L161-244 uses `respx` and `caplog` (revalidated 20261109) | self | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/rag/ingestion/crawler.py` | Sequential `crawl_site` calls in one loop (L121) that make orphaned tasks interfere | `REQ-001` |
| `scripts/rag/ingestion/crawl_persister.py` | `save_http` is synchronous `write_bytes`, so cancellation cannot interrupt it | `REQ-003` |
| `scripts/rag/ingestion/http_fetcher.py` | The fetch and retry sleeps are the cancellation points | `REQ-001` |

## Acceptance Criteria
- AC-1 (`REQ-001`): after `crawl_site` returns from a budget stop with slow requests in flight, `asyncio.all_tasks()` contains no task created by the crawl.
- AC-2 (`REQ-002`): a task raising a non-cancellation exception during cleanup is logged once and does not make `crawl_site` raise; cancelled tasks are silent.
- AC-3 (`REQ-003`): existing budget tests (`test_stops_at_max_pages`, `test_max_pages_warning_logged`) pass unmodified and the persisted JSON files are valid.
- AC-4 (`REQ-004`): the new test finds no "never retrieved" text in the captured asyncio logs and an unchanged file list after a short wait following return.

## Tests
- `REQ-001`/`REQ-004`: new async budget-stop test with `respx` slow responses (delayed side effect), `max_pages=1`, concurrency above 1, asserting live tasks, logs, and files.
- `REQ-002`: a test where an in-flight request raises an unexpected exception during cleanup.
- `REQ-003`: existing budget tests unmodified.
- Static: `uv run ruff check`, `uv run mypy`; `uv run pytest tests/rag/ingestion -q`.

## Documentation Impact
N/A: no documentation change; internal lifecycle only (the crawler doc's budget description is unchanged because budget semantics do not change).

## Assumptions
- Atomic (temp file plus rename) writes for crash safety are a separate concern from cancellation safety (which this plan shows is not at risk) and belong to the partial-write finding of the same review (`issues/20261108-131236_ragrev017_partial-chunk-write-gap.md`) or a later Issue, not to this plan.
- Overlap judgment (Step 8b, `tools/check_plan_target_overlaps.py`): `scripts/rag/ingestion/orchestrator.py` is also a target of the ragrev011 and ragrev012 plans; compatible, they edit `_process_crawl_url_async` and the client construction while this plan edits the loop exit in `crawl_site`; no ordering requirement. `tests/rag/ingestion/test_crawler_integration.py` is also a target of the ragrev011 plan; compatible (new test class vs. updated fetch tests).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the cancellation grace should be bounded (a task that ignores cancellation could block cleanup) | No such task exists in the current code (all awaits are cancellable httpx and sleep calls) | Non-blocking; revisit if a non-cancellable await is added | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/ingestion/orchestrator.py` | Modify | Medium (crawl loop exit; `radon`: `crawl_site` C (11)) | 5 | N/A | not applicable (rsynced) |
| `tests/rag/ingestion/test_crawler_integration.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
Path A (2 target files, no interface or schema change; the public method signature and behavior of the budget stop are unchanged). The cleanup is a private async helper called from `finally`, which keeps `crawl_site` from growing past its current complexity band (C (11)).

Alternatives: (a) `asyncio.TaskGroup` rewrite of the loop, rejected (changes the FIRST_COMPLETED scheduling and budget logic, beyond a minimal fix); (b) cancel only on the budget `break` paths, rejected (an exception or outer cancellation leaves the same orphans). Chosen: `finally`-based cancel-and-gather.

Validation baseline: `radon cc` recorded above; `vulture`/`bandit` pre-existing findings recorded in `plans/20261108-164302_ragrev001_mqe-malformed-response-abort.md` (source unchanged); `diff-cover`: no changed lines at plan time, 90 percent at implementation.

## Implementation steps
1. **Phase 1: Test first**
   - [ ] Budget-stop-with-in-flight-tasks test and the cleanup-exception test (`REQ-001`, `REQ-002`, `REQ-004`; `tests/rag/ingestion/test_crawler_integration.py`)
2. **Phase 2: Cleanup path**
   - [ ] Define `pending` before the `try`; add the cancel-and-gather helper in `finally` before closing `session_db` (`REQ-001`..`REQ-003`; `scripts/rag/ingestion/orchestrator.py`)
3. **Phase 3: Deployment & Verification**
   - [ ] `uv run pytest tests/rag/ingestion -q`, lint/type gates; deploy hand-off to `skills/deploy/SKILL.md` after commit and push, at the user's decision (all requirements; `scripts/rag/ingestion/orchestrator.py`)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/ingestion/orchestrator.py` | Async integration (`respx`, slow responses) | `uv run pytest tests/rag/ingestion/test_crawler_integration.py -q` | new test fails on HEAD (live tasks), passes after |
| ingestion suites | Regression | `uv run pytest tests/rag/ingestion -q` | green |
| touched code | Static | `uv run ruff check`, `uv run mypy`, `PYTHONPATH=scripts uv run lint-imports` | clean |

## Risks
- **Risk**: cancelling in-flight fetches drops pages that would have been persisted just past the budget → **Mitigation**: the budget stop already means those pages are beyond `max_pages`; semantics unchanged.
- **Risk**: a flaky timing-based test → **Mitigation**: use explicit events or a controlled delayed side effect instead of sleeping for fixed intervals, and assert on task state rather than wall-clock.
- **Risk**: cleanup masks the original exception when `crawl_site` fails → **Mitigation**: the helper never raises and runs in `finally`, so the original exception propagates.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: test first | Completed | 20261109-225207 | 20261110-075214 |  |
| 2 | Phase 2: cleanup path | Completed | 20261109-225207 | 20261110-075214 |  |
| 3 | Phase 3: deployment and verification | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261109-225207_01_scripts_rag_ingestion_orchestrator.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261109-225207_02_tests_rag_ingestion_test_crawler_integration.py.md | 1 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261108-131231_ragrev013_crawl-orphaned-tasks-budget.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261108-170226
- **Related target files**: `scripts/rag/ingestion/orchestrator.py`, `tests/rag/ingestion/test_crawler_integration.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1; Acceptance Criteria 1 | `scripts/rag/ingestion/orchestrator.py` | Phase 2 | AC-1 | budget-stop in-flight test | Confirmed by repository evidence |
| REQ-001 | Testing Expectations | `tests/rag/ingestion/test_crawler_integration.py` | Phase 1 | AC-1 | budget-stop in-flight test | Explicit in issue |
| REQ-002 | Required Changes 2 | `scripts/rag/ingestion/orchestrator.py` | Phase 2 | AC-2 | cleanup-exception test | Explicit in issue |
| REQ-002 | Required Changes 2 | `tests/rag/ingestion/test_crawler_integration.py` | Phase 1 | AC-2 | cleanup-exception test | Explicit in issue |
| REQ-003 | Constraints; Unresolved Questions (resolved: no await in the write path) | `scripts/rag/ingestion/orchestrator.py` | Phase 2 | AC-3 | existing budget tests | Confirmed by repository evidence |
| REQ-004 | Acceptance Criteria 2; Testing Expectations | `tests/rag/ingestion/test_crawler_integration.py` | Phase 1 | AC-4 | budget-stop in-flight test | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261109-225207 -->
