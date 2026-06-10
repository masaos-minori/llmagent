# Implementation: embedding_client.py — exception log improvement

## Goal

Improve diagnostic quality of exception logs in `_fetch_embedding`:
1. For `HTTPStatusError`: log `status_code` and first 200 chars of response body.
2. For generic `Exception`: use `error_kind="unknown_error"` to distinguish from HTTP errors.
3. Update `EmbeddingResult.error_kind` comment in `types.py` to include `"unknown_error"`.

## Scope

- **Target file**: `scripts/agent/memory/embedding_client.py`
- **Secondary**: `scripts/agent/memory/types.py` — add `"unknown_error"` to `error_kind` comment
- **Not in scope**: POST body (`{"content": f"query: {text}"}`) — currently correct, no change needed

## Assumptions

1. `httpx.HTTPStatusError` has `.response.status_code` (int) and `.response.text` (str).
2. `error_kind` is a free-form string; existing callers only check for `"disabled"` and `"circuit_open"`.
   Changing `"http_error"` to `"unknown_error"` for generic exceptions does not break callers.
3. Response body may be very large; truncate to 200 chars in log to avoid log flooding.

## Implementation

### Target file

`scripts/agent/memory/embedding_client.py`

### Procedure

1. In `_fetch_embedding`, update the `HTTPStatusError` except block:
   - Change log message to include `e.response.status_code` and `e.response.text[:200]`.
2. In `_fetch_embedding`, update the generic `Exception` except block:
   - Change `error_kind="http_error"` to `error_kind="unknown_error"`.
3. In `types.py` `EmbeddingResult.error_kind` comment, append `"unknown_error"`.

### Method

Direct textual edit.

### Details

In `embedding_client.py`:
```python
except httpx.HTTPStatusError as e:
    logger.warning(
        "EmbeddingClient._fetch_embedding HTTP error: status=%d body=%.200s",
        e.response.status_code,
        e.response.text,
    )
    return EmbeddingResult(success=False, error_kind="http_error")
except Exception as e:
    logger.warning("EmbeddingClient._fetch_embedding unexpected error: %s", e)
    return EmbeddingResult(success=False, error_kind="unknown_error")
```

In `types.py` (EmbeddingResult.error_kind comment):
```python
error_kind: str | None = (
    None  # "disabled"|"circuit_open"|"timeout"|"http_error"|"invalid_response"|"unknown_error"
)
```

## Validation plan

| Check | Command | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/memory/embedding_client.py` | 0 errors |
| Type | `uv run mypy scripts/agent/memory/embedding_client.py` | no new errors |
| Tests | `uv run pytest tests/test_memory_layer.py -x -q` | all pass |
