## Goal

When a robots cache is present on the wired `LinkDiscovery`, fetch the start host's `robots.txt` once before the BFS loop using the shared `httpx.AsyncClient`; do nothing when absent (REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `crawl_site` (lines 76-114) owns the `httpx.AsyncClient` lifecycle (the `async with` at lines 84-88) and the BFS loop (the `while` starting at line 89).
- `self._link_discovery` is the `LinkDiscovery` instance wired by `crawler.py` (row 4); its `_robots_cache` attribute is `None` when the flag is off and a `RobotsCache` when on.
- `RobotsCache.fetch_host` (defined in `scripts/rag/ingestion/robots.py`, row 1) is idempotent per host, so calling it once per `crawl_site` fetches each host exactly once.
- `normalize_url` is already imported at module level (lines 30-32).
- `crawl004` also targets `crawl_site`; implement this eager-fetch change in plan order so it coexists with any session-scoped connection block there.

## Design decisions
- Read the cache via `getattr(self._link_discovery, "_robots_cache", None)` so no change to `LinkDiscovery` is required here and the disabled path (`None`) is a clean no-op.
- Derive the origin (`scheme://netloc`) from the normalized start URL and pass it to `fetch_host` before the loop, so disallowed start paths are filtered before any page is fetched.

## Alternatives considered
- A dedicated `robots_cache` property on `LinkDiscovery` — rejected: it would extend row 2's scope; reading the existing attribute keeps this change confined to `orchestrator.py`.

## Implementation
### Target file
`scripts/rag/ingestion/orchestrator.py`

### Procedure
Eagerly fetch the start host's `robots.txt` once, before the BFS loop, only when a robots cache is wired.

### Method
Add the stdlib import near the other module imports:
```python
from urllib.parse import urlparse (new)
```
Inside `crawl_site` (lines 76-114), right after the `async with httpx.AsyncClient(...) as client:` block (line 88) and before the `while` loop (line 89), insert:
```python
robots_cache = getattr(self._link_discovery, "_robots_cache", None)
if robots_cache is not None:
    parsed_start = urlparse(normalize_url(start_url))
    origin = f"{parsed_start.scheme}://{parsed_start.netloc}"
    await robots_cache.fetch_host(origin, client)
```
Place this inside the `async with` block and before the `while` so it uses the same `client`. If a later `crawl_site` addition wraps the `while` in `try/finally`, put this eager fetch before that `while` so both coexist.

### Details
- `normalize_url(start_url)` strips the fragment/trailing slash; `urlparse` then yields the scheme and netloc used to build `{scheme}://{netloc}/robots.txt` inside `fetch_host`.
- When respect_robots is off, `_robots_cache` is `None`, the branch is skipped, and zero `robots.txt` requests are issued (REQ-002).
- Idempotency in `fetch_host` guarantees at-most-once per host even across the multi-target `crawl` loop (REQ-003).

## Compatibility considerations
Behavior-preserving when disabled: the new block is skipped entirely when `_robots_cache` is `None` (REQ-002). When enabled it adds exactly one GET per host before the crawl begins.

## Security considerations
N/A: the request targets `/robots.txt` and is bounded by the shared `httpx` timeout already used for page fetches.

## Rollback considerations
N/A: revert the commit that introduces this procedure.

## Validation plan
- Static: `uv run ruff format` / `uv run ruff check` on `scripts/rag/ingestion/orchestrator.py`; `uv run mypy --no-namespace-packages scripts/` with no new errors.
- Behavioral: with the flag on and mocked `robots.txt`, assert exactly one fetch per host across a multi-URL same-origin crawl; with the flag off assert zero `robots.txt` requests. Run `tests/rag/ingestion/`.

## Completion criteria
- With the flag on, the start host's `robots.txt` is fetched exactly once before the BFS loop and disallowed start paths are not crawled (REQ-003).
- With the flag off, no `robots.txt` request is issued and crawl behavior is unchanged (REQ-002).

## Out of Scope
Changing the `httpx.AsyncClient` lifecycle or the BFS loop scheduling.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Eagerly fetch start host `robots.txt` once before the BFS loop when a cache is present | Completed | 20261106-183622 | 20261106-183622 | Row 3; place inside `async with`, before `while` (line 89) |
| 2 | Add or update tests per Validation plan | Completed | 20261106-183622 | 20261106-183622 | One-fetch-per-host, zero-fetch when off |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261106-183622 | 20261106-183622 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261106-183622 | 20261106-183622 | N/A |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | N/A: no blocker | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-003`
- **Source issue**: `issues/20261106-073206_crawl005_crawler-robots-txt-policy.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261106-094856_crawl005_crawler-robots-txt-policy.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-135528
- **Related target files**: `scripts/rag/ingestion/orchestrator.py`