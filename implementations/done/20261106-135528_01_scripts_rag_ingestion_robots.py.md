## Goal

Create an isolated `RobotsCache` (new) (`scripts/rag/ingestion/robots.py`) that fetches and parses `robots.txt` per host and answers `can_fetch(user_agent, url)` queries, so external crawling respects Disallow rules (REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `scripts/rag/ingestion/robots.py` does not currently exist; this document creates it (row 1 of the plan).
- The crawl is same-origin (`skip_external = true` by default), so only the start host's `robots.txt` is needed per `crawl_site`; multiple targets mean multiple hosts, each fetched once.
- `urllib.robotparser.RobotFileParser` (stdlib) is adequate; no third-party robots library is available in deps.
- The crawler user agent (`_USER_AGENT`) is used as the robots user-agent token.
- `RobotsCache` (new) is constructed by `crawler.py` (row 4) and injected into `LinkDiscovery` (row 2); this row defines the component the other rows wire.

## Design decisions
- `RobotsCache.__init__(self, user_agent)` stores the user agent and an empty `{host -> RobotFileParser}` map; the cache lives for one crawl session only.
- `fetch_host` (new) caches by netloc and is idempotent: the membership check is placed before any request, so a repeated call for an already-fetched host makes no further network call (at-most-once per host).
- `is_allowed` (new) returns True (allow) for an unknown host so a missing cache entry never blocks a crawl.

## Alternatives considered
- A module-level singleton cache — rejected: instance caching keeps the cache scoped to one crawl session and avoids cross-crawl shared state.
- Fetching `robots.txt` lazily inside `should_enqueue_link` — rejected: the plan fetches eagerly in the orchestrator to keep the synchronous filter synchronous (UNK-01).

## Implementation
### Target file
`scripts/rag/ingestion/robots.py` (new)

### Procedure
Create the module and implement `RobotsCache` (new) with `__init__`, `fetch_host` (new), and `is_allowed` (new).

### Method
Add the module docstring, the two stdlib imports, and the class:
```python
from urllib.parse import urlparse (new)
from urllib.robotparser import RobotFileParser (new)

import httpx (new)


class RobotsCache:
    """Fetches and parses robots.txt per host; answers can_fetch queries."""

    def __init__(self, user_agent: str) -> None:
        self._user_agent = user_agent
        self._parsers: dict[str, RobotFileParser] = {}

    async def fetch_host(self, origin: str, client: httpx.AsyncClient) -> None:
        parsed = urlparse(origin)
        host = parsed.netloc
        if host in self._parsers:
            return
        robots_url = f"{parsed.scheme}://{host}/robots.txt"
        try:
            resp = await client.get(robots_url)
            parser = RobotFileParser()
            if resp.status_code == 200:
                parser.parse(resp.text.splitlines())
            else:
                parser.parse([])
            self._parsers[host] = parser
        except (httpx.RequestError, ValueError):
            fallback = RobotFileParser()
            fallback.parse([])
            self._parsers.setdefault(host, fallback)
            logger.warning("Failed to fetch %s; allowing all", robots_url)

    def is_allowed(self, url: str) -> bool:
        host = urlparse(url).netloc
        parser = self._parsers.get(host)
        if parser is None:
            return True
        return parser.can_fetch(self._user_agent, url)
```

### Details
- `fetch_host` (new) takes the origin (`scheme://netloc`) of the start URL; the caller (`orchestrator.py` row 3) supplies it. The cache key is the netloc, so `is_allowed` (new) (which keys by `urlparse(url).netloc`) hits the same entry.
- `RobotFileParser()` with no arguments defaults the user-agent to `*`; `can_fetch(user_agent, url)` is called explicitly with the crawler UA, so the default is irrelevant.
- On 404/non-2xx store an empty `RobotFileParser()` (allow-all) and on transport error fall back to allow-all and log once per host (`UNK-03`).
- The except clause is narrowed to `httpx.RequestError, ValueError` (not a bare `Exception`) so ruff `BLE001` passes; the fallback constructs a fresh `RobotFileParser()` and calls `.parse([])` explicitly so it is a true allow-all on Python 3.14, where a bare `RobotFileParser()` defaults to deny-all (`last_checked == 0`).
- Idempotency (`if host in self._parsers: return`) sits before the request so a second fetch is a true no-op (REQ-003).

## Compatibility considerations
N/A: new module with no existing callers.

## Security considerations
N/A: reads a well-known public path (`/robots.txt`); no credential handling. The shared `httpx` timeout bounds the request.

## Rollback considerations
N/A: revert the commit that introduces this procedure.

## Validation plan
- Static: `uv run ruff format` / `uv run ruff check` on `scripts/rag/ingestion/robots.py`; `uv run mypy --no-namespace-packages scripts/` with no new errors.
- Unit: `RobotFileParser.can_fetch` returns correct allow/deny for a sample Disallow rule; `is_allowed` (new) returns True for an unknown host; `fetch_host` (new) is idempotent (spy on `client.get` to assert exactly one request per host). Run `uv run pytest tests/rag/ingestion/test_robots.py -v`.

## Completion criteria
- `RobotsCache.fetch_host` issues exactly one `robots.txt` request per host and caches the parsed result; repeated calls make no further requests (REQ-003).
- `RobotsCache.is_allowed` returns False for a URL matching a Disallow rule and True for allowed/unknown-host URLs (REQ-003).
- A missing or failed `robots.txt` falls back to allow-all without raising (REQ-002, UNK-03).

## Out of Scope
Per-host concurrency or crawl-rate parsing beyond `robots.txt`; cross-run (persistent) caching of `robots.txt`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create `scripts/rag/ingestion/robots.py` with `RobotsCache.__init__`, `fetch_host` (new), `is_allowed` (new) | Completed | 20261106-183622 | 20261106-183622 | New module (row 1) |
| 2 | Add `tests/rag/ingestion/test_robots.py` per Validation plan | Completed | 20261106-183622 | 20261106-183622 | can_fetch allow/deny, once-per-host, unknown-host allow |
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
- **Related target files**: `scripts/rag/ingestion/robots.py`