# max_pages budget is consumed by URLs that are never persisted

## Goal
- Make `max_pages` count pages actually persisted by the crawl, with a separate scheduling
  bound so 304/empty-content/language-rejected/failed fetches cannot silently consume the page
  budget or make the loop unbounded, and log scheduled-vs-persisted at loop end.

## Priority
Medium

## Scope
- **In-Scope**: budget accounting inside `CrawlOrchestrator.crawl_site` /
  `_drain_queue_to_tasks` / `_process_crawl_url_async`; characterization + new budget tests;
  replacement of the two vacuous max_pages integration tests; docs semantics update.
- **Out-of-Scope**: crawl scheduling and target-list generation; `CrawlOrchestrator.crawl`
  removal (`issues/20261106-073205_crawl002_remove-dead-orchestrator-crawl-method.md`, still
  open, disjoint region `orchestrator.py:76-88`); the `max_pages` default drift between
  `crawler.py:66` (200) and `orchestrator.py:74` (500) — recorded as a separate issue
  candidate in Unknowns; conditional-GET behavior itself.
- **Dependencies**: none (issue Dependencies N/A). No co-target overlap with any Frozen Plan in
  this batch (verified by `check_plan_target_overlaps.py` after creation).

## Background
`crawl_site` guards with `if len(visited) >= self._max_pages: break` (`orchestrator.py:104-110`)
and `visited.add(url)` happens in `_drain_queue_to_tasks` before any fetch (`:144`).
`_process_crawl_url_async` can consume that slot without persisting: `fetch_html` returns
`None` (304) → early return (`:177-178`), empty extraction → return (`:184-186`), unsupported
resolved lang → return (`:189-191`), task exception → logged only (`:126-127`). Links are
enqueued only after `save_http` succeeds (`:204-215`), so failures shrink the frontier too.
Additional verified overshoot: the guard runs once per loop iteration, but the drain schedules
every queued URL with no per-URL cap — with `visited=199` and a 50-URL queue at `max_pages=200`,
50 URLs are fetched beyond the budget even on the all-success path. Verified against HEAD
`bdb9bed66` in Step 2 of this cycle.

## Problem
A crawl capped at `max_pages` can persist far fewer pages than the cap (304-heavy or
failure-heavy runs), while also fetching more URLs than the cap allows on success-heavy runs —
the single `visited`-based counter neither protects the operator's page budget nor bounds
scheduling.

## Reason for Change
`max_pages` is the operator-facing bound on crawl output and external-site load; counting
non-persisted fetches against it makes crawls silently under-deliver (issue Reason for Change).

## Implementation Intent
Split the single counter into two: a persisted-page counter (incremented in
`_process_crawl_url_async` right after `save_http` returns) gating the BFS loop on
`max_pages`, and a scheduling cap on `len(visited)` at `max_scheduled = 2 * max_pages`
(fixed internal multiplier) enforced per-URL inside `_drain_queue_to_tasks`. `visited` keeps
its dedup role unchanged. Loop end logs scheduled vs persisted counts.

## Requirements
- `REQ-001`: `crawl_site` owns a per-call budget object (small dataclass or equivalent local
  state passed to the private helpers) holding `persisted` count, `max_persist = max_pages`,
  and `max_scheduled = 2 * max_pages` (module-level constant
  `SCHEDULED_BUDGET_MULTIPLIER = 2`). No new config key (issue Unresolved Question resolved in
  the issue file: fixed multiplier chosen over config key). Budget state is per `crawl_site`
  call — `WebCrawler.crawl` calls `crawl_site` per target URL (`crawler.py:106,116`) and each
  call gets a fresh budget, matching today's per-call `visited` scope.
- `REQ-002`: Loop guards become: (a) `persisted >= max_persist` → WARNING "persisted budget
  reached" + break; (b) `len(visited) >= max_scheduled` → WARNING "scheduling budget reached"
  + break; `_drain_queue_to_tasks` stops dequeuing as soon as `len(visited) >= max_scheduled`
  (per-URL cap, fixing the drain overshoot). The old `len(visited) >= max_pages` guard is
  removed. `visited` dedup semantics, `max_depth` check, and single-fetch-per-URL are preserved
  (issue Constraints).
