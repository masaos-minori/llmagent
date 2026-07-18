# Implementation: Correct HttpTransport retry backoff documentation and add tests

## Goal

Correct the misleading description of HttpTransport retry delay in `docs/04_mcp_03_routing_lifecycle_and_execution.md` and add tests for retryable statuses (502, 503, 504) and non-retryable timeout behavior in `tests/test_tool_executor.py`.

## Scope

- **In-Scope**:
  - Fix doc description of retry delay sequence in `docs/04_mcp_03_routing_lifecycle_and_execution.md` line 205
  - Add tests for retryable statuses 502, 503, 504 in `tests/test_tool_executor.py`
  - Add test verifying timeout is non-retryable in `tests/test_tool_executor.py`
  - Verify retry delay formula `2 ** (RETRY_MAX - attempt - 1)` produces correct sequence
- **Out-of-Scope**:
  - Changing retry semantics or delay formula in `HttpTransport`
  - Circuit-breaker changes
  - HealthRegistry logic changes

## Assumptions

- The decreasing delay formula `2 ** (RETRY_MAX - attempt - 1)` is intentional (not a bug); RETRY_MAX=3 yields delays of 4s, 2s, 1s for attempts 0, 1, 2 respectively.
- The delay of 1s on attempt 2 is technically reachable (sleep is called before `continue`, which then hits the `else` clause when no success occurs).
- The term "exponential backoff" does not appear in the current doc (line 205 says "decreasing delay"); background in the requirement refers to an older doc state or colloquial usage.
- No implementation change is required; only documentation and test additions.

## Unknowns Resolution

| ID | Description | Resolution |
|---|---|---|
| UNK-01 | Whether the 1s delay on attempt 2 was intentional or a formula error | Treat as intentional (decreasing delay); document clearly without calling it exponential backoff |
| UNK-02 | Whether `HTTPStatusError` for non-retryable 4xx/5xx should also be tested | Add one test for HTTPStatusError on non-retryable status (e.g. 500) during implementation |

## Implementation

### Target file: `docs/04_mcp_03_routing_lifecycle_and_execution.md`

#### Procedure

Update line 205 retry description to clarify it is NOT exponential backoff.

#### Method

Direct file edit — replace the retry description on line 205.

#### Details

**Replace line 205:**
```markdown
- **Retry:** retries on HTTP 429/502/503/504, up to 3 attempts with decreasing delay (4s → 2s → 1s). Only the final outcome (success or TransportError after all retries exhausted) is recorded in HealthRegistry.
```

**With:**
```markdown
- **Retry:** retries on HTTP 429/502/503/504, up to 3 attempts with decreasing delay: attempt 0 waits 4s, attempt 1 waits 2s, attempt 2 waits 1s before the final exhaustion error. Formula: 2^(RETRY_MAX - attempt - 1). This is NOT exponential backoff (delays decrease with each attempt). Only the final outcome (success or TransportError after all retries exhausted) is recorded in HealthRegistry.
```

### Target file: `tests/test_tool_executor.py`

#### Procedure

Add test methods to `TestHttpTransportRetry` class for 502, 503, 504 retryable statuses and timeout non-retryability.

#### Method

Direct file edit — append new test methods after existing `test_retries_exhausted_returns_error` method (around line 142).

#### Details

