## Goal

Rewrite the `fetch_html` redirect handling so that every hop is validated before it is requested: follow same-origin hops (an http-to-https upgrade allowed, a downgrade refused) hop by hop, and refuse a cross-origin, loopback, link-local, reserved, multicast, or unspecified destination with a distinct failed outcome, carrying the final accepted URL in the result (`REQ-001`: at most a fixed number of hops, a loop or over-long chain logged distinctly; `REQ-002`: per-hop same-host rule plus a non-public-address check for non-start hosts; `REQ-003`: per-hop robots check when a cache is configured; `REQ-005`: the 304, conditional-header, and retry paths are unchanged).

## Scope
**Release unit**: ragrev012-core

- In scope: `scripts/rag/ingestion/http_fetcher.py` — replace the single `client.get(url)` with a bounded hop loop that applies the per-hop policy and returns the final accepted body with its final URL; extend the fetched outcome with a `final_url` (new) field; pass the not-modified and failed outcomes through unchanged.
- Out of scope: building the client with `follow_redirects=False` and passing the start origin and robots cache into the fetch (document `02`), the redirect-allowed and non-public-address policy helpers themselves (document `03`), the mock-transport tests (document `04`), and the documentation (document `05`).
- Plan: `plans/20261108-170101_ragrev012_crawler-redirect-trust-boundary.md` (Plan step 3); the client change lands in document `02`, hence the release unit.

## Assumptions

- Re-verified at generation time (by symbol): `fetch_html` (`scripts/rag/ingestion/http_fetcher.py:42-72`) makes one `client.get(url, headers=req_headers)`, returns `(resp.text, etag, last_modified)` on 200 and `None` on a 304 or after the retry loop is exhausted; its only production caller is `CrawlOrchestrator._process_crawl_url_async` (`orchestrator.py:236`), which unpacks the tuple.
- The sibling plan `plans/20261108-165922_ragrev011_recrawl-304-drops-subtree.md` lands first (Plan Scope Dependencies) and gives `fetch_html` a typed result that separates the fetched, not-modified, and failed outcomes; this procedure is written against that union, so locate the three outcome kinds by purpose, not by a name this document does not define. The typed result is a sequencing dependency, not a conflict.
- The start origin and the `RobotsCache` are passed into `fetch_html` by document `05`; this procedure assumes they are available as parameters.
- The repository has a no-compatibility-shim policy (`tools/check_compat_shims.py`), so no old single-request path is kept.
- Overlap: `http_fetcher.py`, `orchestrator.py`, and the crawler doc are also targets of the ragrev011 Plan; judged a sequencing dependency (ragrev011 first), compatible otherwise because the changes touch different parts of the same functions.

## Design decisions

- Keep the hop loop inside `fetch_html`: it owns the fetch concern and already holds the `client`, the retry state, and the conditional headers; routing each hop through the loop keeps the policy close to the request.
- Put the redirect-allowed and non-public-address rules in `scripts/rag/ingestion/crawler_utils.py` (document `03`) as pure, stdlib-only helpers next to `same_origin`; `fetch_html` calls them and keeps no policy logic of its own.
- Carry the final accepted URL in the fetched outcome (the plan requires "final URL in the result") so the orchestrator persists under it; the loop already knows the accepted URL, so no second lookup is needed.
- A refused hop returns the failed outcome rather than raising: a refused redirect is an expected outcome the orchestrator logs and continues, consistent with how the sibling plan treats a failed fetch.

## Alternatives considered

- Deriving the final URL from the response history in the orchestrator instead of the result: rejected; the plan puts the final URL in the result and the loop already knows the accepted URL, so duplicating it in the orchestrator would split one fact across two files.
- Raising on a refused hop instead of returning the failed outcome: rejected; refusal is an expected, logged outcome, and raising would force the retry/semaphore machinery to treat it as an error.

## Implementation
### Target file
`scripts/rag/ingestion/http_fetcher.py`

### Procedure
1. Change the `fetch_html` signature to accept the crawl `origin` (scheme+netloc of the start URL) and the optional `robots_cache` from the orchestrator (document `05`); thread them through the single call site in `orchestrator.py:236`.
2. Replace the single `client.get(url)` with a bounded hop loop. Derive each hop URL from the previous response's redirect target, request it only after the per-hop policy passes, and stop when a response is not a redirect.
3. Before requesting each hop, apply the redirect-allowed policy (document `03`) against `origin`, and for a non-start host apply the non-public-address check (document `03`); then apply `is_allowed` from the robots cache when one is configured. On any refusal, return the failed outcome with a distinct reason log and enqueue nothing.
4. Bound the hop count; a detected loop or a chain longer than the limit returns the failed outcome with a distinct log (`REQ-001`).
5. On the final accepted (non-redirect) response, build the fetched outcome with the html, `etag`, `last_modified`, and the final accepted URL (the `final_url` (new) field, see Details).
6. Pass the not-modified and failed outcomes through unchanged (`REQ-005`): a 304 still returns the not-modified outcome after its info log, and retry exhaustion still returns the failed outcome.

