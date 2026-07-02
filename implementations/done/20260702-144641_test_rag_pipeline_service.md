# Implementation Procedure: tests/test_rag_pipeline_service.py

## Goal

Add behavior-lock tests for `call_rag_service()` error paths to
`tests/test_rag_pipeline_service.py` (Plan 142136 Phase 1):
- `set_fallback_reason` callback is called on 4xx, 5xx-exhausted, and JSON parse error
- `remote_status_code` is correctly returned in the tuple on 4xx path

## Scope

**In scope:**
- New test class `TestFallbackReasonCallback` with 3 methods
- New test class `TestReturnedStatusCode` with targeted assertions
- All tests use `respx.mock` for HTTP mocking and `AsyncMock` for `asyncio.sleep`

**Out of scope:**
- Changes to `pipeline_service.py` (source is correct)
- Changes to `mcp/rag_pipeline/service.py`

## Assumptions

1. `call_rag_service()` signature: `async def call_rag_service(url, query, *, set_fallback_reason=None, ...) -> tuple[result, status_code, elapsed_ms]`.
   Confirm from `pipeline_service.py:42`.
2. `set_fallback_reason` is a callable accepting a single `str` argument.
3. `respx.mock` is already used in `test_rag_pipeline_service.py` — reuse its fixture/decorator pattern.
4. `asyncio.sleep` must be patched in the 5xx test to avoid real delay (retry backoff).
5. Fallback reason prefixes: `"http_client_error:"` (4xx), `"http_max_retries:"` (5xx exhausted),
   `"http_parse_error:"` (JSON parse error) — confirm from `pipeline_service.py` before writing.

## Implementation

### Target file

`tests/test_rag_pipeline_service.py`

### Procedure

1. Read `scripts/rag/pipeline_service.py` lines around retry logic and `set_fallback_reason`
   calls to confirm exact reason string prefixes.
2. Read `tests/test_rag_pipeline_service.py` to understand existing fixture/mock patterns.
3. Add the following two classes:

```python
class TestFallbackReasonCallback:
    @pytest.mark.asyncio
    async def test_4xx_calls_set_fallback_reason(self, respx_mock):
        reasons: list[str] = []
        respx_mock.post(...).mock(return_value=httpx.Response(400))
        result, status, elapsed = await call_rag_service(
            url=..., query="q", set_fallback_reason=reasons.append
        )
        assert result is None
        assert status == 400
        assert len(reasons) == 1
        assert reasons[0].startswith("http_client_error:")

    @pytest.mark.asyncio
    async def test_5xx_exhausted_calls_set_fallback_reason(self, respx_mock, monkeypatch):
        monkeypatch.setattr("asyncio.sleep", AsyncMock())
        reasons: list[str] = []
        respx_mock.post(...).mock(return_value=httpx.Response(503))  # all retries → 503
        result, status, elapsed = await call_rag_service(
            url=..., query="q", set_fallback_reason=reasons.append
        )
        assert result is None
        assert len(reasons) == 1
        assert reasons[0].startswith("http_max_retries:")

    @pytest.mark.asyncio
    async def test_json_parse_error_calls_set_fallback_reason(self, respx_mock):
        reasons: list[str] = []
        respx_mock.post(...).mock(return_value=httpx.Response(200, content=b"not-json"))
        result, status, elapsed = await call_rag_service(
            url=..., query="q", set_fallback_reason=reasons.append
        )
        assert result is None
        assert len(reasons) == 1
        assert reasons[0].startswith("http_parse_error:")


class TestReturnedStatusCode:
    @pytest.mark.asyncio
    async def test_4xx_returns_status_code(self, respx_mock):
        respx_mock.post(...).mock(return_value=httpx.Response(400))
        _, status, _ = await call_rag_service(url=..., query="q")
        assert status == 400
```

**Notes:**
- Fill `url=...` with the mock URL used in existing tests.
- Fill `respx_mock.post(...)` with the route pattern matching existing tests.
- Verify reason string prefixes by reading `pipeline_service.py` before writing.

## Validation plan

| Step | Command | Expected result |
|------|---------|----------------|
| Run targeted tests | `uv run pytest tests/test_rag_pipeline_service.py -v` | all PASSED |
| Regression | `uv run pytest tests/test_rag_pipeline_mcp_service.py -v` | all PASSED |
| Lint | `ruff check tests/test_rag_pipeline_service.py` | 0 errors |
| Type check | `mypy tests/test_rag_pipeline_service.py` | no new errors |
