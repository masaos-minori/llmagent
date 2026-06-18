# Implementation: scripts/rag/pipeline_service.py

## Goal

Add explicit HTTP timeout, simple retry policy with exponential backoff, and optional `X-RAG-Token` auth header to `call_rag_service()`.

## Scope

- `scripts/rag/pipeline_service.py` — modify `call_rag_service()` only; no interface changes to callers beyond a new `auth_token: str = ""` keyword argument

## Assumptions

1. Timeout: explicit `timeout=10.0` (connect + read) passed to `http.post()`.
2. Retry: 2 retries max for transient errors (5xx, `httpx.TransportError`); no retry on 4xx client errors.
3. Backoff: `min(2 ** attempt, 5)` seconds — 1s after first failure, 2s after second.
4. Auth: if `auth_token != ""`, add `X-RAG-Token: {auth_token}` header to the POST request.
5. All retries exhausted → return `None` (triggers in-process fallback); same behavior as current single-failure path.
6. Empty results (`context=""` or `selected_hits=[]`) are NOT retried — they are valid responses.
7. `asyncio.sleep()` is used for async backoff (do not use `time.sleep` in async context).
8. `httpx.AsyncClient` is already constructed by `RagPipeline.__init__`; do not change the client itself.

## Implementation

### Target file

`scripts/rag/pipeline_service.py`

### Procedure

1. Add `auth_token: str = ""` keyword-only parameter to `call_rag_service()`.
2. Build `headers: dict[str, str] = {}` and conditionally add `"X-RAG-Token": auth_token`.
3. Wrap the `http.post()` call in a retry loop (max 3 total attempts = 1 initial + 2 retries).
4. Catch `httpx.HTTPStatusError` separately: retry only if `resp.status_code >= 500`.
5. Catch `httpx.TransportError` (connection errors): always retry.
6. Catch `orjson.JSONDecodeError`, `ValueError`: do NOT retry (non-transient); return `None` immediately.
7. Add `asyncio` import (for `asyncio.sleep`).
8. Log retry attempts at WARNING level with attempt number and error.

### Method

Iterative retry loop (`for attempt in range(3)`). On transient error: `await asyncio.sleep(min(2**attempt, 5))` then continue. On final failure: return `None` as before.

### Details

**New signature:**
```python
async def call_rag_service(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
) -> str | None:
```

**Headers:**
```python
headers: dict[str, str] = {}
if auth_token:
    headers["X-RAG-Token"] = auth_token
```

**Retry loop structure:**
```python
_MAX_ATTEMPTS = 3
for attempt in range(_MAX_ATTEMPTS):
    try:
        resp = await http.post(
            f"{rag_url}/v1/search",
            json={"query": query, "history_context": history_context},
            headers=headers,
            timeout=10.0,
        )
        resp.raise_for_status()
        body = orjson.loads(resp.content)
        # ... existing parsing logic ...
        return context_raw
    except httpx.HTTPStatusError as e:
        if e.response.status_code < 500:
            # 4xx: non-transient, do not retry
            logger.warning("RAG service client error (%s) %s", rag_url, e)
            return None
        _log_retry(rag_url, attempt, e)
    except httpx.TransportError as e:
        _log_retry(rag_url, attempt, e)
    except (orjson.JSONDecodeError, ValueError) as e:
        logger.warning("RAG service parse error (%s), falling back: %s", rag_url, e)
        return None
    if attempt < _MAX_ATTEMPTS - 1:
        await asyncio.sleep(min(2**attempt, 5))
logger.warning("RAG service (%s) failed after %d attempts, falling back to in-process", rag_url, _MAX_ATTEMPTS)
return None
```

**Helper:**
```python
def _log_retry(rag_url: str, attempt: int, error: Exception) -> None:
    logger.warning(
        "RAG service call failed (%s) attempt %d/%d: %s",
        rag_url, attempt + 1, _MAX_ATTEMPTS, error,
    )
```

**Imports to add:** `import asyncio` at the top of the file.

**Note:** `_log_retry` is a module-level function (not a method) to avoid closures. The `_MAX_ATTEMPTS = 3` is a module-level constant.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lint | `uv run ruff check scripts/rag/pipeline_service.py` | 0 errors |
| Type check | `uv run mypy scripts/rag/pipeline_service.py` | no new errors |
| Tests | `uv run pytest tests/test_agent_rag.py -v` | all pass |
| Full suite | `uv run pytest tests/ -x -q` | no regressions |
