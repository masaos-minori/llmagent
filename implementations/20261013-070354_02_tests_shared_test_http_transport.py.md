## Goal

Pin the observed write-retry behavior of `HttpTransport.call` with a unit test: a write
tool is retried on a non-timeout `httpx.RequestError` (same as a read tool), and a
`httpx.TimeoutException` variant is retried only once.

## Scope

- **In-Scope**: Create `tests/shared/test_http_transport.py` with a unit test asserting a
  write tool is retried 3× on a non-timeout `httpx.RequestError` (e.g.
  `httpx.ConnectError`) and a read tool likewise, and that a `httpx.TimeoutException`
  variant is retried only once. Mock `httpx.AsyncClient.post`.
- **Out-of-Scope**: Any other `HttpTransport` behavior, retryable-status handling, backoff
  timing, or non-shared-module transport tests.

## Assumptions

- `_RETRY_MAX == 3` (confirmed at `scripts/shared/http_transport.py:113`), so a non-timeout
  `RequestError` yields exactly 3 `post` calls before `TransportError` is raised.
- `httpx.TimeoutException` is a `RequestError` subclass caught earlier by the dedicated
  `except httpx.TimeoutException` handler, which breaks without retry (1 attempt).
- Existing conventions in `tests/shared/test_tool_transport_invoker.py` (`MagicMock
  (spec=httpx.AsyncClient)`, `AsyncMock`, `call_count`) apply.

## Design decisions

- **Mock at the network boundary**: replace `transport._http` with
  `MagicMock(spec=httpx.AsyncClient)` and drive `post.side_effect` with the exception type
  under test; count attempts via `mock_post.call_count`. This isolates the retry loop from
  any real I/O.
- **Exception-type branching is the assertion axis**: `httpx.ConnectError` (a
  `RequestError`, not a `TimeoutException`) exercises the always-retry path (3 calls);
  `httpx.TimeoutException` exercises the early-break path (1 call). This directly pins the
  REQ-003 property without depending on status codes.

## Alternatives considered
N/A: the exception-side-effect approach is the minimal way to distinguish the two handlers;
status-code mocking would exercise the separate retryable-status branch instead.

## Implementation
### Target file
`tests/shared/test_http_transport.py` (new)

### Procedure
1. Create `tests/shared/test_http_transport.py`. Import `HttpTransport`, `TransportError`
   (verify exact import paths in `scripts/shared/http_transport.py`), `httpx`, and
   `unittest.mock.AsyncMock`/`MagicMock`.
2. Determine a concrete write-tool name (a member of `_WRITE_TOOLS`) and a non-write tool
   name; confirm membership against `_WRITE_TOOLS` before using them as test inputs.
3. Write an async test that instantiates `HttpTransport` with the minimal constructor args
   required (follow the construction pattern in `test_tool_transport_invoker.py`), wraps
   `transport._http` in `MagicMock(spec=httpx.AsyncClient)`, sets
   `mock_post.side_effect = httpx.ConnectError("boom")`, awaits
   `transport.call(write_tool, {...})`, asserts it raises `TransportError`, and asserts
   `mock_post.call_count == 3`.
4. Add the same assertion for a read tool (non-write name) to show identical retry
   behavior.
5. Add a timeout variant: `mock_post.side_effect = httpx.TimeoutException("timed out")`,
   assert `TransportError` and `mock_post.call_count == 1`.
6. Keep the test focused on the write-vs-read and timeout distinction only — no coverage of
   retryable statuses, backoff, or other paths.

### Method
One async test function (or a small set of `@pytest.mark.asyncio` tests) that constructs
`HttpTransport`, swaps in a mocked async client, and asserts `call_count` per exception
type.

### Details
Suggested shape (adapt imports/constructor to the current source):
```python
@pytest.mark.asyncio
async def test_write_and_read_retried_on_request_error_not_timeout():
    transport = HttpTransport(base_url="http://localhost", ...)  # minimal args
    mock_post = MagicMock(spec=httpx.AsyncClient.post)
    transport._http = MagicMock(spec=httpx.AsyncClient)
    transport._http.post = mock_post

    # Non-timeout RequestError -> always retried (3 attempts) for BOTH tools.
    mock_post.side_effect = httpx.ConnectError("boom")
    with pytest.raises(TransportError):
        await transport.call("some_write_tool", {})
    assert mock_post.call_count == 3

    mock_post.side_effect = httpx.ConnectError("boom")
    with pytest.raises(TransportError):
        await transport.call("some_read_tool", {})
    assert mock_post.call_count == 3

    # TimeoutException -> breaks without retry (1 attempt).
    mock_post.side_effect = httpx.TimeoutException("timed out")
    with pytest.raises(TransportError):
        await transport.call("some_read_tool", {})
    assert mock_post.call_count == 1
```
Note: `HttpTransport.call` is a coroutine; the test must be async and await it. If the
module's test runner requires per-test client wiring, mirror the fixture/setup used in
`test_tool_transport_invoker.py`.

## Compatibility considerations
N/A: new file only; no existing symbol or contract touched.

## Security considerations
N/A: no secret handling; URLs and exceptions are test doubles.

## Rollback considerations
Revert the commit (deletes the new test file).

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/shared/test_http_transport.py` | Unit: assert retry counts via mocked `httpx.AsyncClient.post` | `uv run pytest tests/shared/test_http_transport.py -v` | 3 attempts (non-timeout, write+read), 1 attempt (timeout) |
| `tests/shared/` | Integration: full shared-module suite | `uv run pytest tests/shared/ -v` | no new failures |
| `scripts/`, `tests/` | Static lint/type | `uv run ruff check scripts/ tests/` · `uv run mypy --no-namespace-packages scripts/` | clean |
| changed lines | Diff-scoped coverage | `uv run coverage run -m pytest tests/` → `uv run coverage xml` → `uv run diff-cover coverage.xml --compare-branch=master` | ≥ 90% |

## Completion criteria
`tests/shared/test_http_transport.py` exists, asserts 3 attempts for a non-timeout
`httpx.RequestError` on both a write and a read tool and 1 attempt for a
`httpx.TimeoutException`, and the shared-module suite plus `ruff`/`mypy` pass.

## Out of scope
Retryable-status handling, exponential backoff timing, non-MCP HTTP calls, and any
`HttpTransport` behavior beyond the write-vs-read/timeout retry distinction.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 2 | Add write-retry unit test in `tests/shared/test_http_transport.py` | Pending | — | — | REQ-003; companion to `20261013-070354_01_scripts_shared_http_transport.py.md` |
| 3 | Run ruff/mypy/shared-suite/diff-cover and confirm clean | Pending | — | — | REQ-004 |

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
- **Requirement ID**: `REQ-003` (assert the observed write-retry behavior)
- **Source issue**: `issues/20261012-184834_mcp001_req-006-write-tool-retry-guard-is-structurally-inactive-in-httptransport.call.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261012-214127_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261013-070354
- **Related target files**: `tests/shared/test_http_transport.py`
