## Goal

Add the two unit tests that pin mcpinv003's behavior in `tests/shared/test_http_transport.py`:
the request-error cause appears in the raised retry-exhaustion message, and a request error
followed by a successful response returns the successful result (REQ-002, REQ-003; AC-2, AC-4).

## Scope

- New test `test_request_error_exhaustion_message_contains_cause` (new): three consecutive
  `httpx.ConnectError` attempts raise `TransportError` whose message contains `Retry exhausted`,
  `ConnectError`, and the injected error text.
- New test `test_request_error_then_success_returns_result` (new): `httpx.ConnectError` on the
  first attempt followed by a valid 200 response returns the parsed `ToolCallResult` after 2
  attempts.
- No modification to the two existing tests in this file (characterization pins, AC-3).

## Assumptions

- File-skeleton facts verified in current source: the module already imports `httpx`, `pytest`,
  `AsyncMock`/`MagicMock`, `HttpTransport`, `TransportError`, and the `_http_cfg()` fixture exists
  (L23-32); `transport._http.post = AsyncMock()` injection is the established pattern (L48-49).
- The successful-200 fake needs the shape `_parse_http_response()` consumes; the established helper
  pattern in this test family is a `MagicMock` response with `status_code=200` whose JSON payload
  `call()` parses into `ToolCallResult` — copy the response-fake shape used by status-code tests in
  `tests/shared/test_tool_executor.py` (the 429/502/503/504 success-after-error tests), whose
  parsed-result assertions already prove the fake contract works through `HttpTransport`.
- Backoff sleeps (1s, 2s) already run in the existing 3-attempt tests; the new cause test tolerates
  them like the existing tests do. If suite time matters, `monkeypatch` `asyncio.sleep` — optional,
  not required for correctness.
- Overlap with mcpinv001's test document `20261028-004925_02` on the same file: disjoint sections
  (mcpinv001 adds gate tests for `_PRESEND_SAFE_ERRORS` (new)/`_AMBIGUOUS_RETRY_STATUSES` (new);
  this document adds cause/success tests). Rebase whichever lands second.

## Design decisions

- Assertions are substring-based (`"Retry exhausted" in msg`, `"ConnectError" in msg`, the injected
  detail text in `msg`) rather than full-message equality, so the frozen prefix/suffix shape and
  the new `last_error=` part are all validated without over-pinning spacing.
- `httpx.ConnectError` is the injected error class: a non-timeout `RequestError` (the retried
  class), already used by the existing attempt-count test, so the new tests reuse the file's
  proven injection idiom.

## Alternatives considered

- Extending `test_request_error_retried_three_times_for_write_and_read_tool` with message
  assertions: rejected — that test is a characterization pin that must stay unmodified (AC-3, plan
  Tests "Regression ... pass without edits"); new behavior belongs in new named tests.
- Asserting `__cause__` chaining on the raised `TransportError`: rejected as a test requirement —
  chaining is an optional implementation detail (see `20261028-010601_01` Assumptions); the
  caller-visible contract is message text.

## Implementation

### Target file

`tests/shared/test_http_transport.py`

### Procedure

1. Append after the existing tests (do not edit L1-83):
   ```python
   @pytest.mark.asyncio
   async def test_request_error_exhaustion_message_contains_cause() -> None:
       transport = HttpTransport(
           http=MagicMock(spec=httpx.AsyncClient),
           base_url="http://127.0.0.1:8000",
           server_key="srv",
           cfg=_http_cfg(),
       )
       mock_post = AsyncMock()
       transport._http.post = mock_post
       mock_post.side_effect = httpx.ConnectError("connect refused")
       with pytest.raises(TransportError) as excinfo:
           await transport.call("write_file", {})
       msg = str(excinfo.value)
       assert "Retry exhausted" in msg
       assert "tool=write_file" in msg
       assert "ConnectError" in msg
       assert "connect refused" in msg
       assert "after 3 attempts" in msg
       assert mock_post.call_count == 3
   ```
