## Goal

Create `tests/rag/ingestion/test_crawler_redirects.py` (new): mock-transport redirect tests and policy unit tests covering the refused cases and the allowed same-host upgrade (`REQ-001`..`REQ-006`).

## Scope
**Release unit**: ragrev012-core

- In scope: `tests/rag/ingestion/test_crawler_redirects.py` (new) — mock-transport tests for cross-host, loopback (literal and by name), link-local, private-range, same-host upgrade, https-to-http downgrade, loop, and hop-limit cases; unit tests for the policy helpers.
- Out of scope: the policy helpers themselves (document `03`), the fetch and orchestrator changes (documents `01`, `02`), and the documentation (document `05`).

## Assumptions

- The module runs against the mock transport already used by `tests/rag/ingestion/test_crawler_integration.py`; the policy helpers are the new helpers of document `03`, imported from `crawler_utils`.
- `fetch_html` returns the typed result of the sibling plan (ragrev011), so the refused cases assert the failed outcome and the upgraded case asserts persistence under the final URL.
- Overlap with ragrev011 on the shared test file: that Plan updates the fetch-result tests in its own file; this Plan adds a separate module, so the two do not edit the same file.

## Design decisions

- Use a mock transport (not a live server) so refused addresses never leave the process; the transport returns redirect responses whose target is chosen per case.
- Cover each refusal reason from `REQ-002` in one parametrized test, plus the allowed-upgrade and loop/hop-limit cases.
- Structure the file so `-k policy` selects the policy-helper unit tests and the integration assertions reuse the same transport.

## Alternatives considered

- Live-server tests: rejected; they resolve real hosts and cannot exercise loopback, link-local, or private refusals deterministically.

## Implementation
### Target file
`tests/rag/ingestion/test_crawler_redirects.py` (new)

### Procedure
1. Create the file under `tests/rag/ingestion/` (which exists) with an async client built with `follow_redirects=False`, mirroring the orchestrator's build.
2. Add a mock-transport factory that returns a redirect response whose target is chosen per case: cross-host, `127.0.0.1`, `localhost`, `169.254.169.254`, a private range, a same-host https upgrade, an https-to-http downgrade, a loop, or an over-long chain.
3. Drive `CrawlOrchestrator.crawl_site` (`crawl_site`) from a test and assert the refused cases end as a failed fetch and enqueue nothing, while the same-host upgrade is followed and persisted under the final URL.
4. Parametrize the refusal cases so `-k policy` selects the policy-helper unit tests and the integration assertions share the transport.
5. Assert the loop and the over-long hop limit both end as failed with a distinct log (`REQ-001`).

### Method

- Follow the mock-transport conventions of `test_crawler_integration.py`; keep each case small and independent.
- Do not resolve real network addresses; stub resolution so `localhost` maps to loopback.

### Details

- The refused cases assert the fetch ends failed and no page is persisted; the upgraded case asserts the persister receives the final URL.
- The policy-helper unit tests call the new helpers directly (document `03`) and cover the public/non-public address matrix and the http-to-https rule.
- Run the module with `uv run pytest tests/rag/ingestion/test_crawler_redirects.py -q`.

## Compatibility considerations

- This is a new file; it does not change existing suites. The sibling plan's typed-result updates to `test_crawler_integration.py` coexist in that separate file (`REQ-005`).

## Security considerations

- The mock transport keeps every redirect inside the test process, so refused loopback, link-local, and private destinations are never actually contacted; a case that should be refused must fail on HEAD before the implementation guards it.

## Rollback considerations

- Revert the release unit's commits together (documents `01` to `04`); delete the new test file with them.

## Validation plan

- `uv run pytest tests/rag/ingestion/test_crawler_redirects.py -q -k policy` for the policy matrix.
- `uv run pytest tests/rag/ingestion/test_crawler_redirects.py tests/rag/ingestion/test_crawler_integration.py tests/rag/ingestion/test_robots.py -q`, then `uv run pytest tests/rag/ingestion -q`.
- `uv run ruff check` and `uv run mypy` on the file.

## Completion criteria

- The cross-host, literal-IP, named-loopback, link-local, and private-range cases fail on HEAD and pass after the helpers and fetch loop land.
- The same-host upgrade passes and persists under the final URL; the downgrade, loop, and hop-limit cases behave as specified.
- The new suite is green and the existing suites stay green.

## Out of Scope

- The policy helpers (document `03`).
- The fetch and orchestrator changes (documents `01`, `02`).
- The crawler documentation (document `05`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | New file |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Documentation is document `05` |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261109-205004_04_tests_rag_ingestion_test_crawler_redirects.py.md | 1 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001` (loop and hop-limit tests), `REQ-002` (cross-host and internal-address tests), `REQ-003` (robots-denied hop), `REQ-004` (same-host upgrade), `REQ-006` (new redirect tests)
- **Source issue**: issues/20261108-131127_ragrev012_crawler-redirect-trust-boundary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-170101_ragrev012_crawler-redirect-trust-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-205004
- **Related target files**: `tests/rag/ingestion/test_crawler_redirects.py`
