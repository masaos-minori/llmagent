## Goal

Add two unit tests to `tests/shared/test_http_transport.py`: one asserting the
request-error cause appears in the retry-exhaustion message, and one asserting a
request error followed by a successful response returns the parsed result (REQ-002,
REQ-003).

## Scope

- Append `test_request_error_exhaustion_includes_cause_in_message` (three
  `httpx.ConnectError` responses → `TransportError` whose message carries the cause).
- Append `test_request_error_then_success_returns_result` (one `ConnectError`, then a
  200 with a valid `result` → the `ToolCallResult`).
- Do not modify existing tests; the attempt-count tests stay green unmodified (AC-3).
- The handler/message changes these tests exercise live in
  `scripts/shared/http_transport.py` (this document's sibling procedure).

## Assumptions

- The existing helper `_http_cfg()` (line 23) and imports (`HttpTransport`,
  `TransportError`, `_WRITE_TOOLS`, `MagicMock`, `AsyncMock`, `pytest`, `httpx`) remain
  available; new tests mirror the style of
  `test_request_error_retried_three_times_for_write_and_read_tool` (line 36).
- A success response is built as `httpx.Response(200, request=req, json={"result": "ok",
  "is_error": False})`, matching the pattern already used in
  `tests/shared/test_tool_executor.py`; `parse_http_json` reads `resp.content`.
- Overlap with sibling plan `plans/20261027-102512_mcpinv001_mcp-write-idempotency-backstop.md`
  on `tests/shared/test_http_transport.py` is Compatible and sequenced: this Plan
  implements first; mcpinv001 rebases onto it. See the sibling procedure's Assumptions.
- The injected text `"boom"` in the cause test is benign fixture connection text, not a
  response body; asserting it appears documents the propagated cause, not a body leak.

## Design decisions

- Both tests use the file's existing `MagicMock(spec=httpx.AsyncClient)` + `AsyncMock`
  `transport._http.post` substitution rather than a fake client class, keeping them
  consistent with the characterization pins at the top of the file.

## Alternatives considered

- **A fake async `post` client class** (as in `test_tool_executor.py::TestHttpTransportRetry`):
  works but diverges from this file's established `AsyncMock`/`side_effect` style, so it
  is not used here.

## Implementation

### Target file

`tests/shared/test_http_transport.py`

### Procedure

Append the two tests below to the end of the file (after
`test_timeout_exception_retried_once`, which ends near line 83). They reuse `_http_cfg()`
and the `MagicMock(spec=httpx.AsyncClient)` pattern already used in the file.

### Method

Test 1 — cause present in the exhaustion message (mirrors line 36's setup; inject three
`ConnectError`s, then assert the raised message):

```python
@pytest.mark.asyncio
async def test_request_error_exhaustion_includes_cause_in_message() -> None:
    transport = HttpTransport(
        http=MagicMock(spec=httpx.AsyncClient),
        base_url="http://127.0.0.1:8000",
        server_key="srv",
        cfg=_http_cfg(),
    )
    mock_post = AsyncMock()
    transport._http.post = mock_post
    mock_post.side_effect = httpx.ConnectError("boom")
    with pytest.raises(TransportError) as exc:
        await transport.call("read_text_file", {})
    assert mock_post.call_count == 3
    message = str(exc.value)
    assert "Retry exhausted" in message
    assert "ConnectError" in message
    assert "boom" in message
```

Test 2 — a request error followed by a 200 returns the parsed result (2 attempts):

```python
@pytest.mark.asyncio
async def test_request_error_then_success_returns_result() -> None:
    transport = HttpTransport(
        http=MagicMock(spec=httpx.AsyncClient),
        base_url="http://127.0.0.1:8000",
        server_key="srv",
        cfg=_http_cfg(),
    )
    mock_post = AsyncMock()
    transport._http.post = mock_post
    req = httpx.Request("POST", "http://127.0.0.1:8000/v1/call_tool")
    mock_post.side_effect = [
        httpx.ConnectError("boom"),
        httpx.Response(200, request=req, json={"result": "ok", "is_error": False}),
    ]
    result = await transport.call("read_text_file", {})
    assert mock_post.call_count == 2
    assert result.output == "ok"
```

### Details

- Test 1 relies on the handler capturing the cause as `ConnectError: boom` and appending
  it as `last_error=ConnectError: boom` in the exhaustion message (see the sibling
  `http_transport.py` procedure); the three identical `ConnectError` instances are raised
  once per attempt, so `call_count == 3`.
- Test 2's second `side_effect` entry is a real `httpx.Response`; `call()` sees status
  200 (not retryable), parses the JSON body, and returns it after one retry.
- Use a read tool (`read_text_file`) so the write gate is irrelevant to these assertions.

## Compatibility considerations

- N/A: test-only change; no production contract touched.

## Security considerations

- N/A: no data-handling change. The asserted `"boom"` is fixture text, not a response
  body.

## Rollback considerations

- Revert the commit (append-only test additions).

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/shared/test_http_transport.py` | Unit | `uv run pytest tests/shared/test_http_transport.py tests/shared/test_tool_executor.py` | Both new tests pass; all pre-existing tests pass unmodified |
| `tests/shared/test_http_transport.py` | Static | `uv run ruff check tests/shared/test_http_transport.py`, `uv run mypy --no-namespace-packages tests/shared/test_http_transport.py` | Clean |

## Completion criteria

- `test_request_error_exhaustion_includes_cause_in_message` (new) passes and the message
  contains `[Retry exhausted]`, `ConnectError`, and the injected text (AC-2).
- `test_request_error_then_success_returns_result` (new) passes with `call_count == 2` and the
  returned `ToolCallResult.output == "ok"` (AC-4).
- Existing attempt-count tests remain green unmodified (AC-3).

## Out of Scope

- Modifying any existing test.
- The handler/message implementation (sibling `http_transport.py` procedure).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the cause-in-message and error-then-success unit tests | Completed | 20261028-103012 | 20261028-103012 | Both appended after `test_timeout_exception_retried_once`; mirror line-36 setup style |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261028-103012 | 20261028-103012 | ruff clean; mypy clean within project scope (tests/shared out of mypy `files` scope); 10274 passed/12 skipped/0 failed; diff-cover 100% on handler |

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
- **Requirement ID**: `REQ-002`, `REQ-003`
- **Source issue**: issues/20261027-001424_mcpinv003_discarded-transporterror-httptransport-call.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-103707_mcpinv003_discarded-transporterror-httptransport-call.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-224722
- **Related target files**: tests/shared/test_http_transport.py