### Method
- Edit by symbol; leave the retry loop, the sleep back-off, the header extraction, and `get_conditional_headers` untouched.
- Keep `fetch_html` at or below its current cyclomatic complexity band; the hop loop and the per-hop decision go into small private helpers so the function does not grow past its grade.

### Details
- `final_url` (new) is a field on the fetched outcome; update its constructor call site in step 5 so every fetched page carries the URL it was finally accepted under.
- The per-hop policy helpers are defined in document `03`; here they are called by purpose, not reimplemented.
- Name resolution for the address check uses the event loop's asynchronous resolver; a resolution failure is treated as a refusal and logged.
- Public names remain importable from `rag.ingestion.http_fetcher`; the orchestrator imports `fetch_html` from there.
- Run `uv run python tools/check_module_size.py` after the edit; the module is far below the gate.

## Compatibility considerations

- `fetch_html` gains two parameters (`origin`, `robots_cache`); its only production caller is `CrawlOrchestrator._process_crawl_url_async`, updated by document `02`, and the tests call it directly and are updated by document `04`, so apply and validate documents `02`-`04` as one unit.
- The fetched outcome gains a final-URL field; the union shape is unchanged (only one member grows), so the sibling plan's `isinstance` branching still narrows correctly.
- `REQ-005`: the 304, conditional-header, and retry behavior are unchanged; request headers and retries are identical.

## Security considerations

- Trust-boundary change (core of `REQ-002`): every hop is validated before it is requested, so an open redirect or a malicious page can no longer make the crawler reach another host or an internal service (loopback, link-local, reserved, multicast, unspecified). The start host is always allowed even if it resolves to a private address; only other hosts face the address check.
- Policy helpers use the standard library `ipaddress` and the loop resolver only; no new dependency (Issue constraint).
- `uv run bandit -r scripts/rag -c pyproject.toml -ll` is part of validation.

## Rollback considerations

- Revert the release unit's commits together (documents `01` to `04`); no persisted state is involved beyond which `documents.url` is written for redirected pages (a documented risk in the Plan).

## Validation plan

- After documents `03` to `05`: `uv run pytest tests/rag/ingestion/test_crawler_redirects.py tests/rag/ingestion/test_crawler_integration.py tests/rag/ingestion/test_robots.py -q`, then `uv run pytest tests/rag/ingestion -q`.
- `uv run ruff format` and `uv run ruff check` on the file; `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`; `PYTHONPATH=scripts uv run lint-imports`; `uv run bandit -r scripts/ -c pyproject.toml -ll`; `uv run python tools/check_module_size.py`; `uv run python tools/check_compat_shims.py`.
- Coverage on changed lines at 90 percent (`diff-cover`).

## Completion criteria

- A cross-origin or non-public hop returns the failed outcome and enqueues nothing; a same-origin hop (including http-to-https) is followed and the page is returned with the final accepted URL.
- A redirect loop and a chain longer than the hop limit both return the failed outcome with a distinct log.
- The 304 and retry paths still return the not-modified and failed outcomes unchanged.
- The module passes ruff, mypy, bandit, and the import-linter contracts.

## Out of Scope

- Building the client with `follow_redirects=False` and persisting under the final URL (document `05`).
- The redirect-allowed and non-public-address policy helpers (document `03`).
- The mock-transport and policy tests (document `04`).
- The crawler documentation (document `06`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the `fetch_html` hop loop with the per-hop policy and carry the final URL in the result | Completed | 20261109-234525 | 20261109-234525 | Sequencing dependency: ragrev011's typed result lands first Adversarial verification found REQ-003 per-hop robots check unimplemented; added robots_cache.is_allowed() to _hop_policy per Procedure step 3. |
| 2 | Run the validation sequence together with documents `03`, `04`, and `05` | Completed | 20261109-234525 | 20261109-234525 | Full rag ingestion suite green (314); diff-cover 96%; ruff/mypy/lint-imports/bandit/module-size/compat-shims clean. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261109-205004_01_scripts_rag_ingestion_http_fetcher.py.md | 1 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001` (bounded hops, distinct loop/over-long log), `REQ-002` (per-hop same-host and non-public-address policy), `REQ-003` (per-hop robots when configured), `REQ-005` (304/retry unchanged)
- **Source issue**: issues/20261108-131127_ragrev012_crawler-redirect-trust-boundary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-170101_ragrev012_crawler-redirect-trust-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-205004
- **Related target files**: `scripts/rag/ingestion/http_fetcher.py`