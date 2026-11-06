## Goal

Add persisted-budget unit tests (`REQ-005`) to `test_crawler_retry_boundary.py`:
304-heavy, failure-only, and allowance-path cases that fail against current code and
pass after the two-counter budget lands. Keep `test_max_pages_boundary` as an
unchanged characterization test.

## Scope
**Release unit**: crawl-persisted-budget (Plan Phase 2)

## Assumptions
- The respx harness `_get_base_cfg(tmp_path)` (this file, `_get_base_cfg`) is reusable;
  set `cfg["max_pages"]` per case.
- Content strings produce extractable text above `min_chunk` so pages persist (the
  304-heavy case needs exactly 2 persisted pages).
- `test_max_pages_boundary` pins the all-persisted path where old and new semantics
  agree (`len(respx.calls) <= 1` at `max_pages=1`); it must stay green unchanged.

## Design decisions
- **Characterization first, then RED.** Confirm `test_max_pages_boundary` and the
  max_depth/external-link tests pass as-is (Phase 1), then add the budget tests that
  fail against current code (Phase 2).
- **Assert on persisted artifacts and fetch counts.** Use `respx` routes and assert
  on files written under `tmp_path` (the `rag_src_dir`) for persistence, and on
  `len(respx.calls)` / route `.call_count` for scheduling bounds.
- **Dedup pin lives here too.** A two-pages-link-to-same-URL case asserting exactly
  one fetch of the shared URL (`len(respx.calls)` equals unique-URL count) pins the
  `visited` dedup contract under the new budget.

## Alternatives considered
- Stubbing `HttpFetcher.fetch_html` directly instead of respx: valid but the existing
  respx harness (`_get_base_cfg`, `respx.get(...).mock(...)`) is reusable and already
  exercises the real fetch path. Used respx.

## Implementation
### Target file
- `tests/rag/ingestion/test_crawler_retry_boundary.py`

### Procedure
1. Confirm `test_max_pages_boundary`, `test_retry_on_503_then_succeeds`,
   `test_skip_304_response`, and `test_external_link_filter` pass as-is.
2. Add the three budget test functions (304-heavy, failure-only, allowance paths) and
   the dedup-pin test.
3. Re-run after the `orchestrator.py` change (Phase 3) to confirm GREEN.

### Method
- **304-heavy (fails today):** five routes; three return `Response(304)`, two return
  200 with `min_chunk`-satisfying text. `cfg["max_pages"] = 2`. After
  `await crawler.crawl_site("http://example.com", "en")`, assert exactly 2 chunk
  JSON files exist under `tmp_path` and that scheduled fetches ≤ `2 * max_pages`.
  Today the first 3 × 304 exhaust the `visited` counter, so 0 persist → assertion fails.
- **failure-only (fails today):** every route returns `Response(500)` (or raises).
  `cfg["max_pages"] = 2`. Assert the crawl terminates, `len(respx.calls) <= 2 * max_pages`,
  0 persisted files, and the `BFS stop:` summary log was emitted (via `caplog`).
- **allowance paths:** a route whose content is empty and one whose resolved lang is
  unsupported (e.g. a page whose text resolves outside `{en, ja}`) consume scheduling
  but not the persisted budget; a following valid page still reaches `max_pages`
  persisted. Assert persisted count reaches `max_pages`.
- **dedup pin (passes today):** two source pages both link to the same third URL;
  assert `len(respx.calls)` for that URL equals 1.

### Details
- For the empty-content and unsupported-lang allowance cases, drive them through the
  real extract/resolver by returning HTML whose body text is empty, and whose text
  resolves to an unsupported language; keep `min_chunk` low enough that a valid page
  in the same run persists. If forcing an unsupported resolved lang is impractical via
  respx, stub `LanguageResolver.resolve_lang` for that case only.
- `caplog` for the summary log: use
  `caplog.at_level(logging.INFO, logger="rag.ingestion.orchestrator")`; if capture is
  empty because the module logger's propagation differs, attach `caplog.handler` to
  `logging.getLogger("rag.ingestion.orchestrator")` directly (same pattern as the
  production-security-regression test).
- Count persisted files with `list(tmp_path.glob("*-*.json"))` (the persister writes
  `{ts}-{slug}-{hash}.json`); assert `len == expected_persisted`.
- Do not modify `test_max_pages_boundary`, `test_retry_on_503_then_succeeds`,
  `test_skip_304_response`, or `test_external_link_filter`.

## Compatibility considerations
This document adds tests only; it does not change production behavior. The new tests
fail against current code (Phase 2 RED) and go GREEN after the orchestrator change
(Phase 3). `test_max_pages_boundary` stays green before and after.

## Security considerations
N/A: test-only additions, no input handling or credential change.

## Rollback considerations
Revert the commit to this test file. The new test functions are additive.

## Validation plan
- `test_max_pages_boundary` and existing boundary tests pass as-is (Phase 1).
- Budget tests fail against current code, pass after Phase 3.
- `uv run pytest tests/rag/ingestion/test_crawler_retry_boundary.py -v` passes.
- `uv run pytest tests/rag/ingestion` passes.
- Static gates: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages
  scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`,
  `uv run bandit -r scripts/ -c pyproject.toml -ll` — clean.

## Completion criteria
- 304-heavy, failure-only, allowance-path, and dedup-pin tests exist; they fail
  against current code and pass after the two-counter budget.
- `test_max_pages_boundary` remains green unchanged.
- Full ingestion suite green; static gates clean.

## Out of Scope
- Replacing the vacuous `test_crawler_integration.py` max_pages tests (companion
  document `test_crawler_integration.py`).
- Any production-file change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Characterization + dedup pin (Phase 1) | Pending | — | — | REQ-005 |
| 2 | New budget tests (RED) | Pending | — | — | REQ-005 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-005`
- **Source issue**: `issues/20261106-073538_raging009_crawl-max-pages-pending-tasks.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261106-104423_raging009_crawl-max-pages-pending-tasks.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-154603
- **Related target files**: `tests/rag/ingestion/test_crawler_retry_boundary.py`
