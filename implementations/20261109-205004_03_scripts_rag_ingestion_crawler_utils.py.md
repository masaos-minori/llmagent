## Goal

Add the two hop-policy helpers that `fetch_html` calls before requesting each redirect hop (`REQ-002`): a redirect-allowed rule that reuses `same_origin` but permits an http-to-https upgrade, and a non-public-address check that refuses a non-start host whose resolved addresses are private, loopback, link-local, reserved, multicast, or unspecified.

## Scope
**Release unit**: ragrev012-core

- In scope: `scripts/rag/ingestion/crawler_utils.py` — add the redirect-allowed rule and the non-public-address check next to `same_origin`, standard library only.
- Out of scope: calling the helpers from `fetch_html` (document `01`), building the client and persisting under the final URL (document `02`), the mock-transport tests (document `04`), and the documentation (document `05`).

## Assumptions

- The start origin is passed in as `scheme://netloc`; the redirect-allowed rule compares the hop against it, and the non-public-address check is applied only to hosts other than the start host (document `01`).
- Name resolution for the address check happens before the request and is not pinned to the connection, so a DNS-rebinding attacker is not fully excluded (a documented limitation in the Plan).
- Overlap with the ragrev011 Plan on this file is a sequencing dependency (ragrev011 first); this file is not edited by that Plan.

## Design decisions

- Keep both helpers pure and stdlib-only (`urllib.parse`, `ipaddress`, the event-loop resolver) so they need no new dependency and are trivially unit-testable (document `04`).
- Put the redirect-allowed rule next to `same_origin` and build on it: `same_origin` compares scheme and `netloc`, which would refuse an ordinary http-to-https upgrade, so the new rule allows only that one upgrade and refuses a downgrade.
- Do the address check in a single async helper that resolves once and applies `ipaddress`; keep the sync `ipaddress` predicate small so the policy matrix is testable without a network.

## Alternatives considered

- Reusing `same_origin` unchanged for hops: rejected; it refuses the http-to-https upgrade the Issue requires to keep working.
- Checking only the final URL: rejected; intermediate hops are also requests from inside the host.

## Implementation
### Target file
`scripts/rag/ingestion/crawler_utils.py`

### Procedure
1. Add the redirect-allowed rule (new), taking the hop URL and the start origin, next to `same_origin` (`scripts/rag/ingestion/crawler_utils.py:107-110`): parse both URLs, require the same `hostname`, and allow only an http-to-https scheme upgrade while refusing a downgrade and normalizing default ports.
2. Add the address check (new), an async helper taking the host, that resolves the host with the running loop's `getaddrinfo` and returns `False` unless every resolved address is public per `ipaddress` (not private, loopback, link-local, reserved, multicast, or unspecified); a resolution failure returns `False`.
3. Expose a small sync predicate for the `ipaddress` test (document `04`) as part of the same helper rather than a separate public name.
4. Keep the helpers free of any crawler state; `fetch_html` (document `01`) imports and calls them.

### Method
- Edit by symbol; leave `same_origin`, `extract_text`, `detect_lang`, and the target-file parsers untouched.
- Keep the module under its size gate; the two helpers are short.

### Details
- The redirect-allowed rule reuses `urlparse` and compares `hostname`, so `http://example.com` and `https://example.com/` are the same host and the upgrade is allowed, while a different host differs and is refused.
- The address check treats a resolution failure as a refusal (fail closed) and logs it where called.
- Public names remain importable from `rag.ingestion.crawler_utils`.
- Run `uv run python tools/check_module_size.py` after the edit; the module is far below the gate.

## Compatibility considerations

- The two helpers are additions; existing callers and the sibling plan's tests are unaffected until document `01` wires them in.
- `REQ-005`: the language detection, content extraction, and target-file parsing are unchanged.

## Security considerations

- These are the trust-boundary primitives (`REQ-002`): the redirect-allowed rule keeps the crawl on the start host (plus the required upgrade), and the address check blocks redirects to internal services (loopback, link-local, reserved, multicast, unspecified, private). The start host is exempt from the address check and is decided by the redirect-allowed rule instead.
- Standard library only; no new dependency (Issue constraint).

## Rollback considerations

- Revert the release unit's commits together (documents `01` to `04`); no persisted state is involved.

## Validation plan

- `uv run pytest tests/rag/ingestion/test_crawler_redirects.py -q -k policy` for the policy matrix.
- `uv run ruff format` and `uv run ruff check`; `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`; `PYTHONPATH=scripts uv run lint-imports`; `uv run bandit -r scripts/rag -c pyproject.toml -ll`.
- Coverage on changed lines at 90 percent (`diff-cover`).

## Completion criteria

- The redirect-allowed rule follows a same-host http-to-https upgrade and refuses a downgrade, a cross-host hop, and an apex-to-`www.` hop.
- The address check returns `True` for a public host and `False` for loopback, link-local, private, and other non-public ranges, and on resolution failure.
- The module passes ruff, mypy, bandit, and the import-linter contracts.

## Out of Scope

- Calling the helpers from `fetch_html` (document `01`).
- Building the client and persisting under the final URL (document `02`).
- The mock-transport tests (document `04`).
- The crawler documentation (document `05`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Precedes the fetch loop (document `01`) |
| 2 | Add or update tests per Validation plan | Pending | — | — | Policy unit tests |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Documentation is document `05` |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261109-205004_03_scripts_rag_ingestion_crawler_utils.py.md | 1 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002` (per-hop same-host rule plus non-public-address check)
- **Source issue**: issues/20261108-131127_ragrev012_crawler-redirect-trust-boundary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-170101_ragrev012_crawler-redirect-trust-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-205004
- **Related target files**: `scripts/rag/ingestion/crawler_utils.py`
