## Goal

`REQ-002`: in `scripts/rag/ingestion/http_fetcher.py` narrow `origin` before `redirect_allowed` and refuse a hop whose target URL has no host as non-public before `host_is_public`, fixing the two `arg-type` errors exposed by making `rag.ingestion` a regular package. The redirect decision outcome is unchanged for every input.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Adding `scripts/rag/ingestion/__init__.py` (doc 01) makes mypy resolve `rag.ingestion` types and surface two real `arg-type` errors here: line 168 `redirect_allowed(origin, url)` and line 170 `host_is_public(url_host)`, each `str | None` where `str` is expected (`url_host = urlparse(url).hostname` may be `None`).
- `host_is_public(None)` currently fails closed (catches `gaierror` → `False`), so refusing a host-less hop earlier returns the same value.
- `origin` is truthy whenever `origin_host` is not `None` (`urlparse(origin).hostname if origin else None`), so adding `origin and` to the same-host condition changes no branch taken.

## Design decisions
- `if origin and ...` narrows `origin` to `str` for `redirect_allowed` (same-host branch unchanged by construction).
- `if url_host is None: return False, "non-public destination"` placed before the `if/elif` narrows `url_host` to `str` for `host_is_public` and preserves the fail-closed outcome.

## Alternatives considered
- Changing `host_is_public` / `redirect_allowed` to accept `str | None`: rejected — edits a second file (`crawler_utils.py`) for the same result.

## Implementation
### Target file
`scripts/rag/ingestion/http_fetcher.py`

### Procedure
Edit `_hop_policy` to guard the host-less case and narrow both arguments.

### Method
In `_hop_policy` (current lines 165–171), change
```python
        origin_host = urlparse(origin).hostname if origin else None
        url_host = urlparse(url).hostname
        if origin_host is not None and url_host == origin_host:
            if not redirect_allowed(origin, url):
                return False, "same-host downgrade refused"
        elif not await host_is_public(url_host):
            return False, "non-public destination"
```
to
```python
        origin_host = urlparse(origin).hostname if origin else None
        url_host = urlparse(url).hostname
        if url_host is None:
            return False, "non-public destination"
        if origin and origin_host is not None and url_host == origin_host:
            if not redirect_allowed(origin, url):
                return False, "same-host downgrade refused"
        elif not await host_is_public(url_host):
            return False, "non-public destination"
```

### Details
- Insert the `if url_host is None:` guard immediately after the `url_host = urlparse(url).hostname` line and before the existing `if`.
- Add `origin and ` to the start of the same-host condition; leave the rest of the condition and the `elif` untouched.
- Update the docstring if desired, but do not change behavior; the public contract `(allowed, reason)` is unchanged.

## Companion test files
- `tests/rag/ingestion/test_crawler_redirects.py`
  - Procedure: add `from rag.ingestion.http_fetcher import HttpFetcher` after the `crawler_utils` import (keeps alphabetical order: `crawler` < `crawler_utils` < `http_fetcher`); inside `TestHostIsPublicPolicy` add
    ```python
    @pytest.mark.asyncio
    async def test_hop_without_host_refused_without_dns(self, monkeypatch):
        """A hop whose target URL has no host is refused as non-public without DNS."""
        async def failing_getaddrinfo(self, *args, **kwargs):
            raise AssertionError("getaddrinfo must not be called for a host-less hop")

        monkeypatch.setattr(
            asyncio.base_events.BaseEventLoop, "getaddrinfo", failing_getaddrinfo
        )
        fetcher = HttpFetcher({})
        allowed, reason = await fetcher._hop_policy(START, "http:///x")
        assert (allowed, reason) == (False, "non-public destination")
    ```
    after `test_unknown_host_fails_closed` (still within the class body). `http:///x` has `urlparse(...).hostname == None`; the `getaddrinfo` stub raises if reached, proving the guard fires first.
  - Validation: `uv run pytest tests/rag/ingestion -k policy` (and the full suite) passes; the new test asserts the refusal and that DNS is not consulted.

## Compatibility considerations
N/A: behavior-preserving; every `(allowed, reason)` outcome is identical to before, including the host-less fail-closed case.

## Security considerations
The hop policy is a trust-boundary decision. The host-less guard keeps it fail-closed (refuses instead of resolving `None`); the same-host branch is unchanged. Existing downgrade / public / robots tests still cover the other branches.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`: reports no error in `http_fetcher.py` (the two `arg-type` errors cleared) and no new error elsewhere (AC-2).
- `uv run pytest tests/rag/ingestion`: passes, including the new `test_hop_without_host_refused_without_dns` (new).
- `tools/check_docstrings.py`, `ruff format`, `ruff check`, `lint-imports`, `bandit -r scripts/ -c pyproject.toml`: no new finding.

## Completion criteria
- `_hop_policy` guards `url_host is None` before `host_is_public` and narrows `origin` via `origin and ...` before `redirect_allowed`.
- The new redirect test passes and confirms no DNS lookup for a host-less hop.
- mypy reports zero errors after this document and docs 01–05 run.

## Out of Scope
The suppression removals (docs 02–05), the entry-point/import/docstring/comment fixes (docs 03–04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261113-201242 | 20261113-204236 | _hop_policy host-less guard + origin narrowing per Method |
| 2 | Add or update tests per Validation plan | Completed | 20261113-201242 | 20261113-204236 | companion test test_hop_without_host_refused_without_dns added to test_crawler_redirects.py |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261113-201242 | 20261113-204236 | mypy 0 errors (561 files); pytest 353 passed incl. new test; policy suite green |

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
- **Requirement ID**: `REQ-002`
- **Source issue**: issues/20261110-171004_rmcompat006_rag-ingestion-cleanup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-121532_rmcompat006_rag-ingestion-cleanup.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-201242
- **Related target files**: `scripts/rag/ingestion/http_fetcher.py`, `tests/rag/ingestion/test_crawler_redirects.py`
