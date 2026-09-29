## Goal
Change `WebCrawler`'s `max_pages` fallback default from `500` to `200`, matching
the deployed `config/crawler.toml` value and every other fallback in the same
constructor (REQ-001).

## Scope
- **In-Scope**: The single `cfg.get("max_pages", 500)` call in this target
  file's `__init__` (line 66).
- **Out-of-Scope**: The separate `skip_nofollow` default mismatch (`False` in
  code vs. `True` deployed) — a related but distinct finding, not part of this
  Plan; any other fallback default in this file; `max_depth`/`max_pages`'s
  actual values or empirical tuning; adding the regression test (covered by the
  sibling implementation procedure document for
  `tests/rag/ingestion/test_crawler_integration.py`, seq 02 of this Plan);
  removing the NC-035 governance entry (seq 03 of this Plan).

## Assumptions
- Every other `cfg.get(key, default)` fallback in this same constructor
  (`fetch_timeout`, `crawl_concurrency`, `sqlite_timeout`,
  `sqlite_busy_timeout_ms`, `skip_external`) already mirrors its deployed
  `config/crawler.toml` value exactly (Plan Background) — this change brings
  `max_pages` into the same convention, not a new one.

## Design decisions
- Change only the literal default value (`500` → `200`); do not touch the
  `cfg.get()` call's structure, the surrounding fallback pattern, or any other
  line — per `skills/python-design`, the smallest change that fixes the
  confirmed bug (a single outlier constant), consistent with every sibling
  fallback in this same file.

## Alternatives considered
- Remove the fallback default entirely (require `max_pages` to always be
  present in config) — rejected: out of this Plan's scope (Plan Risks: "the
  fallback pattern itself ... is out of scope; only its value is corrected");
  changes the file's error-handling contract beyond what this bug fix requires.
- Read the default from `config/crawler.toml` itself at import time instead of
  hardcoding `200` — rejected: no other fallback in this file does this, and
  introducing a new pattern for one value would be inconsistent with the
  established, already-accepted convention (Plan Design).

## Implementation
### Target file
`scripts/rag/ingestion/crawler.py`

### Procedure
1. Open `scripts/rag/ingestion/crawler.py` and locate line 66 (confirmed
   unchanged at this line by direct read during this document's generation).
2. Change the fallback default literal from `500` to `200`.

### Method
Direct text replacement (single literal value in one existing line) — no new
imports, no change to the surrounding constructor logic.

### Details
Current line 66 (confirmed via direct read):
```
        self._max_pages: int = int(cfg.get("max_pages", 500))
```

New line 66:
```
        self._max_pages: int = int(cfg.get("max_pages", 200))
```

Do not modify any other line in `__init__` or elsewhere in this file.

## Compatibility considerations
N/A: internal constructor fallback default only, not a public interface or
contract change. Only affects behavior when `max_pages` is absent from config
(not the common, already-configured case) — the deployed
`config/crawler.toml` always sets `max_pages = 200` explicitly, so production
behavior is unchanged; this only corrects what happens if that key were ever
removed or misconfigured.

## Security considerations
N/A: no credentials, data-handling, or security-relevant logic change.

## Rollback considerations
Single-line revert via `git revert`/`git checkout` of this file if needed; no
data migration or schema state to unwind.

## Validation plan
- `uv run ruff format scripts/rag/ingestion/crawler.py` and
  `uv run ruff check scripts/rag/ingestion/crawler.py` — formatting/lint.
- `uv run mypy scripts/rag/ingestion/crawler.py` — type check (no type change
  expected; the literal remains an `int`).
- `PYTHONPATH=scripts uv run lint-imports` — architecture/import-boundary
  check (no import change expected).
- `uv run bandit scripts/rag/ingestion/crawler.py` — security scan (no new
  finding expected).
- `uv run pytest tests/rag/ingestion/test_crawler_integration.py -v` —
  targeted; confirm the sibling document's new fallback-default test passes
  and no existing test in the file regresses.
- `uv run pytest -q` — full suite, once, per `rules/toolchain.md` (REQ-002).

## Completion criteria
- `scripts/rag/ingestion/crawler.py`'s `max_pages` fallback default is `200`.
- No other line in this file is changed.
- All validation steps above pass.

## Out of scope
- Adding the regression test — handled by the sibling implementation
  procedure document for `tests/rag/ingestion/test_crawler_integration.py`
  (seq 02 of this Plan).
- Removing the NC-035 entry from
  `docs/00_governance/governance_03_issue-and-uncertainty-management.md` —
  handled by the sibling implementation procedure document for that file (seq
  03 of this Plan).
- The separate `skip_nofollow` default mismatch and any empirical
  `max_depth`/`max_pages` tuning.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Change the fallback default per Implementation > Procedure/Method/Details | Completed | 20260929-152533 | 20260929-152533 | max_pages fallback default changed 500->200; diff scoped to 1 line |
| 2 | Run non-test validation (ruff/mypy/lint-imports/bandit) | Completed | 20260929-152533 | 20260929-152533 | ruff/lint-imports/bandit run; pre-existing unrelated mypy unused-type-ignore and lint-imports shared->agent violation confirmed via git stash comparison; bandit clean. Test execution deferred to sibling seq02 document. |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260927-211418_nc035_fix-crawler-max_pages-default-mismatch-and-confirm-limit-rationale.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260928-164033_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260929-152211
- **Related target files**: scripts/rag/ingestion/crawler.py