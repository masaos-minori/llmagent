# Implementation Procedure: tests/shared/test_tool_executor_routing.py

## Prior-doc status

`implementations/done/20260620-144019_test_tool_executor_routing.py.md` and
`implementations/done/20260709-103725_test_tool_executor_routing.py.md`
both target the same basename but are unrelated, already-applied past work.
Confirmed against current source: `grep -n
"test_http_status_error_raises_transport_error\|class TestHttpTransportErrors"
tests/shared/test_tool_executor_routing.py` finds both names already
present in the file (class at line 296, test at line 298), and neither
prior doc's filename match references either name — a coincidental filename
match. This document is written fresh.

## Goal

Confirm — and document precisely, since the grounded outcome differs from
the plan's initial framing — that `test_http_status_error_raises_transport_error`
requires **no source edit in this file**: its assertion already encodes the
desired post-fix behavior and will pass once the source fix in
`scripts/shared/http_transport.py` lands (see
`implementations/20260814-002542_http_transport.py.md`).

## Scope

In scope:
- Re-run `test_http_status_error_raises_transport_error` after the source
  fix lands, to confirm it flips from FAIL to PASS with no test-file edit.

Out of scope:
- Any edit to this test file's assertions or fixtures — grounding (below)
  shows none is needed.
- Any other test in `TestHttpTransportErrors` or the file.

## Assumptions

- Grounded by reading `tests/shared/test_tool_executor_routing.py:296-320`
  directly (current source):

  ```python
  class TestHttpTransportErrors:
      @pytest.mark.asyncio
      async def test_http_status_error_raises_transport_error(self) -> None:
          mock_http = AsyncMock(spec=httpx.AsyncClient)
          req = httpx.Request("POST", "http://127.0.0.1:8000/v1/call_tool")
          resp_obj = httpx.Response(500, request=req)
          mock_http.post = AsyncMock(
              side_effect=httpx.HTTPStatusError(
                  "server error", request=req, response=resp_obj
              )
          )
          transport = HttpTransport(mock_http, "http://127.0.0.1:8000", "svc")
          with pytest.raises(TransportError) as exc_info:
              await transport.call("my_tool", {})
          assert "HTTPStatusError" in str(exc_info.value)
  ```

  This assertion (`"HTTPStatusError" in str(exc_info.value)`) already
  matches the plan's target post-fix state — it is not being changed by
  this plan.
- Why it currently fails (pre-fix) and will pass (post-fix), traced through
  `scripts/shared/http_transport.py`'s current `HttpTransport.call` (see
  `implementations/20260814-002542_http_transport.py.md` for the full
  grounding): `mock_http.post` always raises `httpx.HTTPStatusError` with
  status 500. Status 500 is not in `_RETRYABLE_STATUS`
  (`{429, 502, 503, 504}`), so it is never intercepted by the line-114
  pre-check and always reaches `resp.raise_for_status()` /
  the `except httpx.HTTPStatusError` handler on every one of the 3
  attempts.
  - **Pre-fix**: the handler never sets `break_flag=True`, so the loop
    exhausts all 3 attempts and falls into the `for...else` branch, which
    raises the generic `"[Retry exhausted] tool=... url=... after 3
    attempts"` message — this string does **not** contain the substring
    `"HTTPStatusError"`, so the assertion fails today.
  - **Post-fix**: the handler sets `break_flag=True` for this
    non-retryable status, causing `_transport_error(...)` to `raise` the
    `TransportError` immediately on the first attempt, with message prefix
    `"[HTTPStatusError]"` — which contains the substring `"HTTPStatusError"`,
    so the assertion passes, and it passes via the immediate-raise path
    (never reaching the `for...else` branch at all).
- No other assertion in this test, and no other test in
  `TestHttpTransportErrors`, depends on retry count or message format in a
  way affected by the source fix (only this one test asserts on the
  HTTPStatusError-specific message content in this file).

## Design decisions

N/A — this procedure is verification-only; no design choice is being made
in this file.

## Alternatives considered

N/A.

## Implementation

### Target file

`tests/shared/test_tool_executor_routing.py`

### Procedure

No source edit to this file. Re-run the targeted test after
`scripts/shared/http_transport.py`'s fix lands to confirm the FAIL→PASS
flip predicted above.

### Method

N/A — verification only.

### Details

N/A — no code change in this file. If, contrary to the grounding above, the
test is observed to still fail after the source fix lands, re-open this
document: the most likely cause would be a mismatch between this
procedure's traced control-flow and the actual edited
`scripts/shared/http_transport.py`, in which case re-read the post-fix
`HttpTransport.call` before touching this test file.

## Compatibility considerations

N/A — no change made.

## Security considerations

N/A — no change made.

## Rollback considerations

N/A — no change made; nothing to roll back in this file.

## Validation plan

`uv run pytest tests/shared/test_tool_executor_routing.py::TestHttpTransportErrors -v` —
expect `test_http_status_error_raises_transport_error` to flip from FAIL to
PASS once `scripts/shared/http_transport.py`'s fix lands, with
`test_request_error_raises_transport_error` and
`test_invalid_response_raises_transport_error` (siblings in the same class)
remaining PASS throughout (unaffected by the fix).

## Out of scope

- Any edit to `tests/shared/test_tool_executor_routing.py` — none required.
- The 400/404 non-retryable coverage addition — that requirement is
  satisfied in `tests/shared/test_tool_executor.py`, not this file (see
  `implementations/20260814-002620_test_tool_executor.py.md`).

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260813-185820_plan.md
- Source implementation procedure: N/A
- Generated at: 20260814-002650
- Related target files: test_tool_executor_routing.py