- `REQ-003`: `_process_crawl_url_async` increments the budget's persisted counter after
  `save_http` returns (`orchestrator.py:204`), before `enqueue_links` (`:215`). Counter
  mutation is safe without locks: single event loop, loop reads only after `asyncio.wait`
  completion points.
- `REQ-004`: At BFS stop (either guard or queue/pending exhaustion), log one summary line
  `BFS stop: scheduled=%d persisted=%d max_pages=%d` so operators see why the crawl stopped
  (issue Required Changes bullet 3).
- `REQ-005`: Tests: replace the two vacuous tests in `tests/rag/ingestion/test_crawler_integration.py`
  (`test_stops_at_max_pages`, `test_max_pages_warning_logged`, `:160-206` — they patch
  `crawl_site` and assert nothing) with real respx/stubbed-fetcher assertions of the new
  semantics; characterization test `test_max_pages_boundary`
  (`tests/rag/ingestion/test_crawler_retry_boundary.py:62-76`, asserts `len(respx.calls) <= 1`
  at `max_pages=1`) must pass unchanged before and after (it pins the all-persisted path,
  where new and old semantics agree).

## Implementation Target Files
**Freeze status**: Frozen (Step 8b validation passed 20261106-104423 — every row `Verified`).

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/ingestion/orchestrator.py` | Modify | Split persisted vs scheduled budgets; per-URL drain cap; persisted increment after `save_http`; loop-stop summary log | REQ-001..REQ-004; AC-1..AC-3 | Guard `:104-110`; `visited.add` pre-fetch `:144`; non-persist early returns `:177-178`, `:184-186`, `:189-191`; exception-only handling `:126-127`; `save_http`/`enqueue_links` order `:204-215` (checked in Step 2) | `tests/rag/ingestion/test_crawler_retry_boundary.py`, `tests/rag/ingestion/test_crawler_integration.py` | Verified |
| `tests/rag/ingestion/test_crawler_retry_boundary.py` | Modify | Keep `test_max_pages_boundary` as characterization; add new persisted-budget unit tests (304-heavy, failure-only, empty-content/lang allowance) | REQ-005; AC-1, AC-2, AC-3 | Existing boundary test at `:62-76` pins scheduled-fetch semantics (`len(respx.calls) <= 1`); respx harness `_get_base_cfg` reusable (checked in Step 2) | itself | Verified |
| `tests/rag/ingestion/test_crawler_integration.py` | Modify | Replace the two vacuous max_pages tests with real behavior assertions | REQ-005; AC-3 | `test_stops_at_max_pages` / `test_max_pages_warning_logged` patch `crawl_site` and assert nothing ("verify the guard exists by checking the source logic", `pass`) at `:160-206` (checked in Step 2) | itself | Verified |
| `docs/21_rag/rag_05_01-configuration-reference.md` | Modify | Update the `max_pages` key description to persisted-page semantics + 2x scheduling cap | REQ-001, REQ-002; AC-4 | Line 34: "`max_pages`: reaching it stops BFS for the site" — no persisted/scheduled distinction (checked in Step 3) | N/A: documentation file, validated by review | Verified |
| `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md` | Modify | Update §2.1.1 BFS-bound wording to the two-counter semantics | REQ-002, REQ-004; AC-4 | §2.1.1 (`:39-45`) describes `max_pages` only as a BFS growth bound (checked in Step 3) | N/A: documentation file, validated by review | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/rag/ingestion/crawler.py` | `crawl_site` call sites per target (`:106,116`); `_max_pages` default at `:66` (200) vs `orchestrator.py:74` (500) drift context | REQ-001 per-call budget scope; UNK-02 |
| `config/crawler.toml` | Existing `max_pages = 200` and its "unvalidated heuristics" comment (`:22-23`) — basis for rejecting a new config key | REQ-001 multiplier decision |
| `scripts/rag/ingestion/crawl_persister.py` | `save_http` success boundary — the exact point the persisted counter increments | REQ-003 |
| `tests/rag/ingestion/test_crawler_retry_boundary.py` | respx mock patterns and `_get_base_cfg` harness for the new tests | REQ-005 |
| `issues/20261106-073205_crawl002_remove-dead-orchestrator-crawl-method.md` | Open issue on the dead `crawl` method (`orchestrator.py:76-88`) — disjoint region, no coordination needed beyond not reviving it | Scope boundary |

