## Goal

Replace the `tuple | None` return of `HttpFetcher.fetch_html` with a typed result that separates fetched, not-modified, and failed outcomes, so callers never infer meaning from `None` (`REQ-001`: typed three-outcome result; `REQ-004`: a failed fetch is a result kind distinct from a 304).

## Scope
**Release unit**: ragrev011-core

- In scope: `scripts/rag/ingestion/http_fetcher.py` (the result types, the `fetch_html` return paths and docstring, the not-modified log wording).
- Out of scope: `get_conditional_headers`, retry and timeout behavior, redirect handling (ragrev012), and the orchestrator and tests that consume the result (documents `02` and `03`).
- Plan: `plans/20261108-165922_ragrev011_recrawl-304-drops-subtree.md` (Plan step 2); the orchestrator breaks until document `02` lands, hence the release unit.

## Assumptions

- Re-verified at generation time (by symbol): `fetch_html` returns `None` both for a 304 (after an info log) and after the retry loop is exhausted, and returns `(resp.text, etag, last_modified)` on success; its only production caller is `CrawlOrchestrator._process_crawl_url_async`; tests call it directly and mock it in `tests/rag/ingestion/test_crawler_integration.py`.
- The repository has a no-compatibility-shim policy (`tools/check_compat_shims.py`), so no old-shape wrapper is kept.
- Overlap: `plans/20261108-170101_ragrev012_crawler-redirect-trust-boundary.md` also edits `fetch_html` and declares `Depends on` this Plan phase 2; this Plan lands first and ragrev012 builds its redirect loop on the typed result (sequencing dependency, no conflict). Locate code by symbol name, not line number.

## Design decisions

- Three small frozen dataclasses in `http_fetcher.py` and a union alias: `Fetched` (new) with `html`, `etag`, `last_modified`; `NotModified` (new) with no fields; `FetchFailed` (new) with no fields; `FetchResult` (new) is `Fetched | NotModified | FetchFailed`. Callers branch with `isinstance`, which mypy narrows; no enum or string kind to compare.
- Keep the types in `http_fetcher.py`: the orchestrator already imports from this module, so no new import edge or file is needed.

## Alternatives considered

- One dataclass with a `kind` field and optional members: rejected; every consumer would re-check optional fields, which the union avoids.
- Raising on failure and a sentinel for 304: rejected; failure is an expected, retried outcome and the orchestrator logs and continues.

## Implementation
### Target file
`scripts/rag/ingestion/http_fetcher.py`

### Procedure
1. Add the frozen dataclasses Fetched (new), NotModified (new), and FetchFailed (new) and the alias FetchResult (new) above `HttpFetcher`.
2. Change the return annotation of `fetch_html` to FetchResult and update its docstring to name the three outcomes.
3. Return `NotModified()` for a 304, `Fetched(resp.text, etag, last_modified)` on success, and `FetchFailed()` after the retry loop is exhausted.
4. Reword the 304 log line so it no longer says "skipping" (the orchestrator may now fetch the page again for link discovery): log `"%s Not Modified: %s"`.

### Method
- Edit by symbol; leave the retry loop, the sleep back-off, the header extraction, and `get_conditional_headers` untouched.
- Keep `fetch_html` at or below cyclomatic complexity B (8); the change only swaps return expressions.

### Details
- Use `@dataclass(frozen=True)` (the module already imports nothing from `dataclasses`, so add that import at the top with the other standard-library imports).
- Public names are importable from `rag.ingestion.http_fetcher`; the orchestrator and the tests import them from there.
- Run `uv run python tools/check_module_size.py` after the edit; the module is far below the gate.

## Compatibility considerations

- Breaking change to a public method's return contract, by design: the only production caller (`CrawlOrchestrator._process_crawl_url_async`) and the tests are updated by documents `02` and `03` of this release unit; the rest of `tests/rag/ingestion` fails until both land, so apply and validate them as one unit.
- No persisted data, config key, or wire behavior changes; request headers and retries are unchanged.

## Security considerations

N/A: no trust-boundary change; the same requests are made and no new input is parsed (redirect policy is ragrev012).

## Rollback considerations

- Revert the release unit's commits together (documents `01` to `03`); no persisted state is involved.

## Validation plan

- After documents `01` to `03`: `uv run pytest tests/rag/ingestion/test_crawler_integration.py tests/rag/ingestion/test_robots.py -q`, then `uv run pytest tests/rag/ingestion -q`.
- `uv run ruff format` and `uv run ruff check` on the file; `uv run mypy`; `PYTHONPATH=scripts uv run lint-imports`; `uv run python tools/check_module_size.py`; `uv run python tools/check_compat_shims.py`.
- Coverage on changed lines at 90 percent (`diff-cover`).

## Completion criteria

- `fetch_html` returns exactly one of Fetched, NotModified, or FetchFailed; no path returns `None`.
- FetchResult and its members are the only definition of the fetch outcome; no old-shape function remains.
- The module passes ruff, mypy, and the import-linter contracts.

## Out of Scope

- Redirect handling, robots policy, conditional-header lookup, retry policy, and the consumers of the result (documents `02` and `03`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the result types and change the `fetch_html` returns, docstring, and 304 log wording | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) together with documents `02` and `03` | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (typed three-outcome result), `REQ-004` (failed distinct from 304)
- **Source issue**: issues/20261108-131125_ragrev011_recrawl-304-drops-subtree.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-165922_ragrev011_recrawl-304-drops-subtree.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-143141
- **Related target files**: `scripts/rag/ingestion/http_fetcher.py`
