## Goal

Add a test asserting that when `HttpTransport.call` performs multiple HTTP attempts
(retries), the health, lifecycle, and semaphore gates execute exactly once per logical
call — not once per attempt.

## Scope

- **In-Scope**: Add a test to `tests/shared/test_tool_transport_invoker.py` that drives a
  real `HttpTransport.call` through a retry sequence and asserts the gates run once while
  `post` is called 3x.
- **Out-of-Scope**: Any change to `scripts/shared/`; changes to the retryable-status set,
  backoff, `_RETRY_MAX`, or existing tests.

## Assumptions

- Option (a) is the intended resolution; the test pins the resolved invariant.
- A real `HttpTransport` can be constructed and injected into `invoker._transports["srv"]`
  (same pattern as existing tests), so the actual retry loop executes rather than a mock.

## Design decisions

- **Real transport, mocked HTTP layer**: construct a genuine `HttpTransport` and mock only
  its `httpx.AsyncClient.post` to return a retryable status, so the real retry loop runs
  end-to-end.
- **Count gate executions via wraps-mocks**: replace `_check_health`, `_maybe_semaphore`,
  and the lifecycle object with recording doubles and assert `call_count == 1` each, while
  asserting `post.call_count == 3`. This directly encodes "once per logical call, not per
  attempt."

## Alternatives considered
N/A: option (b) (per-attempt re-check) is explicitly rejected by the Plan; this test pins
the resolved option (a).

## Implementation
### Target file
`tests/shared/test_tool_transport_invoker.py`

### Procedure
1. Add a new test class `TestRetryGatesRunOnce` at the end of the file (after the last
   existing test), mirroring the existing `@pytest.mark.asyncio` style.
2. In a test method, build an invoker with `_make_invoker()` (default config `"srv"`,
   PERSISTENT, no health registry set so `_check_health` dispatches).
3. Set a recording lifecycle: `lifecycle = AsyncMock(); invoker.set_lifecycle(lifecycle)`.
4. Construct a real transport and inject it:
   ```python
   http = MagicMock(spec=httpx.AsyncClient)
   transport = HttpTransport(
       http=http, base_url="http://127.0.0.1:8000", server_key="srv", timeout_sec=60.0
   )
   resp = MagicMock()
   resp.status_code = 503  # in _RETRYABLE_STATUS -> retryable
   http.post = AsyncMock(return_value=resp)
   invoker._transports["srv"] = transport  # type: ignore[assignment]
   ```
5. Wrap the gates with recording doubles:
   ```python
   invoker._check_health = MagicMock(wraps=invoker._check_health)
   invoker._maybe_semaphore = MagicMock(wraps=invoker._maybe_semaphore)
   ```
   (Optionally pass `concurrency_limits={"srv": 10}` to `_make_invoker` so a real
   semaphore is acquired instead of `nullcontext`; the `call_count == 1` assertion holds
   either way.)
6. Patch the backoff sleep to avoid real waits between attempts:
   ```python
   monkeypatch.setattr("shared.http_transport.asyncio.sleep", AsyncMock())
   ```
7. Drive one logical call and assert:
   ```python
   result = await invoker.invoke("srv", "some_tool", {})
   assert http.post.call_count == 3          # retries exhausted on 503
   assert invoker._check_health.call_count == 1    # health gate once
   assert lifecycle.ensure_ready.call_count == 1   # lifecycle gate once
   assert invoker._maybe_semaphore.call_count == 1 # semaphore gate once
   assert result.is_error is True            # exhaustion returns a transport error
   ```
8. Do not modify any existing test or any file under `scripts/shared/`.

### Method
One new test class using a real `HttpTransport` + mocked `post` + recording gate doubles;
no new imports beyond what the file already has (`AsyncMock`, `MagicMock`, `httpx`,
`HttpTransport`, `ToolCallResult`).

### Details
The retry loop in `http_transport.py::call` (lines 163-217) calls `self._http.post` and
`continue`s on a retryable status up to `_RETRY_MAX = 3`, sleeping via
`await asyncio.sleep(2**attempt)` between attempts (attempts 0 and 1). Patching
`shared.http_transport.asyncio.sleep` removes the ~3s real wait. The loop exhausts after
3 attempts and raises `TransportError`, which `_invoke_and_record` catches and converts
to an error result (`is_error=True`). Because `invoke()` calls `_run_precall_gates` once,
and that method calls `_check_health` (sync, line 238), `lifecycle.ensure_ready` (line
255), and `_execute_with_semaphore`→`_maybe_semaphore` (line 212) exactly once, each
recording double reports `call_count == 1` despite 3 HTTP attempts.

Reference conventions already present in this file: `_make_invoker` (line 36),
`MagicMock(spec=httpx.AsyncClient)` (line 40), direct injection
`invoker._transports["srv"] = mock_transport` (line 76), `lifecycle = AsyncMock()` +
`invoker.set_lifecycle(...)` (lines 67-68), and `result.is_error is True` (line 60).

## Compatibility considerations
N/A: additive test only; no production code touched.

## Security considerations
N/A: no secret handling; the test uses a non-write tool name (`"some_tool"`) so the
idempotency-key write guard (REQ-005) is not exercised.

## Rollback considerations
Remove the added test class.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/shared/test_tool_transport_invoker.py` | New gate-once test | `uv run pytest tests/shared/test_tool_transport_invoker.py -k TestRetryGatesRunOnce` | test present and green |
| `tests/shared/` + `scripts/shared/` | Full suite + lint/type | `uv run pytest tests/shared/` · `uv run ruff check scripts/shared tests/shared` · `uv run mypy --no-namespace-packages scripts/shared tests/shared` | all pass |

## Completion criteria
`TestRetryGatesRunOnce` exists and passes, asserting `post` is called 3x while the
health/lifecycle/semaphore gates each run once, and `ruff`, `mypy`, and the shared-module
suite pass.

## Out of scope
`scripts/shared/tool_transport_invoker.py` (REQ-001), `scripts/shared/http_transport.py`
(REQ-002), and any retry/backoff or health-failure-counting change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 2 | Add gate-once-across-retries test (`tests/shared/test_tool_transport_invoker.py`) | Pending | — | — | REQ-003 |
| 3 | Run ruff/mypy/shared-suite validation | Pending | — | — | REQ-004 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | N/A: structural non-issue | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-003` (assert gates run once across a multi-attempt retry)
- **Source issue**: `issues/20261012-185100_mcp002_health-and-lifecycle-gates-run-once-per-logical-call-not-per-http-retry-in-mcp-transport.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261012-223034_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261013-074037
- **Related target files**: `tests/shared/test_tool_transport_invoker.py`
