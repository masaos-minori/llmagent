## Goal

Turn automatic redirect following off and persist an accepted page under the URL it was finally accepted under (`REQ-001`: the client is built without following redirects; `REQ-004`: the final accepted URL is what is persisted and marked visited), threading the start origin and the robots cache into the fetch so the hop policy in `fetch_html` can validate every hop.

## Scope
**Release unit**: ragrev012-core

- In scope: `scripts/rag/ingestion/orchestrator.py` — build the `AsyncClient` with `follow_redirects=False`, pass the start origin and the robots cache into `fetch_html`, branch on the typed result, persist the fetched page under its final accepted URL, add that URL to the visited set, and log a refused redirect distinctly.
- Out of scope: the manual redirect loop and per-hop policy in `fetch_html` (document `01`), the redirect-allowed and non-public-address policy helpers (document `03`), the mock-transport tests (document `04`), and the documentation (document `05`).

## Assumptions

- The sibling plan `plans/20261108-165922_ragrev011_recrawl-304-drops-subtree.md` lands first and gives `fetch_html` a typed result that separates the fetched, not-modified, and failed outcomes; this procedure branches on that union and refers to the outcomes by purpose, not by a name it does not define.
- The start origin is the scheme plus netloc of the normalized start URL, matching the value already derived at `orchestrator.py:129-131`; the robots cache is the attribute read via `getattr` there.
- The fetched outcome carries the final accepted URL (a field document `01` adds); this procedure reads it to choose the persisted URL.
- Overlap with the ragrev011 Plan on this file is a sequencing dependency (ragrev011 first, recorded under the Plan's Scope Dependencies), compatible because the changes touch different parts of the same methods.

## Design decisions

- Keep the client change in `crawl_site` and the persistence/visited change in `_process_crawl_url_async`: each owns one concern and the diff stays next to the existing code.
- Mark the final URL visited rather than the requested URL: the page is persisted under the final URL, so deduplication must key on the same value the persister writes.
- Log a refused redirect at error level with the reason, matching how the sibling plan reports a failed fetch, so the operator sees why a page was dropped.

## Alternatives considered

- Marking the requested URL visited instead of the final URL: rejected; the persister writes the final URL, so the visited set would not deduplicate it on a later hop.
- Persisting under the requested URL: rejected; the plan persists under the final accepted URL and records the resulting conditional-header cost in its Risks.

## Implementation
### Target file
`scripts/rag/ingestion/orchestrator.py`

### Procedure
1. In `crawl_site`, change the `AsyncClient` build (current `scripts/rag/ingestion/orchestrator.py:109-113`) to `follow_redirects=False` so `fetch_html` owns redirect following.
2. Derive the start origin from the normalized start URL as `scheme://netloc` (as at `orchestrator.py:129-131`) and pass it together with the robots cache already loaded at `orchestrator.py:127-131` into the fetch.
3. Thread those two arguments through `_process_crawl_url_async` (`orchestrator.py:216-265`) to the single `fetch_html` call site.
4. Branch on the typed result: for the fetched outcome read the final accepted URL; for the not-modified and failed outcomes behave as the sibling plan specifies and enqueue nothing.
5. Persist the fetched page with `save_http` under the final accepted URL instead of the requested URL (`orchestrator.py:254-263`), then add the final URL to the visited set (`orchestrator.py:101`) so the BFS does not fetch it twice.
6. On a refused redirect, log the reason distinctly before returning.

### Method
- Edit by symbol; leave the semaphore, the `FIRST_COMPLETED` loop, the session SQLite connection, and the budget bookkeeping untouched.
- Keep `crawl_site` within its current complexity band; the two argument additions are thin threads, not new branches.

### Details
- When the fetched outcome has no redirect the final URL equals the requested URL, so persistence is unchanged for non-redirected pages.
- `visited` now keys on the persisted URL, so a redirected page and the URL that requested it are not both scheduled.
- Public names remain importable from `rag.ingestion.orchestrator`.
- Run `uv run python tools/check_module_size.py` after the edit; the module is far below the gate.

## Compatibility considerations

- `fetch_html` gains the two parameters threaded here (document `01`); its only production caller is updated by this document, and the tests call it directly and are updated by document `04`, so apply and validate documents `01`, `03`, and `04` as one unit.
- Turning off automatic redirects means every redirecting page now goes through the hop loop; the 304, conditional-header, and retry paths are otherwise unchanged (`REQ-005`).

## Security considerations

- This is the enforcement half of the trust boundary: with `follow_redirects=False` the hop policy in `fetch_html` is the only path that requests a redirected URL, so a refused cross-origin or non-public hop can no longer reach an internal service. The start host is always allowed even if it resolves to a private address; only other hosts face the address check.

## Rollback considerations

- Revert the release unit's commits together (documents `01` to `04`); the only state effect is which `documents.url` is written for redirected pages.

## Validation plan

- After documents `01`, `03`, `04`: `uv run pytest tests/rag/ingestion/test_crawler_redirects.py tests/rag/ingestion/test_crawler_integration.py tests/rag/ingestion/test_robots.py -q`, then `uv run pytest tests/rag/ingestion -q`.
- `uv run ruff format` and `uv run ruff check` on the file; `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`; `PYTHONPATH=scripts uv run lint-imports`; `uv run bandit -r scripts/rag -c pyproject.toml -ll`; `uv run python tools/check_compat_shims.py`.
- Coverage on changed lines at 90 percent (`diff-cover`).

## Completion criteria

- The client is created with `follow_redirects=False`; a page that redirects is persisted under the final accepted URL and that URL is in the visited set.
- A same-host upgrade is followed and persisted under the final URL; a downgrade, cross-origin, or non-public hop is logged distinctly and enqueues nothing.
- The 304, conditional-header, retry, and link-discovery paths are unchanged.
- The module passes ruff, mypy, bandit, and the import-linter contracts.

## Out of Scope

- The manual redirect loop and per-hop policy (`fetch_html`, document `01`).
- The policy helpers (document `03`).
- The mock-transport tests (document `04`).
- The crawler documentation (document `05`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261109-234525 | 20261109-234525 | Sequencing dependency: ragrev011's typed result lands first |
| 2 | Add or update tests per Validation plan | Completed | 20261109-234525 | 20261109-234525 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261109-234525 | 20261109-234525 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261109-234525 | 20261109-234525 | Documentation is document `05` |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261109-205004_02_scripts_rag_ingestion_orchestrator.py.md | 1 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001` (client built without following redirects), `REQ-004` (persist and mark the final accepted URL visited)
- **Source issue**: issues/20261108-131127_ragrev012_crawler-redirect-trust-boundary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-170101_ragrev012_crawler-redirect-trust-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-205004
- **Related target files**: `scripts/rag/ingestion/orchestrator.py`