# Implementation: memory/embedding_client.py — query_prefix policy + EmbeddingErrorKind

## Goal

1. Add `query_prefix: str = "query: "` to `EmbeddingClientConfig`.
2. Replace hardcoded `f"query: {text}"` with `f"{config.query_prefix}{text}"`.
3. Use `EmbeddingErrorKind` enum values instead of string literals.

## Scope

- `scripts/agent/memory/embedding_client.py` — primary

## Assumptions

1. `EmbeddingErrorKind` is imported from `agent.memory.types`.
2. Existing callers that check `result.error_kind == "disabled"` still work because `EmbeddingErrorKind` is a `StrEnum`.
3. `_fetch_embedding()` receives `config` as a parameter to access `query_prefix`.
   Alternatively, pass `query_prefix: str` directly.

## Implementation

### EmbeddingClientConfig

```python
@dataclass
class EmbeddingClientConfig:
    embed_url: str = ""
    timeout: float = 5.0
    max_retries: int = 2
    circuit_open_after: int = 3
    circuit_reset_sec: float = 60.0
    query_prefix: str = "query: "   # new field
```

### _fetch_embedding: use query_prefix + EmbeddingErrorKind

```python
async def _fetch_embedding(text: str, http, embed_url: str, query_prefix: str) -> EmbeddingResult:
    try:
        resp = await http.post(embed_url, json={"content": f"{query_prefix}{text}"})
        resp.raise_for_status()
        embedding = resp.json().get("embedding")
        if isinstance(embedding, list) and embedding:
            return EmbeddingResult(success=True, embedding=[float(v) for v in embedding])
        return EmbeddingResult(success=False, error_kind=EmbeddingErrorKind.INVALID_RESPONSE)
    except httpx.HTTPStatusError as e:
        logger.warning("HTTP error: status=%d body=%.200s", e.response.status_code, e.response.text)
        return EmbeddingResult(success=False, error_kind=EmbeddingErrorKind.HTTP_ERROR)
    except Exception as e:
        logger.warning("Unexpected embedding error: %s", e)
        return EmbeddingResult(success=False, error_kind=EmbeddingErrorKind.UNKNOWN_ERROR)
```

Pass `query_prefix=self._config.query_prefix` from `EmbeddingClient.fetch()`.

### EmbeddingClient.fetch: use EmbeddingErrorKind

Replace all `error_kind="..."` string literals with `EmbeddingErrorKind.*` enum values.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/memory/embedding_client.py` | 0 errors |
| Type | `uv run mypy scripts/agent/memory/embedding_client.py` | no new errors |
| Tests | `uv run pytest tests/test_memory_layer.py -x -q` | all pass |
| No hardcode | `grep '"query: "' scripts/agent/memory/embedding_client.py` | 0 hits |
