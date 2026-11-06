## Goal
- Surface a missing or empty `rag_db_path` at crawler startup as a clear, single error signal instead of letting an uncaught `ValueError` propagate per crawled URL and silently drop every HTTP URL in a site crawl.

## Priority
Medium

## Scope
- **In-Scope**:
  - Provide a clear startup signal when `rag_db_path` is unset or empty.
  - Prevent the per-URL uncaught `ValueError` from failing each fetch task.
  - Keep the conditional-header cache lookup working correctly when `rag_db_path` IS configured.
- **Out-of-Scope**:
  - Changing the SQLite schema or the `documents` table.
  - Changing where `rag_db_path` is read from config.
  - Reusing a single DB connection across the session (see crawl004).
  - robots.txt or rate-limit policy.
- **Dependencies**: `N/A: none`

## Background
`HttpFetcher.get_conditional_headers` looks up cached `etag`/`last_modified` before each fetch. It opens a connection via `SQLiteHelper(db_path=self._rag_db_path, ...)` inside `except (sqlite3.OperationalError, sqlite3.DatabaseError)`. `SQLiteHelper._connect` raises `ValueError` when `not self._db_path`.

## Problem
`ValueError` is not in the caught tuple, so an empty/misconfigured `rag_db_path` propagates out of `get_conditional_headers`. In `_process_crawl_url_async` this fails the individual URL task and is only logged as "Crawl task error" by the orchestrator's `asyncio.wait` exception handler. Net effect: when `rag_db_path` is unset, every HTTP URL is dropped and the site crawl produces no documents, with no startup signal that the DB is misconfigured. Test configs use `""` or omit the key, so the failure mode is reachable.

## Reason for Change
A misconfigured DB currently fails silently at scale (every URL) rather than loudly at startup. Operators get no indication that the crawl produced nothing because of a missing path, and the root cause is buried in per-task error logs.

## Implementation Intent
Add a clear startup signal for an empty `rag_db_path` without changing the construction contract of `HttpFetcher` or `WebCrawler`. The issue's title asks for "fail fast at crawler startup"; the plan recommends achieving that via a preflight/validation step at the actual crawl entry (`main()`) or a dedicated pre-BFS validation method, rather than raising inside `__init__`, because raising in `__init__` has a large test blast radius (see Unknowns). If a strict constructor raise is preferred, the affected tests must be updated to supply a non-empty `rag_db_path`. As a safety net regardless of the chosen mechanism, `get_conditional_headers` should also absorb the `ValueError` (and any other non-DB-error) so a single bad path cannot crash the whole crawl, logging once.

## Requirements
- `REQ-001`: When `rag_db_path` is empty/unset, the crawler emits exactly one clear startup error indicating the DB is misconfigured, before or at the start of BFS.
- `REQ-002`: An empty `rag_db_path` no longer causes an uncaught `ValueError` to propagate from `get_conditional_headers` into the per-URL task exception path.
- `REQ-003`: When `rag_db_path` is configured to a valid path, conditional-header lookups continue to work unchanged.
- `REQ-004`: Existing tests that construct `HttpFetcher`/`WebCrawler` with an empty or omitted `rag_db_path` continue to pass (no constructor-contract regression).

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/ingestion/http_fetcher.py` | Modify | Absorb the `ValueError` from `SQLiteHelper` in `get_conditional_headers` (add `ValueError` to the caught tuple or wrap the connection open) and emit a single deduped startup warning when `self._rag_db_path` is empty; keep returning `{}` on failure (REQ-002, REQ-003) | REQ-002 | `get_conditional_headers` catches only `(sqlite3.OperationalError, sqlite3.DatabaseError)`; `SQLiteHelper._connect` raises `ValueError` on empty path (verified) | Existing integration tests | Verified |
| `scripts/rag/ingestion/crawler.py` | Modify | Add a pre-BFS startup validation that raises/logs a clear error when `rag_db_path` is empty, called once at crawl startup (REQ-001, REQ-004) | REQ-001 | `WebCrawler.__init__` reads `rag_db_path` with `""` default and wires `HttpFetcher`; `main()` is the real startup entry (verified) | Existing crawler tests | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/db/helper.py` | Owns `SQLiteHelper._connect`, which raises `ValueError` on empty `_db_path`; read to match the exact exception type and message contract (REQ-002) | `scripts/rag/ingestion/http_fetcher.py` |
| `scripts/rag/ingestion/orchestrator.py` | Owns `_process_crawl_url_async` and the `asyncio.wait` exception handler that currently masks the failure as "Crawl task error"; read to confirm the propagation path and that the fix removes it (REQ-001, REQ-002) | `scripts/rag/ingestion/http_fetcher.py`, `scripts/rag/ingestion/crawler.py` |