**Add after line 142 (after `test_retries_exhausted_returns_error`):**
```python
    @pytest.mark.asyncio
    async def test_retries_on_502_and_succeeds(self) -> None:
        call_count = 0

        class _FakeClient:
            async def post(self, url: str, **kw: Any) -> httpx.Response:
                nonlocal call_count
                call_count += 1
                req = httpx.Request("POST", url)
                if call_count < 3:
                    return httpx.Response(
                        502, request=req, json={"result": "", "is_error": False}
                    )
                return httpx.Response(
                    200, request=req, json={"result": "ok", "is_error": False}
                )

        transport = HttpTransport(
            _FakeClient(),  # type: ignore[arg-type]
            base_url="http://localhost:8080",
            server_key="test",
        )
        with patch("asyncio.sleep", return_value=None):
            result = await transport.call("write_file", {"path": "a"})
        assert result.output == "ok"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retries_on_503_and_succeeds(self) -> None:
        call_count = 0

        class _FakeClient:
            async def post(self, url: str, **kw: Any) -> httpx.Response:
                nonlocal call_count
                call_count += 1
                req = httpx.Request("POST", url)
                if call_count < 3:
                    return httpx.Response(
                        503, request=req, json={"result": "", "is_error": False}
                    )
                return httpx.Response(
                    200, request=req, json={"result": "ok", "is_error": False}
                )

        transport = HttpTransport(
            _FakeClient(),  # type: ignore[arg-type]
            base_url="http://localhost:8080",
            server_key="test",
        )
        with patch("asyncio.sleep", return_value=None):
            result = await transport.call("write_file", {"path": "a"})
        assert result.output == "ok"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retries_on_504_and_succeeds(self) -> None:
        call_count = 0

        class _FakeClient:
            async def post(self, url: str, **kw: Any) -> httpx.Response:
                nonlocal call_count
                call_count += 1
                req = httpx.Request("POST", url)
                if call_count < 3:
                    return httpx.Response(
                        504, request=req, json={"result": "", "is_error": False}
                    )
                return httpx.Response(
                    200, request=req, json={"result": "ok", "is_error": False}
                )

        transport = HttpTransport(
            _FakeClient(),  # type: ignore[arg-type]
            base_url="http://localhost:8080",
            server_key="test",
        )
        with patch("asyncio.sleep", return_value=None):
            result = await transport.call("write_file", {"path": "a"})
        assert result.output == "ok"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_timeout_is_non_retryable(self) -> None:
        call_count = 0

        class _FakeClient:
            async def post(self, url: str, **kw: Any) -> httpx.Response:
                nonlocal call_count
                call_count += 1
                raise httpx.TimeoutException("timed out")

        transport = HttpTransport(
            _FakeClient(),  # type: ignore[arg-type]
            base_url="http://localhost:8080",
            server_key="test",
        )
        with pytest.raises(TransportError) as exc_info:
            await transport.call("write_file", {"path": "a"})
        assert call_count == 1
        assert "timeout" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_non_retryable_http_status_not_retried(self) -> None:
        call_count = 0

        class _FakeClient:
            async def post(self, url: str, **kw: Any) -> httpx.Response:
                nonlocal call_count
                call_count += 1
                req = httpx.Request("POST", url)
                return httpx.Response(
                    500, request=req, json={"result": "", "is_error": True}
                )

        transport = HttpTransport(
            _FakeClient(),  # type: ignore[arg-type]
            base_url="http://localhost:8080",
            server_key="test",
        )
        with pytest.raises(TransportError):
            await transport.call("write_file", {"path": "a"})
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_delay_values_via_sleep_mock(self) -> None:
        sleep_calls = []

        class _FakeClient:
            async def post(self, url: str, **kw: Any) -> httpx.Response:
                req = httpx.Request("POST", url)
                return httpx.Response(
                    429, request=req, json={"result": "", "is_error": False}
                )

        transport = HttpTransport(
            _FakeClient(),  # type: ignore[arg-type]
            base_url="http://localhost:8080",
            server_key="test",
        )

        async def capture_sleep(*args, **kwargs):
            sleep_calls.extend(args)
            return None

        with patch("asyncio.sleep", side_effect=capture_sleep):
            try:
                await transport.call("write_file", {"path": "a"})
            except TransportError:
                pass  # Expected — all retries exhausted

        assert len(sleep_calls) == 2
        assert sleep_calls[0] == 4
        assert sleep_calls[1] == 2
```

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/test_tool_executor.py` | New unit tests for 502/503/504 retry and timeout non-retry | `uv run pytest tests/test_tool_executor.py -v` | All tests pass, no regressions |
| `docs/04_mcp_03_routing_lifecycle_and_execution.md` | Manual review of retry description | Visual diff review | Description matches implementation; no mention of exponential backoff |
| `scripts/shared/tool_executor.py` | No code change; existing tests still pass | `uv run pytest tests/test_tool_executor.py -v` | No regressions |

## Risks & Mitigations

- **Risk**: New tests mock `asyncio.sleep` globally which may interfere with other async behavior in the same test → **Mitigation**: Use `patch("asyncio.sleep", return_value=None)` scoped to `with` block as already done in existing tests; no global patching.
- **Risk**: Doc change description becomes too verbose → **Mitigation**: Keep the updated description to ≤2 lines; use a code comment reference `# 4, 2, 1` already present in implementation.
- **Risk**: Misidentifying whether 1s delay is reachable leads to wrong doc → **Mitigation**: Trace the for-loop: attempt 2 with retryable status executes `sleep(1)` then `continue`, then `else` clause triggers `Retry exhausted`; 1s is reachable and should be documented.