## Acceptance Criteria
- AC-1 (REQ-001..REQ-003): A run with N cached (304) URLs and M persistable URLs at
  `max_pages = M` persists all M pages (N ≤ max_pages so the 2x scheduling cap covers them;
  covered by a stubbed-fetch test).
- AC-2 (REQ-002): A failure-only queue (every fetch raises) terminates with at most
  `2 * max_pages` scheduled URLs (covered by a test).
- AC-3 (REQ-002, REQ-005): `test_max_pages_boundary` stays green unchanged; the two vacuous
  integration tests are replaced by assertions that fail on the old code's under-delivery
  scenario and pass on the new code; no URL is fetched twice per run (dedup assertion).
- AC-4 (REQ-001, REQ-002, REQ-004): Both docs describe `max_pages` as persisted-page budget
  with the 2x scheduling cap and the stop summary log.
- AC-5 (REQ-001..REQ-005): `uv run pytest tests/rag/ingestion` passes and changed lines reach
  the `rules/toolchain.md` diff-cover threshold (≥ 90%).

## Tests
- Characterization (pre-change, REQ-005): `test_max_pages_boundary` unchanged — pins that an
  all-persisted crawl at `max_pages=1` makes at most 1 fetch under both old and new semantics.
- REQ-005 new (304-heavy): stub `HttpFetcher.fetch_html` (or respx) so 3 URLs return 304 and 2
  return content, `max_pages=2` → 2 chunk files persisted under `rag-src/`, scheduled ≤ 4.
  Fails today (first 3 × 304 exhausts the budget, 0 persisted).
- REQ-005 new (failure-only): every fetch raises → loop terminates, scheduled ≤ 2 * max_pages,
  persisted = 0, summary log emitted.
- REQ-005 new (allowance paths): empty-content and unsupported-lang URLs consume scheduling
  but not the persisted budget; persisted count still reaches `max_pages`.
- REQ-005 new (dedup pin): a crawl where two pages link to the same URL → exactly one fetch of
  that URL (`len(respx.calls)` equals unique-URL count).
- REQ-005 replaced: `TestMaxPagesBoundaryCondition` rewritten as real async crawls asserting
  the stop WARNING line (persisted vs scheduled wording) via `caplog`.
- Characterization: `max_depth` and external-link filter tests in the same files unchanged and
  green.

## Documentation Impact
REQ-001/REQ-002: `docs/21_rag/rag_05_01-configuration-reference.md` line 34 (`max_pages` key
description) and `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md` §2.1.1 are rewritten to
state that `max_pages` counts persisted pages and scheduling is capped at 2x `max_pages`. No
other doc references found in the Step 3 scan.

## Assumptions
- 304-heavy crawls in practice have N_cached ≤ max_pages (the 2x cap covers them); heavier
  staleness profiles are handled by UNK-01 monitoring rather than a larger multiplier.
- `save_http` returning normally means the page is persisted (no post-save failure path was
  found in `crawl_persister.py` — to be re-confirmed at implementation start).
- The stop-summary log wording does not break `docs/21_rag/rag_05_03-logging.md` categories
  (it reuses the existing crawler logger, no new category).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the fixed 2x scheduling multiplier is adequate for production sites with very high 304 rates | No production crawl statistics on 304/failure ratios | Monitor the new stop-summary log (`scheduled=` vs `persisted=`) after deploy; revisit the constant with the operator if scheduled routinely hits 2x with persisted short of budget | False |
