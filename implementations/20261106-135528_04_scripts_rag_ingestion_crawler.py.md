## Goal

Read the respect_robots config flag (`cfg.get("respect_robots", False)`) and, when enabled, construct a `RobotsCache` and inject it into `LinkDiscovery`; leave wiring unchanged when disabled (REQ-001, REQ-005).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Config is read via `cfg.get(...)` with defaults (lines 64-77), so adding a key cannot break existing configs that omit it (REQ-001).
- respect_robots defaults to `False`, so without the flag in `crawler.toml` the injection is `None` and behavior is unchanged (REQ-002).
- `RobotsCache(user_agent)` takes the crawler user agent; `WebCrawler._USER_AGENT` (line 46) is the shared token.
- `RobotsCache` is defined in `scripts/rag/ingestion/robots.py` (row 1); `LinkDiscovery.__init__` accepts the `robots_cache` parameter (row 2).

## Design decisions
- Read the flag next to the other boolean switches (`skip_nofollow`/`skip_external`) and build the cache inline at the `LinkDiscovery` construction site, so the enable/disable decision sits beside the wiring it controls.

## Alternatives considered
- Reading the flag lazily inside `crawl_site` — rejected: the plan injects the cache through `LinkDiscovery`, and constructing it here keeps the `RobotsCache` lifecycle tied to `WebCrawler.__init__`.

## Implementation
### Target file
`scripts/rag/ingestion/crawler.py`

### Procedure
Read the respect_robots flag and pass a constructed `RobotsCache` into `LinkDiscovery` only when it is enabled.

### Method
Add the import alongside the other `rag.ingestion` imports (near line 31):
```python
from rag.ingestion.robots import RobotsCache (new)
```
Read the flag after the `skip_external` read (line 71):
```python
self._skip_external: bool = bool(cfg.get("skip_external", True))
self._respect_robots: bool = bool(cfg.get("respect_robots", False))
```
Build the cache and pass it at the `LinkDiscovery` construction (lines 82-86):
```python
robots_cache = RobotsCache(self._USER_AGENT) if self._respect_robots else None
self.link_discovery = LinkDiscovery(
    skip_nofollow=self._skip_nofollow,
    skip_external=self._skip_external,
    max_depth=self._max_depth,
    robots_cache=robots_cache,
)
```

### Details
- `bool(cfg.get("respect_robots", False))` coerces the TOML value and defaults to `False`.
- When disabled, `robots_cache=None` flows into `LinkDiscovery`, whose default preserves today's behavior (REQ-002).
- `self._USER_AGENT` matches the UA used by `HttpFetcher`/`CrawlOrchestrator`, so `RobotsCache` answers queries with the same token.

## Compatibility considerations
Backward compatible: the new config key is optional and defaults to `False`; existing `crawler.toml` files crawl exactly as before (REQ-001, REQ-002).

## Security considerations
N/A: no new input handling or credential access.

## Rollback considerations
N/A: revert the commit that introduces this procedure.

## Validation plan
- Static: `uv run ruff format` / `uv run ruff check` on `scripts/rag/ingestion/crawler.py`; `uv run mypy --no-namespace-packages scripts/` with no new errors.
- Behavioral: with respect_robots unset/`false`, assert `LinkDiscovery._robots_cache is None`; set it `true` and assert a `RobotsCache` instance is injected. Run `tests/rag/ingestion/`.

## Completion criteria
- With respect_robots unset or `false`, `LinkDiscovery` receives `robots_cache=None` and behavior is unchanged (REQ-001, REQ-002).
- With `respect_robots = true`, a `RobotsCache` bound to `_USER_AGENT` is injected into `LinkDiscovery` (REQ-001).

## Out of Scope
Adding the config key to `config/crawler.toml` (documented in row 5); changing the config-loading mechanism.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read respect_robots and inject `RobotsCache` into `LinkDiscovery` when enabled | Pending | — | — | Row 4; `cfg.get("respect_robots", False)` |
| 2 | Add or update tests per Validation plan | Pending | — | — | None-when-off, instance-when-on |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | See row 5 for the doc change |

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
- **Requirement ID**: `REQ-001`, `REQ-005`
- **Source issue**: `issues/20261106-073206_crawl005_crawler-robots-txt-policy.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261106-094856_crawl005_crawler-robots-txt-policy.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-135528
- **Related target files**: `scripts/rag/ingestion/crawler.py`
