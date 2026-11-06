## Goal

Add an optional `robots_cache` (new) to `LinkDiscovery` and, when set, skip enqueuing URLs that `robots_cache.is_allowed` returns False for, keeping all existing nofollow/cross-origin logic intact (REQ-002, REQ-003, REQ-004).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `should_enqueue_link` (lines 63-78) is the single enqueue decision point; `enqueue_links` (lines 44-61) is the choke point that calls it.
- `RobotsCache` is defined by `scripts/rag/ingestion/robots.py` (row 1, earlier seq) and injected by `crawler.py` (row 4); this row only consumes it.
- When respect_robots is off, `crawler.py` injects `robots_cache=None`, so `self._robots_cache is None` and behavior is byte-for-byte unchanged (REQ-002).
- The plan targets same-origin crawls (`skip_external = true`); the robots check runs after the external filter so cross-origin URLs are already dropped when enabled.

## Design decisions
- Add `robots_cache: RobotsCache | None = None` to `__init__` and store it as the private attribute `_robots_cache` (new) via `self._robots_cache`; the default preserves the disabled contract.
- In `should_enqueue_link`, compute the normalized `next_url` once (moved out of the `skip_external` branch) and add the robots check last, after the nofollow and external filters.

## Alternatives considered
- Computing `next_url` inside the robots branch only — rejected: the external filter already needs the normalized URL, so computing it once avoids a duplicate `normalize_url(urljoin(...))` call.

## Implementation
### Target file
`scripts/rag/ingestion/link_discovery.py`

### Procedure
Thread an optional `RobotsCache` through `LinkDiscovery` and consult it in `should_enqueue_link`.

### Method
Edit `__init__` (lines 34-42): add the parameter and store it:
```python
def __init__(
    self,
    skip_nofollow: bool = False,
    skip_external: bool = True,
    max_depth: int = 0,
    robots_cache: RobotsCache | None = None,
) -> None:
    self._skip_nofollow = skip_nofollow
    self._skip_external = skip_external
    self._max_depth = max_depth
    self._robots_cache = robots_cache
```
Edit `should_enqueue_link` (lines 63-78): resolve `next_url` once and append the robots check before the final `return True`:
```python
def should_enqueue_link(self, a_tag, current_url, start_url):
    href = a_tag.get("href")
    if not isinstance(href, str):
        return False
    next_url = normalize_url(urljoin(current_url, str(href)))
    if self._skip_nofollow:
        rel = a_tag.get("rel")
        if isinstance(rel, str):
            rel = rel.split()
        if rel and "nofollow" in rel:
            return False
    if self._skip_external:
        if not same_origin(next_url, start_url):
            return False
    if self._robots_cache is not None and not self._robots_cache.is_allowed(next_url):
        return False
    return True
```
Add the type import under the existing `TYPE_CHECKING` block:
```python
if TYPE_CHECKING:
    from rag.ingestion.robots import RobotsCache (new)
```

### Details
- `from __future__ import annotations` already makes annotations lazy, so the `TYPE_CHECKING` import does not create a runtime circular dependency (consistent with the existing `crawler_utils` local-import pattern).
- The robots check reads `self._robots_cache.is_allowed(next_url)` synchronously; `RobotsCache.is_allowed` is a pure, non-async method, so no `await` is needed inside the sync filter (UNK-01).
- When `robots_cache` (new) is `None` the new branch short-circuits and every existing path is unchanged (REQ-004).

## Compatibility considerations
Backward compatible: the new parameter defaults to `None`, so existing callers (and the crawl004 session-connection change in `orchestrator.py`) are unaffected. Behavior is identical when the flag is off (REQ-002, REQ-004).

## Security considerations
N/A: no new input handling or credential access. The check is an in-memory dict lookup on an already-parsed parser.

## Rollback considerations
N/A: revert the commit that introduces this procedure.

## Validation plan
- Static: `uv run ruff format` / `uv run ruff check` on `scripts/rag/ingestion/link_discovery.py`; `uv run mypy --no-namespace-packages scripts/` with no new errors.
- Behavioral: with a mocked `RobotsCache`, assert a Disallow URL is not enqueued and an allowed URL is; with `robots_cache=None` assert zero `robots.txt` requests and unchanged queue output. Run `tests/rag/ingestion/`.

## Completion criteria
- With a robots cache present, a URL failing `is_allowed` is skipped at enqueue and allowed URLs are queued (REQ-003).
- With `robots_cache=None` the filter behaves exactly as before, issuing no `robots.txt` request (REQ-002, REQ-004).

## Out of Scope
Changing nofollow or cross-origin filtering semantics; fetching `robots.txt` (handled in `orchestrator.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add optional `robots_cache` (new) to `LinkDiscovery.__init__` and the `is_allowed` check in `should_enqueue_link` | Pending | — | — | Row 2; coexists with crawl004's orchestrator change |
| 2 | Add or update tests per Validation plan | Pending | — | — | Disallow-skip, None-preserves-behavior |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: `REQ-002`, `REQ-003`, `REQ-004`
- **Source issue**: `issues/20261106-073206_crawl005_crawler-robots-txt-policy.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261106-094856_crawl005_crawler-robots-txt-policy.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-135528
- **Related target files**: `scripts/rag/ingestion/link_discovery.py`
