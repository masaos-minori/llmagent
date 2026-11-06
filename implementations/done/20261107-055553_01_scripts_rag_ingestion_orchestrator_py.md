## Goal

- Align `CrawlOrchestrator`'s key-absent `max_pages` fallback with `WebCrawler`'s (200) so both consumers of
  the same crawler config dict default identically (REQ-001: fallback literal 500 → 200; REQ-002: pin both
  consumers in the existing fallback test).

## Scope
**Release unit**: fallback alignment

- One integer literal change in `CrawlOrchestrator.__init__`, plus its companion test extension in
  `tests/rag/ingestion/test_crawler_integration.py`. Test lands first (Phase 1, RED), then the literal change
  (Phase 2) — one release unit.

## Assumptions

- No deployed or test environment relies on the 500 key-absent fallback (Plan A-001: deployed TOML sets 200;
  the `mock_config` fixture passes `max_pages` explicitly as 500 — an explicit key, unaffected).
- Key-present behavior is unchanged; the 009 Plan's `_CrawlBudget` region in `crawl_site` is untouched.

## Design decisions

- Literal alignment only: no shared-constants module (overkill for one integer; config-isolation ADR pattern).
- `WebCrawler` and `crawler.py` are unchanged — the orchestrator's own fallback is the divergent side.

## Alternatives considered

- Unifying fallbacks in a shared constants module: rejected by the Plan (overkill, coupling).
- Removing `WebCrawler._max_pages`: rejected (pinned by the nc035 regression test).

## Implementation
### Target file
`scripts/rag/ingestion/orchestrator.py`

### Procedure
1. Extend the companion fallback test first (see Companion test files) and confirm it is RED with
   `500 == 200` failure on the orchestrator assertion (Plan Phase 1).
2. Change the fallback literal (Plan Phase 2, REQ-001).
3. Re-run the companion test: green.

### Method
- In `CrawlOrchestrator.__init__` (currently line 89), change
  `int(config.get("max_pages", 500))` to `int(config.get("max_pages", 200))`.
  Nothing else in the file changes — no other fallback default, and the `crawl_site`/budget region is untouched.

### Details
- Single literal; type annotation and surrounding lines stay identical. `crawler.py` already defaults to 200
  (`int(cfg.get("max_pages", 200))`, currently line 67) and passes the same dict via
  `CrawlOrchestrator(config=self.config)` — reference only, not modified.

### Companion test files
- `tests/rag/ingestion/test_crawler_integration.py`
  - Procedure: in `TestMaxPagesBoundaryCondition.test_max_pages_fallback_default`, add one assertion after
    the existing `crawler._max_pages == 200` line: `assert crawler.orchestrator._max_pages == 200` (the
    `WebCrawler.orchestrator` attribute is constructed by `WebCrawler.__init__`); update the docstring to
    cover both consumers.
  - Validation: `uv run pytest tests/rag/ingestion/test_crawler_integration.py -v` — RED (500 != 200) before
    step 2 of Procedure, green after.

## Compatibility considerations

- Zero behavior change for the deployed (key-present) path; only the key-absent default changes 500 → 200.
- The config-comment correction is a separate target row (seq03, `config/crawler.toml`).

## Security considerations

- N/A: integer default alignment; no trust-boundary change.

## Rollback considerations

- N/A: revert the commit (single literal + one assertion).

## Validation plan

- `uv run pytest tests/rag/ingestion/test_crawler_integration.py -v` — RED before the literal change, green
  after (AC-003).
- `uv run pytest tests/rag/ingestion` — 009 budget tests (`test_stops_at_max_pages`,
  `test_max_pages_warning_logged`, `test_crawler_retry_boundary.py`) unaffected (key-present behavior).
- Completion gates per `rules/toolchain.md`: ruff, ruff format, mypy, lint-imports, bandit, diff-cover ≥90%,
  full `uv run pytest`.
- Gate baselines: `uv run radon cc scripts/rag/ingestion/orchestrator.py -n B` (no new C+), `uv run vulture
  scripts/rag/ingestion/orchestrator.py` (no new finding).

## Completion criteria

- AC-003: constructing `WebCrawler` without `max_pages` yields `_max_pages == 200` and
  `orchestrator._max_pages == 200`.
- AC-002: key-present behavior unchanged (budget persists 200 / schedules 400 when the key is present — 009
  tests green).
- Only the constructor literal changed in the target file (Boundary row of the Plan's Acceptance Criteria).

## Out of Scope

- `max_depth`/`max_pages` rationale question (nc035 governance half), `skip_nofollow` divergence.
- `crawl_site`/`_CrawlBudget` region (009 Plan's frozen region).
- `config/crawler.toml` NOTE comment (own document, seq03).
- Deploy: Phase 3 hands off to the user-approval deploy step (`scripts/` change).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend companion test `test_max_pages_fallback_default` with the orchestrator assertion; confirm expected RED (Plan Phase 1) | Completed | 2026-11-07 | 2026-11-07 | Release unit "fallback alignment": intentionally RED until step 2 |
| 2 | Change fallback literal 500 → 200 in `CrawlOrchestrator.__init__` (Plan Phase 2, REQ-001) | Completed | 2026-11-07 | 2026-11-07 | — |
| 3 | Re-run companion test + `tests/rag/ingestion`: all green | Completed | 2026-11-07 | 2026-11-07 | — |
| 4 | Run the validation sequence (`rules/toolchain.md`) incl. radon/vulture baselines and diff-cover ≥90% | Completed | 2026-11-07 | 2026-11-07 | — |

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
- **Requirement ID**: REQ-001 (fallback literal alignment), REQ-002 (both-consumer fallback pin test)
- **Source issue**: issues/done/20261106-110944_ragfix002_orchestrator-max-pages-default.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-052809_ragfix002_orchestrator-max-pages-default.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-055553
- **Related target files**: `scripts/rag/ingestion/orchestrator.py`, `tests/rag/ingestion/test_crawler_integration.py`
