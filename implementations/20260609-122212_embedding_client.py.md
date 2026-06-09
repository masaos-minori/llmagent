# Implementation: embedding_client.py — Change fetch() return type to EmbeddingResult

## Goal

Change `EmbeddingClient.fetch()` return type from `list[float] | None` to `EmbeddingResult`
so callers can distinguish failure reasons (disabled, circuit open, timeout, HTTP error,
invalid response) instead of treating all failures as `None`.

## Scope

- `scripts/agent/memory/types.py`: add `EmbeddingResult` dataclass.
- `scripts/agent/memory/embedding_client.py`: change `_fetch_embedding()` and `fetch()` to return `EmbeddingResult`.
- `scripts/agent/memory/ingestion.py`: update `on_session_stop()` and `_persist_entry()` to use `EmbeddingResult`.
- `scripts/agent/memory/injection.py`: update `on_user_prompt()` to use `EmbeddingResult`.

## Assumptions

1. `EmbeddingResult` is added to `types.py` (not a new file) to keep the type alongside other memory types.
2. The `error_kind` field uses a small fixed string set: `"disabled"`, `"circuit_open"`, `"timeout"`, `"http_error"`, `"invalid_response"`.
3. `ingestion.py` and `injection.py` are the only callers of `EmbeddingClient.fetch()` (grep confirmed).
4. When `success=False`, `embedding` is `None`; when `success=True`, `embedding` is a non-empty `list[float]`.

## Implementation

### Target files

- `scripts/agent/memory/types.py`
- `scripts/agent/memory/embedding_client.py`
- `scripts/agent/memory/ingestion.py`
- `scripts/agent/memory/injection.py`

### Procedure

**types.py — add EmbeddingResult:**
```python
@dataclass
class EmbeddingResult:
    """Result of an embedding generation attempt."""
    success: bool
    embedding: list[float] | None = None
    error_kind: str | None = None  # "disabled"|"circuit_open"|"timeout"|"http_error"|"invalid_response"
```

**embedding_client.py — _fetch_embedding():**

Change return type from `list[float] | None` to `EmbeddingResult`:
```python
async def _fetch_embedding(text: str, http: httpx.AsyncClient, embed_url: str) -> EmbeddingResult:
    try:
        resp = await http.post(embed_url, json={"content": f"query: {text}"})
        resp.raise_for_status()
        embedding = resp.json().get("embedding")
        if isinstance(embedding, list) and embedding:
            return EmbeddingResult(success=True, embedding=[float(v) for v in embedding])
        logger.warning("embed response missing 'embedding' field")
        return EmbeddingResult(success=False, error_kind="invalid_response")
    except httpx.HTTPStatusError as e:
        logger.warning(f"EmbeddingClient._fetch_embedding HTTP error: {e}")
        return EmbeddingResult(success=False, error_kind="http_error")
    except Exception as e:
        logger.warning(f"EmbeddingClient._fetch_embedding failed: {e}")
        return EmbeddingResult(success=False, error_kind="http_error")
```

**embedding_client.py — fetch():**

```python
async def fetch(self, text: str) -> EmbeddingResult:
    if not self._enabled or self._http is None or not self._config.embed_url:
        return EmbeddingResult(success=False, error_kind="disabled")
    if self._is_circuit_open():
        logger.debug("EmbeddingClient circuit open — skipping embed")
        return EmbeddingResult(success=False, error_kind="circuit_open")

    for attempt in range(self._config.max_retries + 1):
        try:
            result = await asyncio.wait_for(
                _fetch_embedding(text, self._http, self._config.embed_url),
                timeout=self._config.timeout,
            )
            if result.success:
                self._fail_count = 0
                return result
        except TimeoutError:
            logger.warning(
                "EmbeddingClient timeout (attempt %d/%d)",
                attempt + 1,
                self._config.max_retries + 1,
            )
            result = EmbeddingResult(success=False, error_kind="timeout")
        self._record_failure()
        if self._is_circuit_open():
            return EmbeddingResult(success=False, error_kind="circuit_open")

    return EmbeddingResult(success=False, error_kind="http_error")
```

**ingestion.py — on_session_stop():**

Replace `embedding = await self._embed_client.fetch(...)` usages:
```python
embed_result = await self._embed_client.fetch(entry.content)
embedding = embed_result.embedding if embed_result.success else None
if (
    self._dedup_policy.action == DedupAction.SKIP_NEW
    and embed_result.success
    and self._has_near_duplicate(entry.memory_id, embed_result.embedding)  # type: ignore[arg-type]
):
    ...
```

**injection.py — on_user_prompt():**

```python
embed_result = await self._embed_client.fetch(query)
embedding = embed_result.embedding if embed_result.success else None
hits_s = self._retriever.search(..., embedding=embedding, ...)
```

### Method

Staged edits: types.py → embedding_client.py → ingestion.py → injection.py.
Run mypy after each file to catch type errors early.

### Details

The existing `None`-based callers in `ingestion.py` check:
- `if embedding is not None and self._has_near_duplicate(...)` → becomes `if embed_result.success and ...`
- `self._store.upsert(entry, embedding=embedding)` → unchanged (still `list[float] | None`)
- `if embedding is not None: self._link_duplicates(...)` → becomes `if embed_result.success:`

## Validation plan

| Check | Command | Expected |
|---|---|---|
| No `list[float] \| None` return from fetch | `grep -n "list\[float\]" scripts/agent/memory/embedding_client.py` | only in `EmbeddingResult.embedding` field |
| EmbeddingResult imported | `grep "EmbeddingResult" scripts/agent/memory/embedding_client.py` | present |
| Lint | `uv run ruff check scripts/agent/memory/embedding_client.py scripts/agent/memory/ingestion.py scripts/agent/memory/injection.py` | 0 errors |
| Type check | `uv run mypy scripts/agent/memory/` | 0 new errors |
| Tests | `uv run pytest tests/test_memory_layer.py -v` | all pass |