## Acceptance Criteria
- `REQ-001`: Constructing/starting a crawler with an empty `rag_db_path` produces one clear startup error naming the misconfiguration.
- `REQ-002`: With an empty `rag_db_path`, `get_conditional_headers` returns `{}` (or raises a caught, logged error) instead of propagating `ValueError`.
- `REQ-003`: With a valid `rag_db_path`, conditional headers are still returned from the cache.
- `REQ-004`: The existing `HttpFetcher`/`WebCrawler` tests that omit or blank `rag_db_path` still pass.

## Tests
- Unit test: `get_conditional_headers` with an empty `rag_db_path` does not raise `ValueError` and returns `{}` (REQ-002).
- Startup test: starting a crawl with an empty `rag_db_path` emits the clear startup error (REQ-001).
- Regression test: a valid `rag_db_path` still yields conditional headers (REQ-003).
- `ruff` / `mypy` clean on touched files (REQ-004).

## Documentation Impact
`N/A: the DB path config is not documented in `docs/*.md``; if a config note describes `rag_db_path`, update only the startup-validation behavior.

## Assumptions
- `rag_db_path` is expected to be a filesystem path string; "empty" means `""` or an unset config key.
- A configured-but-nonexistent path is a separate concern (SQLite would raise `OperationalError`, already handled); this issue targets the unset/empty case.
- `main()` is the real crawler startup for production; tests construct `WebCrawler` directly, so a constructor raise would break them.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Fail-fast location: raise in `HttpFetcher.__init__`/`WebCrawler.__init__` versus a startup preflight in `main()`/a pre-BFS validate method. Raising in `__init__` gives the earliest signal but breaks ≥3 integration tests that build `HttpFetcher` with bare `mock_config` (no `rag_db_path`) and several `WebCrawler` tests. | Blast radius measured: `HttpFetcher(` appears in 4 test sites, `WebCrawler(` in 12+ test sites; some set `rag_db_path`, some do not. | Recommended: emit the clear startup error via a pre-BFS validation (e.g. a `validate_config()` method called once before BFS, or a check in `main()`), and additionally absorb the `ValueError` in `get_conditional_headers` as a safety net. This satisfies the issue's "clear startup signal" intent without a constructor-contract change. Constructor raise accepted only if reviewer mandates it and tests are updated accordingly. Non-blocking. | False |
| UNK-02 | Whether the startup signal should be a hard `raise` (true fail-fast, aborts the process) versus a logged error plus graceful empty result. The issue title says "fail-fast"; safe degradation avoids crashing a partially-configured run. | None required; both verified feasible. | Prefer a hard raise at `main()` startup (true fail-fast) since `main()` is not exercised by unit tests; keep the `get_conditional_headers` absorption as the non-crashing safety net. Non-blocking. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/ingestion/http_fetcher.py` | Modify | Medium (referenced by 12+ test sites via WebCrawler; constructor contract must be preserved) | N/A | N/A | not applicable (rsynced) |
| `scripts/rag/ingestion/crawler.py` | Modify | Low (startup preflight; `main()` not covered by unit tests) | N/A | N/A | not applicable (rsynced) |

## Design
Current flow: `WebCrawler.__init__` (line 73) and `HttpFetcher.__init__` (line 37) both
default `rag_db_path` to `""`. On each fetch, `_process_crawl_url_async` calls
`get_conditional_headers(url)`, which opens `SQLiteHelper(db_path="")`. `SQLiteHelper._connect`
raises `ValueError("..._db_path is not configured ...")` because `not self._db_path`. That
`ValueError` is not in the `except (sqlite3.OperationalError, sqlite3.DatabaseError)` tuple,
so it escapes `get_conditional_headers`, becomes the task exception, and is logged only as
"Crawl task error" by the orchestrator's `asyncio.wait` handler. Every URL fails; the site
produces nothing; there is no startup signal.

**Recommended design (UNK-01, UNK-02):**
1. In `get_conditional_headers`, broaden the safety net: catch `ValueError` in addition to
   the SQLite errors (or wrap the `SQLiteHelper(...).open(...)` call in its own try/except),
   log once (deduped by a flag so it prints a single time per process), and return `{}`. This
   guarantees a bad path can never crash the whole crawl (REQ-002) while preserving correct
   behavior when the path is valid (REQ-003).
2. Add a startup preflight that produces the clear, single error the issue asks for. Prefer a
   dedicated validation invoked once before BFS begins (e.g. `WebCrawler.validate_config()`
   called at the top of `crawl()`, or a check inside `main()` before `crawler.crawl()` runs).
   Raise a clear `ValueError`/`RuntimeError` naming `rag_db_path` so production aborts loudly
   (REQ-001, REQ-002). This avoids changing the `__init__` contract that many unit tests rely
   on (REQ-004).
3. Do NOT move the validation into `HttpFetcher.__init__` unless a reviewer explicitly requires
   a constructor raise; that path breaks ≥3 integration tests that build the fetcher with a
   bare `mock_config`.

This keeps the fix low-blast-radius, preserves the conditional-header cache for valid configs,
and converts a silent per-URL collapse into a loud, single startup signal.

## Implementation steps
1. **Phase 1: Safety net in `get_conditional_headers`** (`scripts/rag/ingestion/http_fetcher.py`, REQ-002, REQ-003)
   - [ ] Wrap the `SQLiteHelper(...).open(...)` block so a `ValueError` (empty path) is caught alongside the SQLite errors.
   - [ ] Log a single deduped warning when `self._rag_db_path` is empty (module-level or instance-level `_logged_empty_path` flag), then return `{}`.
   - [ ] Confirm the valid-path branch (returning etag/last_modified headers) is unchanged.
2. **Phase 2: Startup preflight** (`scripts/rag/ingestion/crawler.py`, REQ-001, REQ-004)
   - [ ] Add a pre-BFS validation that raises a clear error naming `rag_db_path` when it is empty/unset, invoked once before BFS starts (top of `crawl()` or in `main()`).
   - [ ] Ensure the validation does not run during unit construction that intentionally blanks the path (keep it at the startup/BFS boundary, not `__init__`).
3. **Phase 3: Verification & commit** (REQ-003, REQ-004)
   - [ ] Run `uv run ruff format` and `uv run ruff check` on both touched files; confirm clean.
   - [ ] Run `uv run mypy --no-namespace-packages scripts/`; confirm no new errors.
   - [ ] Run the crawler/fetcher test suite (`tests/rag/ingestion/`); confirm all pass, including tests that blank `rag_db_path` (REQ-004).
   - [ ] Commit, rebase onto `origin/master`, and push via `git-commit-and-sync`.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/ingestion/http_fetcher.py` | Static: format, lint, type | `uv run ruff format` / `uv run ruff check` / `uv run mypy --no-namespace-packages scripts/` | Clean, no new errors |
| `scripts/rag/ingestion/http_fetcher.py` | Unit: empty-path returns `{}` without raising | `uv run pytest tests/rag/ingestion/test_crawler_integration.py -v` | New + existing tests pass |
| `scripts/rag/ingestion/crawler.py` | Behavioral: startup error on empty path | `uv run pytest tests/rag/ingestion/ -v` | No regressions |

## Risks
- **Risk**: Raising in `__init__` to achieve true fail-fast breaks many existing tests. → **Mitigation**: place the startup validation at the BFS/main() boundary, not the constructor; absorb the `ValueError` in `get_conditional_headers` as the non-crashing safety net.
- **Risk**: A deduped log flag could hide a genuinely new misconfiguration on a later restart. → **Mitigation**: the flag is per-process; each fresh crawl process logs once, which is sufficient for a startup signal.
- **Risk**: Changing the caught-exception tuple could mask a legitimate new error type. → **Mitigation**: only add `ValueError` (the known empty-path error); keep the SQLite errors intact.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `ValueError` safety net + deduped startup warning in `get_conditional_headers` (`scripts/rag/ingestion/http_fetcher.py`) | Completed | — | 20261106 |  |
| 2 | Add pre-BFS startup validation for empty `rag_db_path` (`scripts/rag/ingestion/crawler.py`) | Completed | — | 20261106 | Depends on UNK-01 resolution |
| 3 | Format/lint/type/test verification and commit | Completed | — | 20261106 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261106-134321_01_scripts_rag_ingestion_http_fetcher.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261106-134321_02_scripts_rag_ingestion_crawler.py.md` | 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261106-073205_crawl003_rag-db-path-misconfiguration-handling.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261106-094153
- **Related target files**: `scripts/rag/ingestion/http_fetcher.py`, `scripts/rag/ingestion/crawler.py`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Summary / Reason for Change | `scripts/rag/ingestion/crawler.py` | Step 2 | REQ-001 acceptance criteria | startup-error test | Confirmed by repository evidence |
| REQ-002 | Problem / Background | `scripts/rag/ingestion/http_fetcher.py` | Step 1 | REQ-002 acceptance criteria | empty-path unit test | Confirmed by repository evidence |
| REQ-003 | Background / Required Changes | `scripts/rag/ingestion/http_fetcher.py` | Step 1 | REQ-003 acceptance criteria | valid-path regression test | Confirmed by repository evidence |
| REQ-004 | Implementation Intent | `scripts/rag/ingestion/crawler.py`, `scripts/rag/ingestion/http_fetcher.py` | Step 3 | REQ-004 acceptance criteria | full crawler/fetcher suite | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261106-134321 -->