2. Append the success-after-error test:
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
       ok = MagicMock()
       ok.status_code = 200
       ok.raise_for_status.return_value = None
       ok.json.return_value = {"result": "done", "is_error": False}
       ok.headers = {}
       mock_post.side_effect = [httpx.ConnectError("flaky"), ok]
       result = await transport.call("read_text_file", {})
       assert result.is_error is False
       assert mock_post.call_count == 2
   ```
   Adjust the `ok.json` payload keys to the exact shape `_parse_http_response()` accepts (mirror
   the success fake used by the 429/502/503/504 success-after-error tests in
   `tests/shared/test_tool_executor.py`); the keys above are placeholders resolved against that
   proven shape at implementation time.

### Method

Append-only edits; reuse the file's existing fixture (`_http_cfg`) and injection idiom
(`transport._http.post = AsyncMock()` with `side_effect` list for mixed sequences).

### Details

- The first test's `mock_post.side_effect = httpx.ConnectError("connect refused")` (a single
  exception, not a list) raises on every attempt, matching the existing test's idiom (L52).
- The second test asserts attempt count 2 (error attempt + success attempt) — proving the explicit
  `continue` from `20261028-010601_01` preserves retry semantics (AC-4).
- The second test also proves `last_request_error` (new) capture has no effect on the success path: the
  loop returns the parsed result and the exhaustion message is never built.

## Compatibility considerations

- Existing tests L35-83 stay byte-for-byte unchanged; their attempt-count assertions (3, 1) must
  stay green (AC-3).
- `tests/shared/test_tool_executor.py` is unmodified by this plan; its `"Retry exhausted"`
  substring assertions pin the frozen message shape from the other side (REQ-003).
- File overlap with mcpinv001 `20261028-004925_02` (same file, disjoint appended tests): both
  append blocks after L83; land mcpinv003's tests first per plan sequencing, rebase mcpinv001's
  block on top.

## Security considerations

- Tests inject fake transports only; no network access, no real server, no secrets in test text.

## Rollback considerations

- Remove the two appended test functions (`git checkout -- tests/shared/test_http_transport.py`)
  together with the transport revert in `20261028-010601_01`'s Rollback section — the cause test
  fails against the pre-change transport.

## Validation plan

- `uv run pytest tests/shared/test_http_transport.py tests/shared/test_tool_executor.py` — new
  tests pass; all pre-existing tests pass unmodified.
- `uv run ruff check tests/`, `uv run mypy --no-namespace-packages tests/` per `rules/toolchain.md`
  — clean.
- Diff-cover: both new branches (`last_error` (new) present/absent paths) covered by the two tests plus
  the pre-existing status-exhaustion tests.

## Completion criteria

- Both new tests exist and pass; `ConnectError` and the injected detail string appear in the raised
  message (AC-2); success-after-error returns a non-error `ToolCallResult` with 2 attempts (AC-4).
- The two pre-existing tests pass with zero edits (AC-3).

## Out of Scope

- Any change to the existing two tests or to `tests/shared/test_tool_executor.py`.
- Gate tests for the mcpinv001 classification gate — covered by `20261028-004925_02`.
- Sleep monkeypatching — optional optimization, not required.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | In Progress | 2026-10-28 | — | Append after L83 |
| 2 | Add or update tests per Validation plan | In Progress | 2026-10-28 | — | This document is the test procedure |
| 3 | Run the validation sequence (`rules/toolchain.md`) | In Progress | 2026-10-28 | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | In Progress | 2026-10-28 | — | N/A for this row |

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
- **Requirement ID**: REQ-002, REQ-003
- **Source issue**: issues/20261027-001424_mcpinv003_discarded-transporterror-httptransport-call.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-103707_mcpinv003_discarded-transporterror-httptransport-call.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-010601
- **Related target files**: tests/shared/test_http_transport.py
