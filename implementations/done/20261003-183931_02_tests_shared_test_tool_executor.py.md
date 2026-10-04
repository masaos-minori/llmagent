# Implementation Procedure — `tests/shared/test_tool_executor.py`

## Goal

Add a regression test asserting that a persistently malformed `/v1/call_tool` response makes `HttpTransport.call()` fail after **exactly one** `post` call instead of three (`REQ-005`). This pins the invoc002 fix in `scripts/shared/http_transport.py` (row 1): a `ValueError` from `_parse_http_response()` must raise `TransportError` immediately rather than loop.

## Scope

- **In-Scope**: Append one new test method to `TestToolExecutorErrorClassification` in `tests/shared/test_tool_executor.py` that drives a malformed body through a real `HttpTransport`, asserts `error_type == "transport"`, and asserts the fake client's `post` was invoked exactly once. Existing tests left unchanged.
- **Out-of-Scope**: Production code change (row 1 / `scripts/shared/http_transport.py`); any other test class or fixture modification.

## Assumptions

- The existing `test_malformed_response_is_transport_error` (L468-497) already builds a real `HttpTransport` around a `_FakeClientMalformed` and asserts `error_type == "transport"` and `stat_transport_errors == 1`. That assertion holds both before and after the fix (the single `TransportError` still propagates once downstream), so it does **not** by itself lock the one-attempt behavior — the new post-count assertion does.
- Counting `post` calls requires instrumenting the underlying `httpx` client, not mocking `HttpTransport.call` at the `ToolExecutor` level. Mocking `call` would bypass `HttpTransport.call()`'s own retry loop and could not prove the fix.
- `asyncio.sleep` between retries is irrelevant here: after the fix there is no second attempt, so no sleep occurs. No `patch("asyncio.sleep")` is needed, though adding it keeps the test hermetic if the fix regresses.

## Design decisions

- **Mirror the existing malformed test.** Reuse the exact `_FakeClientMalformed` shape (returns `httpx.Response(200, request=req, content=body)`), wrapped in a real `HttpTransport(base_url=..., server_key="file_read")`, injected via `ex._transports["file_read"] = transport`, driven by `await ex._raw_execute("read_text_file", {})`. This exercises the genuine retry loop inside `call()`.
- **Instrument the fake client with a call counter.** Give the fake client a mutable counter (e.g. a small wrapper class holding `self.calls = 0` incremented at the top of `post`, or a closure variable) and assert `counter == 1` after the call. This is the assertion that distinguishes fixed from broken.
- **Assert both outcomes.** Keep `assert result.error_type == "transport"` (behavior preserved) alongside `assert counter == 1` (the fix). Both together prevent a future regression that silently reintroduces the retry loop.
- **Keep it non-parametrized.** One representative malformed body is sufficient to lock the attempt count; the existing parametrized suite already covers body variety for the `error_type` classification.

## Alternatives considered

- **Parametrize the new test like the existing one.** Rejected — the goal is to lock the *attempt count*, which is invariant across bodies; one case suffices and keeps the assertion unambiguous.
- **Count via `mock_transport.call` invocations on a mocked transport.** Rejected — bypasses `HttpTransport.call()`'s retry loop entirely, so it cannot prove the malformed body stops after one attempt. Must count the real `post`.

## Implementation

### Target file

`tests/shared/test_tool_executor.py`

### Procedure

Append a new async method to `TestToolExecutorErrorClassification` (the class starting at L351, which currently ends near L497 before the `H-5` section at L500):

1. Define a fake client that counts `post` calls, e.g.:
   ```python
   class _FakeClientMalformedCounter:
       def __init__(self, body: bytes) -> None:
           self.body = body
           self.calls = 0

       async def post(self, url: str, **kw: Any) -> httpx.Response:
           self.calls += 1
           req = httpx.Request("POST", url)
           return httpx.Response(200, request=req, content=self.body)
   ```
2. Add the test method:
   ```python
   @pytest.mark.asyncio
   async def test_malformed_response_fails_after_single_post(self) -> None:
       registry = McpServerHealthRegistry(failure_threshold=3)
       ex = _make_executor()
       ex.set_health_registry(registry)

       client = _FakeClientMalformedCounter(b'{"is_error": false}')
       transport = HttpTransport(
           client,  # type: ignore[arg-type]  -- duck-typed fake for test
           base_url="http://127.0.0.1:8000",
           server_key="file_read",
       )
       ex._transports["file_read"] = transport

       result = await ex._raw_execute("read_text_file", {})

       assert result.error_type == "transport"
       assert client.calls == 1
   ```
   Use a malformed body that triggers the `ValueError` path in `_parse_http_response` (any of `b"[1, 2]"`, `b'{"is_error": false}'`, or `b'{"result": "x", "is_error": 1}'` from the existing parametrization works).

### Method

Reuse imports already present in the module: `AsyncMock`/`MagicMock` (L8), `httpx` (L10), `HttpTransport` (L13), `McpServerHealthRegistry` (L16-20), `Any` (L8), `_make_executor` (defined in-module). No new imports required.

### Details

- Preserve English docstrings/comments; keep line length ≤ 88 (`ruff format`).
- Do not modify any existing test, fixture, or class body.
- If the fix regresses to a 3-attempt loop, this test fails with `client.calls == 3` — an unambiguous signal.

## Compatibility considerations

Purely additive. Coexists with `test_malformed_response_is_transport_error` (L468-497) and the rest of `TestToolExecutorErrorClassification`. Does not depend on the UNK-01 message normalization; it only asserts attempt count and error classification.

## Security considerations

N/A: test-only addition; no secrets or I/O beyond a mocked HTTP client returning controlled bytes.

## Rollback considerations

Delete the appended method (and helper class) to fully revert.

## Validation plan

| Target File/Module | Strategy | Tool / Command | Expected |
|---|---|---|---|
| `tests/shared/test_tool_executor.py` | New regression passes | `uv run pytest tests/shared/test_tool_executor.py::TestToolExecutorErrorClassification::test_malformed_response_fails_after_single_post -v` | Passes; `client.calls == 1` |
| `tests/shared/test_tool_executor.py` | Full-suite regression | `uv run pytest tests/shared/test_tool_executor.py` | No regressions; existing malformed/retry/timeout suites pass |
| `tests/shared/test_tool_executor.py` | Static: lint/format/import-order | `uv run ruff check tests/shared/test_tool_executor.py` | Zero findings |

## Completion criteria

- The new method exists in `TestToolExecutorErrorClassification` and passes in isolation and in the full suite.
- It asserts both `error_type == "transport"` and that the fake client's `post` was called exactly once.
- All pre-existing tests in the module still pass unmodified.
- `ruff` reports zero findings.

## Out of scope

Production code (row 1), the `invoke()`-vs-`_raw_execute()` equivalence test (invoc001 row 4), and any change to existing tests or fixtures.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Done | — | — | Append malformed post-count regression |
| 2 | Add or update tests per Validation plan | Done | — | — | Same addition; verify full suite |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | — | — | pytest + ruff OK |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Done | — | — | N/A: no docs document retry/backoff policy |

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
- **Requirement ID**: `REQ-005`
- **Source issue**: `issues/20261003-154654_invoc002_harden-httptransport-call-retry-control-flow.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261003-165320_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261003-183931
- **Related target files**: `tests/shared/test_tool_executor.py`
