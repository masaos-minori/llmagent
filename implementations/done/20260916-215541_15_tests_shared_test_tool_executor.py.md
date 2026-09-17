## Goal

Update the two retry tests whose assertions encode the current buggy behavior; add new secret/sensitive-fragment-redaction tests.

## Scope

- Update `test_retry_delay_values_via_sleep_mock` to assert exactly two sleep calls in increasing order (REQ-008).
- Update `test_retries_exhausted_returns_error` to assert `TransportError` specifically (REQ-009).
- Add synthetic-secret/sensitive-payload-fragment redaction tests (REQ-010).

## Assumptions

- The existing `_make_executor()` helper creates a `ToolExecutor` with default configs.
- The existing `TestHttpTransportRetry` class provides a good home for these new tests.

## Design decisions

- Rename `test_retry_delay_values_via_sleep_mock` to `test_retry_delay_values_increase_and_stop_before_final_attempt` to reflect the new assertion.
- Add each new test as a separate method in the appropriate existing test class.

## Alternatives considered

- Creating a new test class for each requirement — rejected: adds unnecessary class proliferation.
- Merging all three requirements into one test — rejected: clarity benefits from separation.

## Implementation

### Target file

`tests/shared/test_tool_executor.py`

### Procedure

1. Rename and rewrite `test_retry_delay_values_via_sleep_mock` for REQ-008.
2. Update `test_retries_exhausted_returns_error` for REQ-009.
3. Add REQ-010 redaction tests.

### Method

- **Step 1** (REQ-008): In `TestHttpTransportRetry`, rename and rewrite `test_retry_delay_values_via_sleep_mock`:

```python
# Before (lines 225-254):
def test_retry_delay_values_via_sleep_mock(self) -> None:
    """Assert the exact sleep delays used during retries."""
    ...
    mock_sleep.assert_has_calls([call(4), call(2), call(1)])

# After:
@pytest.mark.asyncio
async def test_retry_delay_values_increase_and_stop_before_final_attempt(self) -> None:
    """REQ-008: exactly two sleeps in increasing order (1 then 2 seconds)."""
    # ... implement using mock asyncio.sleep
    pass
```

- **Step 2** (REQ-009): Update `test_retries_exhausted_returns_error`:

```python
# Before (line 74):
with pytest.raises(Exception):

# After:
with pytest.raises(TransportError):
```

- **Step 3** (REQ-010): Add redaction tests:

```python
class TestRedaction:
    """REQ-010: synthetic secrets and sensitive payload fragments are not leaked."""

    @pytest.mark.asyncio
    async def test_synthetic_secret_not_leaked_in_transport_error(self) -> None:
        # ... implement using mock HTTP response with synthetic secret
        pass

    @pytest.mark.asyncio
    async def test_sensitive_payload_fragment_not_leaked_in_tool_result_output(self) -> None:
        # ... implement using ToolTransportInvoker path
        pass
```

### Details

**Step 1 — REQ-008:** Replace lines 225-254 in `TestHttpTransportRetry`:

```python
@pytest.mark.asyncio
async def test_retry_delay_values_increase_and_stop_before_final_attempt(self) -> None:
    """REQ-008: exactly two sleeps in increasing order (1 then 2 seconds)."""
    # Arrange: create an HttpTransport that will trigger retries
    transport = HttpTransport(
        base_url="http://127.0.0.1:8000",
        timeout=5.0,
        auth_token=None,
    )
    
    # Mock the HTTP client to return retryable status codes
    mock_resp = MagicMock()
    mock_resp.status_code = 503
    mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Service Unavailable", request=MagicMock(), response=mock_resp
    )
    
    call_count = 0
    
    async def mock_post(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            return mock_resp  # Retryable
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"tools": []}
        return mock_resp
    
    transport._http.post = mock_post
    
    # Act: capture sleep calls
    sleep_calls = []
    original_sleep = asyncio.sleep
    
    async def mock_sleep(sec):
        sleep_calls.append(sec)
    
    with patch.object(asyncio, 'sleep', side_effect=mock_sleep):
        result = await transport.call("test_tool", {})
    
    # Assert: exactly two sleeps in increasing order
    assert len(sleep_calls) == 2
    assert sleep_calls[0] == 1  # attempt 0: 2^0 = 1 second
    assert sleep_calls[1] == 2  # attempt 1: 2^1 = 2 seconds
```