| UNK-02 | `max_pages` default drift: `crawler.py:66` defaults to 200, `orchestrator.py:74` defaults to 500 on the same config dict | None — both locations verified | File a separate issue for default unification (out of scope here); pending user decision on filing | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/ingestion/orchestrator.py` | Modify | Medium | 0 | High (single maintainer) | not applicable (rsynced) |
| `tests/rag/ingestion/test_crawler_retry_boundary.py` | Modify | Low | 1 | High (single maintainer) | not applicable (rsynced) |
| `tests/rag/ingestion/test_crawler_integration.py` | Modify | Low | 0 | High (single maintainer) | not applicable (rsynced) |
| `docs/21_rag/rag_05_01-configuration-reference.md` | Modify | Low | 16 | High (single maintainer) | not applicable (rsynced) |
| `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md` | Modify | Low | 5 | High (single maintainer) | not applicable (rsynced) |

## Design
- Path B classification: intentional behavior change to crawl budget semantics with
  operator-visible output changes (stop log, persisted counts), characterization-first.
- Budget-shape decision: a small internal `@dataclass _CrawlBudget` (`persisted: int`,
  `max_persist: int`, `max_scheduled: int`, `scheduled` derivable from `len(visited)`) created
  in `crawl_site` and passed to `_drain_queue_to_tasks` and `_process_crawl_url_async`:
  chosen over (a) instance attributes (`self._persisted` — cross-`crawl_site`-call state that
  must be reset per call; rejected as lifecycle hazard) and (b) a plain `list[int]` counter
  (opaque; rejected). The budget is private to the orchestrator — no public API change,
  satisfying the issue's "keep the change inside the orchestrator loop" instruction.
- Multiplier decision: `SCHEDULED_BUDGET_MULTIPLIER = 2` module constant, `max_scheduled =
  max_pages * 2` — recorded in the issue's Unresolved Questions as the chosen resolution
  (fixed multiplier over config key): `config/crawler.toml:22-23` already documents the limit
  values as unvalidated heuristics, and a safety-valve bound is not an operator tuning knob;
  a new config key would add surface without measured justification.
- Drain-cap placement: check `len(visited) >= max_scheduled` inside the `while not
  queue.empty()` loop of `_drain_queue_to_tasks` before `visited.add`, in addition to the two
  top-of-loop guards — this is what fixes the verified overshoot (bulk drain with no per-URL
  cap); URLs left in the queue at cap-hit are dropped exactly as today's break drops them.
- Counter visibility: the loop reads `budget.persisted` only after `asyncio.wait`
  FIRST_COMPLETED boundaries; `_process_crawl_url_async` increments after `save_http` on the
  same single-threaded event loop — no lock needed (verified reasoning, pinned by tests).
- `visited` unchanged in role: added at scheduling time (`:144`), guaranteeing the
  no-refetch constraint (`:177-215` fetch path runs once per URL); the persisted counter is
  additive state, not a replacement of dedup.
- Cross-plan coordination: no Frozen Plan targets `orchestrator.py`, either crawler test file,
  `rag_02_02`, or `rag_05_01` (overlap checker output after creation confirms). The open
  crawl002 issue (dead `crawl` method, `:76-88`) is a disjoint region; if implemented first or
  later, this plan's region (`crawl_site` and below) is unaffected either way.
- `scan_change_consumers.py` not run: no persisted schema, public API, or shared-constant
  change; `crawl_site`'s signature is unchanged and the chunk JSON payload shape is untouched.
  Historical analysis (Step 3): churn (30d) 0/1/0/16/5 — module stable, docs active;
  single maintainer throughout. Operational check: inherited from this batch's
  `fuser /opt/llm/db/rag.sqlite` (no holders); crawler runs are operator-scheduled
  (`crawl` command), so deploy timing should avoid an in-flight crawl. Persisted schema check:
  N/A — no DDL.
- Validation quality baseline (Step 5): `radon cc scripts/rag/ingestion/orchestrator.py` — no
  C-or-worse grade (measured this cycle, `radon-CD-exit:1`); `bandit`/`vulture` clean on the
  ingestion package in this batch's scans. `pip-audit` N/A: no dependency change. Diff-cover
  current number not measured; ≥ 90% on changed lines required at implementation per
  `rules/toolchain.md`.

## Implementation steps
1. **Phase 1: Characterization (behavior lock, no production change)**
   - [x] Confirm `test_max_pages_boundary` (`test_crawler_retry_boundary.py:62-76`) and the
     max_depth/external-link tests pass as-is; add the dedup-pin test (passes against current
     code) (REQ-005)
2. **Phase 2: Failing budget tests (RED)**
   - [x] Add 304-heavy, failure-only, and allowance-path tests to
     `tests/rag/ingestion/test_crawler_retry_boundary.py`; rewrite the two vacuous tests in
     `tests/rag/ingestion/test_crawler_integration.py` as real assertions (REQ-005; the new
     semantics tests must fail against current code before Phase 3)
3. **Phase 3: Two-counter budget (GREEN)**
   - [x] Add `_CrawlBudget` + `SCHEDULED_BUDGET_MULTIPLIER`; swap loop guards; per-URL drain
     cap; persisted increment after `save_http`; stop-summary log
     (`scripts/rag/ingestion/orchestrator.py`) (REQ-001..REQ-004)
4. **Phase 4: Documentation & verification & deploy hand-off**
   - [x] Update `docs/21_rag/rag_05_01-configuration-reference.md` (`max_pages` bullet) and
     `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md` §2.1.1 (REQ-001, REQ-002, REQ-004)
   - [x] Run the `rules/toolchain.md` gate sequence on the touched files (pytest targeted +
     `tests/rag/ingestion`, ruff, mypy, lint-imports, bandit, diff-cover ≥ 90%)
   - [ ] Deploy hand-off: after the change is committed and pushed, `scripts/` sync via
     `skills/deploy/SKILL.md` is the user's decision (approval gate); schedule sync to avoid
     an in-flight crawl (Operational check note) (REQ-001..REQ-004)

### Release units
**Unit**: crawl-persisted-budget | **Phases**: 1, 2, 3 | **Reason**: Phase 1 locks current behavior, Phase 2 adds tests that fail against it, and only Phase 3 makes the suite green; splitting any phase out leaves the suite red or the behavior unlocked.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/ingestion/orchestrator.py` | Integration (respx/stubbed fetch) | `uv run pytest tests/rag/ingestion/test_crawler_retry_boundary.py -v` | 304-heavy run persists all M ≤ max_pages pages; failure-only run bounded at 2 * max_pages scheduled |
| `scripts/rag/ingestion/orchestrator.py` | Characterization | `uv run pytest tests/rag/ingestion/test_crawler_retry_boundary.py::test_max_pages_boundary -v` | Green before and after (all-persisted path unchanged) |
| `tests/rag/ingestion/test_crawler_integration.py` | Integration | `uv run pytest tests/rag/ingestion/test_crawler_integration.py -v` | Replaced max_pages tests assert real stop behavior and warning wording via caplog |
| whole `tests/rag/ingestion` | Regression | `uv run pytest tests/rag/ingestion` | All ingestion tests green |
| `scripts/` touched files | Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll` | Clean, no new findings |
| changed lines | Coverage | `uv run coverage run -m pytest tests/` then `uv run coverage xml` and `uv run diff-cover coverage.xml --compare-branch=master` | ≥ 90% on changed lines |

## Risks
- **Risk**: redefining `max_pages` semantics changes crawl output volume for existing operator
  expectations (a 304-heavy crawl now keeps going) → **Mitigation**: bounded by the 2x
  scheduling cap (AC-2); docs updated in the same change (AC-4); UNK-01 monitoring via the new
  stop-summary log.
- **Risk**: replacing the vacuous tests changes what the suite pins and could mask a
  regression they nominally covered → **Mitigation**: they assert nothing today (verified), so
  nothing is lost; replacements assert the new guards strictly (Phase 2 RED against old code).
- **Risk**: async counter visibility races between tasks and the loop → **Mitigation**: reads
  occur only at `asyncio.wait` boundaries on a single event loop (Design note); the 304-heavy
  and failure-only tests would surface any off-by-one behaviorally.
- **Risk**: interaction with the open crawl002 issue region → **Mitigation**: disjoint methods
  (`crawl` vs `crawl_site` chain); either implementation order works (Design note).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Characterization + dedup pin | Completed | 2026-11-06 | 2026-11-06 | REQ-005 |
| 2 | New budget tests (RED) + replace vacuous tests | Completed | 2026-11-06 | 2026-11-06 | REQ-005 |
| 3 | Two-counter budget in `orchestrator.py` | Completed | 2026-11-06 | 2026-11-06 | REQ-001..REQ-004 |
| 4 | Docs update + gate sequence + deploy hand-off | Completed | 2026-11-06 | 2026-11-06 | REQ-001..REQ-004; deploy hand-off pending push |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocker recorded at plan creation | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261106-154603_01_scripts_rag_ingestion_orchestrator.py.md` | 3 | Procedure | Completed | — | — |
| `implementations/20261106-154603_02_tests_rag_ingestion_test_crawler_retry_boundary.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261106-154603_03_tests_rag_ingestion_test_crawler_integration.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261106-154603_04_docs_21_rag_rag_05_01-configuration-reference.md.md` | 4 | Procedure | Completed | — | — |
| `implementations/20261106-154603_05_docs_21_rag_rag_02_02_ingestion_pipeline-crawler.md.md` | 4 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261106-073538_raging009_crawl-max-pages-pending-tasks.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261106-104423
- **Related target files**: `scripts/rag/ingestion/orchestrator.py`,
  `tests/rag/ingestion/test_crawler_retry_boundary.py`,
  `tests/rag/ingestion/test_crawler_integration.py`,
  `docs/21_rag/rag_05_01-configuration-reference.md`,
  `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes bullets 1-2; Unresolved Question resolved (fixed multiplier); budget defaults verified at `orchestrator.py:74`, `crawler.py:66` (checked in Step 2) | `scripts/rag/ingestion/orchestrator.py` | Phase 3 | AC-1, AC-4 | 304-heavy + failure-only tests | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes bullet 2 + Constraints bullets 1-3; guard and drain verified at `:104-110`, `:144` (checked in Step 2) | `scripts/rag/ingestion/orchestrator.py` | Phase 3 | AC-2, AC-3, AC-4 | failure-only bound test + dedup pin | Confirmed by repository evidence |
| REQ-003 | Issue Summary non-persist list; early returns verified at `:177-191`, save order at `:204-215` (checked in Step 2) | `scripts/rag/ingestion/orchestrator.py` | Phase 3 | AC-1 | 304-heavy + allowance tests | Confirmed by repository evidence |
| REQ-004 | Issue Required Changes bullet 3 | `scripts/rag/ingestion/orchestrator.py` | Phase 3 | AC-4 | replaced warning-wording tests (caplog) | Explicit in issue |
| REQ-005 | Issue Testing Expectations + Acceptance Criteria; vacuous tests and boundary test verified at `test_crawler_integration.py:160-206`, `test_crawler_retry_boundary.py:62-76` (checked in Step 2) | `tests/rag/ingestion/test_crawler_retry_boundary.py`, `tests/rag/ingestion/test_crawler_integration.py` | Phase 1, 2 | AC-1..AC-3, AC-5 | New + replaced + characterization tests | Explicit in issue (corrected: claimed max_pages coverage was partly vacuous) |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261106-154603 -->
