# Implementation Procedure: tests/shared/test_tool_executor.py

## Prior-doc status

`implementations/done/20260707-143200_test_tool_executor.py.md` and
`implementations/done/20260715-152212_test_tool_executor.py.md` both target
the same basename but are unrelated, already-applied past work: the
`20260715-152212` doc is explicitly scoped to `TestCacheStampede` /
cache-bypass routing tests and states in its own "Out of scope" section
"No change to `TestHttpTransportRetry` or any other test class in this file
beyond `TestCacheStampede` and `test_cache_hit_no_health_registry_update`."
Confirmed against current source: `grep -n
"test_non_retryable_http_status_not_retried\|class TestHttpTransportRetry"
tests/shared/test_tool_executor.py` finds both names already present in the
file (class at line 159, test function at line 313), but neither prior doc
addresses them. This is a coincidental filename match — this document is
written fresh.

## Goal

Add a second non-retryable-HTTP-status regression case (e.g. HTTP 400)
alongside the existing 500 case in `TestHttpTransportRetry`, per the
requirement's acceptance criteria, once the source fix in
`scripts/shared/http_transport.py` (see
`implementations/20260814-002542_http_transport.py.md`) lands.

## Scope

In scope:
- Add one additional non-retryable-status test case (HTTP 400) in
  `TestHttpTransportRetry` (class starts at line 159), asserting
  `call_count == 1` — either as a new assertion inside
  `test_non_retryable_http_status_not_retried` (line 313) or as a new
  sibling test function.

Out of scope:
- `test_non_retryable_http_status_not_retried`'s existing 500-status
  assertion (line 313-332) — already asserts `call_count == 1`; this is the
  *desired* post-fix assertion already, per the plan's Affected-areas note,
  and needs no edit.
- Any other test class in this file (`TestCacheStampede`,
  `TestExecuteCacheBypass`, etc.) — untouched by this plan.

## Assumptions

- Grounded by reading `tests/shared/test_tool_executor.py:290-345` directly
  (current source). Current `test_non_retryable_http_status_not_retried`:

  ```python
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
  ```

- This test currently *fails* (observes `call_count == 3`) against
  unfixed `scripts/shared/http_transport.py`, per the plan; it will pass
  once the source fix lands. No edit to this specific test is required by
  this plan beyond adding the new 400 case.
- `HttpTransport`, `TransportError`, `httpx`, `pytest`, `Any` are already
  imported at the top of the file (lines 8-31) — no new imports needed for
  a same-shape 400 test case.

## Design decisions

- Mirror the existing `test_non_retryable_http_status_not_retried` test's
  exact shape (a local `_FakeClient` with a `post()` returning a fixed
  status, incrementing `call_count`) rather than introducing shared
  fixtures/parametrization, to keep the diff minimal and consistent with
  the plan's "add/confirm coverage for a second non-retryable status"
  wording (either extension form is acceptable per the plan).
- Add the 400 case as a new sibling test method
  (`test_non_retryable_400_status_not_retried`) rather than folding it into
  the existing test via a loop/parametrize, so a future regression in either
  status code fails with an unambiguous, individually-named test.

## Alternatives considered

- Parametrize `test_non_retryable_http_status_not_retried` over `[400,
  500]` via `@pytest.mark.parametrize`. Not chosen: the existing test's
  fixed-500 shape is simple and already correct; converting it to a
  parametrized form is a larger diff than adding one new sibling test, with
  no added coverage benefit for this plan's narrow goal.

## Implementation

### Target file

`tests/shared/test_tool_executor.py`

### Procedure

1. Immediately after `test_non_retryable_http_status_not_retried` (ends at
   line 332, before `test_retry_delay_values_via_sleep_mock` at line 334),
   add a new test method in `TestHttpTransportRetry`:

### Method

Same pattern as the existing 500 test: a local `_FakeClient` class whose
`post()` always returns a fixed non-retryable status, wrapped in
`pytest.raises(TransportError)`, asserting `call_count == 1` (i.e., no
retry occurred).

### Details

```python
    @pytest.mark.asyncio
    async def test_non_retryable_400_status_not_retried(self) -> None:
        call_count = 0

        class _FakeClient:
            async def post(self, url: str, **kw: Any) -> httpx.Response:
                nonlocal call_count
                call_count += 1
                req = httpx.Request("POST", url)
                return httpx.Response(
                    400, request=req, json={"result": "", "is_error": True}
                )

        transport = HttpTransport(
            _FakeClient(),  # type: ignore[arg-type]
            base_url="http://localhost:8080",
            server_key="test",
        )
        with pytest.raises(TransportError):
            await transport.call("write_file", {"path": "a"})
        assert call_count == 1
```

## Compatibility considerations

- Additive test-only change; no existing test is modified, no fixture
  signature changes, no import changes.

## Security considerations

N/A — test-only change, no new I/O or external data handling beyond the
existing in-process fake HTTP client pattern already used in this file.

## Rollback considerations

- Single new test method; revert by deleting it. No other test or fixture
  depends on it.

## Validation plan

`uv run pytest tests/shared/test_tool_executor.py::TestHttpTransportRetry -v` —
expect all tests in the class to PASS, including the new
`test_non_retryable_400_status_not_retried` and the pre-existing
`test_non_retryable_http_status_not_retried` (both require the source fix
in `scripts/shared/http_transport.py` to be applied first).

## Out of scope

- No change to `TestCacheStampede`, `TestExecuteCacheBypass`, or any other
  class in this file.
- No change to the existing 500-status test's assertions (already correct).

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260813-185820_plan.md
- Source implementation procedure: N/A
- Generated at: 20260814-002620
- Related target files: test_tool_executor.py