**Step 2 — REQ-009:** Update line 74 in `test_retries_exhausted_returns_error`:

```python
# Before:
with pytest.raises(Exception):

# After:
from shared.transport_dto import TransportError

# ... later:
with pytest.raises(TransportError):
```

**Step 3 — REQ-010:** Add new test class after `TestHttpTransportRetry`:

```python
class TestRedaction:
    """REQ-010: synthetic secrets and sensitive payload fragments are not leaked."""

    @pytest.mark.asyncio
    async def test_synthetic_secret_not_leaked_in_transport_error(self) -> None:
        """REQ-010: synthetic secrets embedded in error responses are not emitted."""
        # Arrange: register a synthetic secret
        from shared.logger import register_secret
        register_secret("super-secret-value-should-not-leak")
        
        # Create an HttpTransport with the synthetic secret as auth token
        transport = HttpTransport(
            base_url="http://127.0.0.1:8000",
            timeout=5.0,
            auth_token="super-secret-value-should-not-leak",
        )
        
        # Mock the HTTP client to return an error with the secret in the body
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = '{"error": "super-secret-value-should-not-leak"}'
        mock_resp.headers.get.return_value = ""
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Internal Server Error", request=MagicMock(), response=mock_resp
        )
        
        transport._http.post = AsyncMock(return_value=mock_resp)
        
        # Act: trigger the error
        with pytest.raises(TransportError) as exc_info:
            await transport.call("test_tool", {})
        
        # Assert: the synthetic secret is NOT in the error message
        assert "super-secret-value-should-not-leak" not in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_sensitive_payload_fragment_not_leaked_in_tool_result_output(self) -> None:
        """REQ-010: sensitive payload fragments are not emitted in ToolCallResult.output."""
        # ... similar implementation using ToolTransportInvoker path
        pass
```

## Compatibility considerations

- Renamed test replaces the old assertion; all other tests in `TestHttpTransportRetry` are unchanged.
- New tests use the existing `_make_executor()` helper pattern.

## Security considerations

- No security impact. This is a behavioral change test for REQ-008/009/010.

## Rollback considerations

- Reverting the test changes restores the pre-fix test suite but does not affect source code.

## Validation plan

- Run unit tests: `uv run pytest tests/shared/test_tool_executor.py -v`
- Verify the renamed test passes with the new assertion.
- Verify REQ-009 test asserts `TransportError`.
- Verify REQ-010 tests pass (synthetic secret not leaked).
- Static analysis: `uv run ruff check tests/shared/test_tool_executor.py`, `uv run mypy tests/shared/test_tool_executor.py`.

## Completion criteria

- `test_retry_delay_values_increase_and_stop_before_final_attempt` asserts `[1, 2]` sleeps.
- `test_retries_exhausted_returns_error` asserts `TransportError`.
- REQ-010 tests confirm synthetic secrets are not leaked.
- All existing tests pass without regression.
- No new lint/type errors introduced.

## Out of scope

- Modifying `scripts/shared/http_transport.py` source code — covered in previous row.
- Modifying `scripts/shared/tool_transport_invoker.py` source code — covered in previous row.
- Any MCP server business logic unrelated to the invocation gate chain.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update retry delay test for REQ-008 | Completed | 20260917-192336 | 20260917-192336 |  |
| 2 | Update retry exhaustion test for REQ-009 | Completed | 20260917-192336 | 20260917-192336 |  |
| 3 | Add REQ-010 redaction tests | Completed | 20260917-192336 | 20260917-192336 |  |
| 4 | Run the validation sequence (rules/toolchain.md) | Completed | 20260917-192337 | 20260917-192337 |  |
| 5 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260917-192346 | 20260917-192346 |  |

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
- **Requirement ID**: REQ-008, REQ-009, REQ-010
- **Source issue**: issues/20260914-103224_mcpagent06_http-retry-backoff-safe-diagnostics.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-124248_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-215541
- **Related target files**: tests/shared/test_tool_executor.py