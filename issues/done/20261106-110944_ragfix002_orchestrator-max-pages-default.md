# Finish the max_pages fallback-default fix in CrawlOrchestrator

## Priority
Medium

## Summary
`CrawlOrchestrator` still defaults `max_pages` to 500 when the key is absent from the
crawler config, while `WebCrawler` now defaults it to 200. Unify the remaining stale
fallback so both consumers of the same config dict agree, mirroring the deployed
`config/crawler.toml` value (200).

## Background
Archived issue `issues/done/20260927-211418_nc035_fix-crawler-max_pages-default-mismatch-and-confirm-limit-rationale.md`
fixed `crawler.py`'s `cfg.get("max_pages", 500)` fallback to `200` (confirmed in current
source: `scripts/rag/ingestion/crawler.py:66`). Its scope was `crawler.py` only. Found
during verification of `issues/20261106-073538_raging009_crawl-max-pages-pending-tasks.md`
(recorded as UNK-02 in `plans/20261106-104423_raging009_crawl-max-pages-pending-tasks.md`):
`scripts/rag/ingestion/orchestrator.py:74` reads the same raw config dict with
`config.get("max_pages", 500)` — the nc035 fix left this second fallback untouched. The
nc035 reasoning applies unchanged: every sibling fallback in these modules mirrors its
deployed config value; `orchestrator.py`'s 500 is a stale leftover.

## Problem
With `max_pages` absent from `config/crawler.toml`, `WebCrawler._max_pages` says 200 while
the BFS guard in `CrawlOrchestrator.crawl_site` actually enforces 500 — a silent 2.5x
behavior difference between the component that reports the limit and the component that
applies it, only on the key-absent fallback path (the deployed key is set to 200 today).

## Reason for Change
Same confirmed-bug class nc035 fixed, one call-site remaining; leaving it makes the
"fallback mirrors deployed value" convention half-applied and re-arms the mismatch if the
key is ever removed or overridden per-target.

## Implementation Intent
Change the `orchestrator.py` constructor fallback from 500 to 200 so both consumers default
identically. Minimal one-value change plus its test; no behavior change when the key is
present.

## Target Files or Areas
- `scripts/rag/ingestion/orchestrator.py` (constructor fallback)
- `tests/rag/ingestion/` crawler tests (fallback-default assertion)

## Required Changes
- Change `config.get("max_pages", 500)` to `config.get("max_pages", 200)` in
  `CrawlOrchestrator.__init__`.
- Add a unit test: constructing the orchestrator (or WebCrawler) with `max_pages` absent
  yields 200 in both `WebCrawler._max_pages` and the orchestrator guard value.

## Constraints
- Preserve behavior for deployments where the key is present (the common case).
- Do not touch any other fallback default (including `skip_nofollow`, still out of scope per
  nc035).
- Do not change the deployed `config/crawler.toml` value.

## Acceptance Criteria
- `orchestrator.py`'s `max_pages` fallback is 200.
- A test asserts the key-absent fallback produces 200 for both consumers.
- `uv run pytest tests/rag/ingestion` passes with no regression.

## Testing Expectations
- Unit test for the key-absent fallback value on both `WebCrawler` and `CrawlOrchestrator`.
- Targeted run then `uv run pytest tests/rag/ingestion` per `rules/toolchain.md`.

## Documentation Impact
N/A: no doc states the fallback defaults; `docs/21_rag/rag_05_01-configuration-reference.md`
documents the deployed key, not code fallbacks. The 3/200 rationale question remains
tracked by nc035's governance entry and is unchanged here.

## Out of Scope
- The `max_depth=3` / `max_pages=200` rationale question (nc035's open half).
- The `skip_nofollow` default divergence.
- The persisted-vs-scheduled budget redesign (planned in
  `plans/20261106-104423_raging009_crawl-max-pages-pending-tasks.md`).

## Dependencies
- `issues/done/20260927-211418_nc035_fix-crawler-max_pages-default-mismatch-and-confirm-limit-rationale.md`
  — completed half of this fix (crawler.py); blocks: none, this issue completes it.
- `plans/20261106-104423_raging009_crawl-max-pages-pending-tasks.md` — co-targets
  `orchestrator.py` (constructor line vs its `crawl_site`/drain region; disjoint). Implement
  either order; if the 009 Plan lands first, re-verify the fallback line still exists.
  depends on ordering: none required.

## Unresolved Questions
- N/A: none.

## AI Implementation Instruction
One-value fallback change plus one test. Do not redesign budget semantics in the same diff;
keep the 009 Plan's region untouched.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261106-104423_raging009_crawl-max-pages-pending-tasks.md` (UNK-02)
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261106-110944
- **Related target files**: `scripts/rag/ingestion/orchestrator.py`, `tests/rag/ingestion/`
